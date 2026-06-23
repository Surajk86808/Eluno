"""
POST /api/chat — LLM Chat Agent endpoint.

Stores conversation history in PostgreSQL (chat_messages table) and calls
the Gemini-powered agent to answer operational questions using real DB data.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatMessage
from app.schemas import ChatRequest, ChatResponse
from app.services.chat_service import run_agent

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    # Create or reuse conversation
    conversation_id = payload.conversation_id or str(uuid.uuid4())

    # Load existing history for this conversation (last 20 messages)
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in db.scalars(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(20)
        ).all()
    ]

    # Persist user message
    db.add(ChatMessage(conversation_id=conversation_id, role="user", content=payload.message))
    db.commit()

    # Run agent
    try:
        reply, structured_data = run_agent(payload.message, history, db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Persist assistant reply
    db.add(ChatMessage(conversation_id=conversation_id, role="assistant", content=reply))
    db.commit()

    return ChatResponse(
        reply=reply,
        data=structured_data,
        conversation_id=conversation_id,
    )
