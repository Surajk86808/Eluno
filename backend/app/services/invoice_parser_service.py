"""
Generic Invoice / Document Parser Service

Separate from the prescription parser — this handles vendor invoices.
Uses the same Gemini base64-upload pattern as prescription parsing in main.py,
but with a different prompt and output schema (InvoiceData).
"""
from __future__ import annotations

import base64
import json
import logging
import os

logger = logging.getLogger(__name__)


async def parse_invoice(file_contents: bytes, content_type: str) -> dict:
    """
    Send file to Gemini and extract structured invoice data.

    Returns a dict matching the InvoiceData schema.
    Raises ValueError with a human-readable message on failure.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        encoded = base64.b64encode(file_contents).decode()

        prompt = (
            "You are an invoice data extraction assistant. "
            "Extract structured data from the provided invoice document and return ONLY valid JSON "
            "matching this exact schema:\n"
            "{\n"
            '  "vendor_name": string or null,\n'
            '  "invoice_number": string or null,\n'
            '  "invoice_date": string (YYYY-MM-DD) or null,\n'
            '  "line_items": [\n'
            '    {"description": string, "quantity": number or null, "unit_price": number or null, "total": number or null}\n'
            "  ],\n"
            '  "subtotal": number or null,\n'
            '  "tax": number or null,\n'
            '  "grand_total": number or null\n'
            "}\n"
            "If a field cannot be found, use null. "
            "Do not include any text outside the JSON object. "
            "If this does not appear to be an invoice, set all fields to null and line_items to []."
        )

        response = model.generate_content(
            [
                prompt,
                {
                    "inline_data": {
                        "mime_type": content_type,
                        "data": encoded,
                    }
                },
            ],
            generation_config={"response_mime_type": "application/json"},
        )

        if not response or not response.text:
            raise ValueError("Gemini returned an empty response")

        data = json.loads(response.text)
        return data

    except json.JSONDecodeError as exc:
        raise ValueError("Could not parse invoice: Gemini returned invalid JSON") from exc
    except Exception as exc:
        logger.exception("Invoice parsing failed")
        raise ValueError(f"Invoice parsing failed: {exc}") from exc
