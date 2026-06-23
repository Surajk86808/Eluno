"""
LLM Chat Agent — Gemini function-calling layer.

Each tool maps directly to a DB query.  The agent receives the user's message
(plus conversation history), decides which tool(s) to call, runs them against
the live database, then summarises the results in plain English.

Business-scope guardrail: if Gemini returns no function call AND the message
appears unrelated to operations, the agent declines politely instead of
hallucinating an answer.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Inventory, Order
from app.constants import TERMINAL_STATUSES

logger = logging.getLogger(__name__)

# ── Tool implementations (pure DB queries) ──────────────────────────────────

def _get_low_stock_items(db: Session, threshold: int = 20) -> list[dict]:
    items = db.scalars(
        select(Inventory).where(Inventory.quantity < threshold)
    ).all()
    return [
        {
            "sku_id": item.id,
            "lens_type": item.lens_type,
            "power": item.power,
            "quantity": item.quantity,
            "reorder_level": item.reorder_level,
        }
        for item in items
    ]


def _get_sla_risk_orders(db: Session, risk_level: str = "high") -> list[dict]:
    normalised = risk_level.capitalize()  # "low" → "Low"
    orders = db.scalars(
        select(Order)
        .where(Order.risk_level == normalised)
        .where(Order.status.not_in(TERMINAL_STATUSES))
        .order_by(Order.breach_probability.desc())
        .limit(50)
    ).all()
    return [
        {
            "order_id": o.id,
            "customer_name": o.customer_name,
            "lens_type": o.lens_type,
            "store_location": o.store_location,
            "status": o.status,
            "risk_level": o.risk_level,
            "breach_probability_pct": round((o.breach_probability or 0) * 100, 1),
        }
        for o in orders
    ]


def _get_order_summary(db: Session, start_date: str | None = None, end_date: str | None = None) -> dict:
    stmt = select(Order)
    if start_date:
        stmt = stmt.where(Order.created_at >= _parse_date(start_date))
    if end_date:
        stmt = stmt.where(Order.created_at <= _parse_date(end_date, end_of_day=True))

    orders = db.scalars(stmt).all()
    counts: dict[str, int] = {}
    for o in orders:
        counts[o.status] = counts.get(o.status, 0) + 1

    return {
        "total": len(orders),
        "by_status": counts,
        "date_range": {"start": start_date, "end": end_date},
    }


def _get_revenue_summary(db: Session, start_date: str | None = None, end_date: str | None = None) -> dict:
    """
    Revenue proxy: we don't store price, so we derive a rough estimate using
    SLA tier as a proxy for order value (Single Vision=₹500, Bifocal=₹800, Progressive=₹1200).
    This is clearly labelled as an estimate in the reply.
    """
    PRICE_PROXY = {"Single Vision": 500, "Bifocal": 800, "Progressive": 1200}

    stmt = select(Order)
    if start_date:
        stmt = stmt.where(Order.created_at >= _parse_date(start_date))
    if end_date:
        stmt = stmt.where(Order.created_at <= _parse_date(end_date, end_of_day=True))

    orders = db.scalars(stmt).all()
    if not orders:
        return {"total_orders": 0, "estimated_revenue": 0, "average_order_value": 0, "note": "No orders in range"}

    total = sum(PRICE_PROXY.get(o.lens_type, 700) for o in orders)
    return {
        "total_orders": len(orders),
        "estimated_revenue_inr": total,
        "average_order_value_inr": round(total / len(orders), 2),
        "note": "Revenue is estimated using lens type price proxies (Single Vision ₹500, Bifocal ₹800, Progressive ₹1200)",
        "date_range": {"start": start_date, "end": end_date},
    }


def _get_stockout_forecast(db: Session, sku_id: int | None = None) -> list[dict]:
    """Call the forecast service; import here to avoid circular deps."""
    from app.services.forecast_service import compute_forecasts
    forecasts = compute_forecasts(db)
    if sku_id is not None:
        forecasts = [f for f in forecasts if f["sku_id"] == sku_id]
    return forecasts


# ── Date helpers ────────────────────────────────────────────────────────────

def _parse_date(value: str, end_of_day: bool = False) -> datetime:
    try:
        d = date.fromisoformat(value)
        dt = datetime(d.year, d.month, d.day)
        if end_of_day:
            dt = dt + timedelta(days=1) - timedelta(seconds=1)
        return dt
    except Exception:
        return datetime.utcnow()


# ── Tool dispatch table ──────────────────────────────────────────────────────

TOOL_DECLARATIONS = [
    {
        "name": "get_low_stock_items",
        "description": (
            "Returns inventory items (SKUs) where current stock is below the given threshold. "
            "Use when the user asks about low stock, items running out, or inventory levels."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "threshold": {
                    "type": "integer",
                    "description": "Stock quantity threshold. Default 20.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_sla_risk_orders",
        "description": (
            "Returns active orders filtered by SLA breach risk level. "
            "Use when the user asks about at-risk orders, high-risk deliveries, or SLA breaches."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "risk_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Risk level to filter by.",
                }
            },
            "required": ["risk_level"],
        },
    },
    {
        "name": "get_order_summary",
        "description": (
            "Returns a count of orders grouped by status, optionally filtered by date range. "
            "Use for questions about order counts, fulfillment rates, or status breakdowns."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "ISO date string YYYY-MM-DD (inclusive). Optional.",
                },
                "end_date": {
                    "type": "string",
                    "description": "ISO date string YYYY-MM-DD (inclusive). Optional.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_revenue_summary",
        "description": (
            "Returns estimated revenue and average order value for a date range. "
            "Use for revenue, sales, or financial performance questions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "ISO date string YYYY-MM-DD (inclusive). Optional.",
                },
                "end_date": {
                    "type": "string",
                    "description": "ISO date string YYYY-MM-DD (inclusive). Optional.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_stockout_forecast",
        "description": (
            "Forecasts when each SKU will run out of stock based on recent consumption. "
            "Use when the user asks which products will run out, stockout predictions, or inventory forecasts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sku_id": {
                    "type": "integer",
                    "description": "Optional specific inventory item ID. Omit to get all SKUs.",
                }
            },
            "required": [],
        },
    },
]


def dispatch_tool(name: str, args: dict, db: Session) -> Any:
    if name == "get_low_stock_items":
        return _get_low_stock_items(db, threshold=args.get("threshold", 20))
    if name == "get_sla_risk_orders":
        return _get_sla_risk_orders(db, risk_level=args.get("risk_level", "high"))
    if name == "get_order_summary":
        return _get_order_summary(db, start_date=args.get("start_date"), end_date=args.get("end_date"))
    if name == "get_revenue_summary":
        return _get_revenue_summary(db, start_date=args.get("start_date"), end_date=args.get("end_date"))
    if name == "get_stockout_forecast":
        return _get_stockout_forecast(db, sku_id=args.get("sku_id"))
    raise ValueError(f"Unknown tool: {name}")


# ── Main agent entry point ──────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an operations copilot for Eluno, an eyewear order management company.
You have access to tools that query live business data: inventory levels, orders, SLA risk, revenue, and stockout forecasts.
Always use the appropriate tool(s) to answer the user's question with real data.
Summarise results concisely in plain English. Include key numbers.
If the question is clearly unrelated to eyewear operations, inventory, orders, or business data, politely decline and explain you can only help with operational queries.
Do NOT make up data — only report what the tools return."""


