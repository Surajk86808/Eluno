"""
POST /api/documents/parse-invoice — Generic invoice parser endpoint.

Accepts a PDF or image upload and returns structured invoice data extracted
by Gemini.  Completely separate from the prescription parser.
"""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import InvoiceData
from app.services.invoice_parser_service import parse_invoice

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/parse-invoice", response_model=InvoiceData)
async def parse_invoice_endpoint(file: UploadFile = File(...)):
    content_type = file.content_type or "application/pdf"

    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {content_type}. Supported: PDF, JPEG, PNG, WebP",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        data = await parse_invoice(contents, content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return data