def run_agent(message: str, history: list[dict], db: Session) -> tuple[str, Any]:
    """
    Run one turn of the agent.

    Returns (reply_text, structured_data_or_None).
    structured_data is passed back to the frontend for rendering as a table/chart.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Agent unavailable: GEMINI_API_KEY is not configured.", None

    try:
        import google.generativeai as genai
        from google.generativeai.types import FunctionDeclaration, Tool

        genai.configure(api_key=api_key)

        # Build tool objects
        tool_declarations = [
            FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=t["parameters"],
            )
            for t in TOOL_DECLARATIONS
        ]
        tools = [Tool(function_declarations=tool_declarations)]

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
            tools=tools,
        )

        # Build conversation history in Gemini format
        gemini_history: list[dict] = []
        for msg in history[-10:]:  # last 10 messages for context
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [{"text": msg["content"]}]})

        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(message)

        # Check for function calls
        structured_data = None
        tool_results: list[dict] = []

        candidate = response.candidates[0] if response.candidates else None
        if candidate:
            for part in candidate.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    fn = part.function_call
                    tool_name = fn.name
                    tool_args = dict(fn.args) if fn.args else {}
                    logger.info("Agent calling tool: %s(%s)", tool_name, tool_args)

                    try:
                        result = dispatch_tool(tool_name, tool_args, db)
                    except Exception as exc:
                        logger.exception("Tool %s failed", tool_name)
                        result = {"error": str(exc)}

                    tool_results.append({"tool": tool_name, "args": tool_args, "result": result})

                    # Keep last tool result as structured data for the frontend
                    if isinstance(result, (list, dict)):
                        structured_data = {"tool": tool_name, "rows": result if isinstance(result, list) else [result]}

        if tool_results:
            # Send tool results back to model for a natural language summary
            function_responses = []
            for tr in tool_results:
                function_responses.append(
                    {
                        "function_response": {
                            "name": tr["tool"],
                            "response": {"result": json.dumps(tr["result"], default=str)},
                        }
                    }
                )
            follow_up = chat.send_message(function_responses)
            reply_text = follow_up.text or "I retrieved the data above."
        else:
            reply_text = response.text or "I'm not sure how to answer that with the available data."

        return reply_text, structured_data

    except Exception as exc:
        logger.exception("Chat agent error")
        return f"Sorry, I encountered an error: {exc}", None
