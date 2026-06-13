import base64
import json
import os
from pathlib import Path
import re

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from app.api.routes import analytics, dashboard, inventory, orders
from app.database import Base, engine, ensure_sqlite_schema, get_db
from app.models import Alert
from app.schemas import AlertRead, PredictionRead, RiskPredictionRequest
from app.services.ml_predictor import PredictionError, predict_breach

Base.metadata.create_all(bind=engine)
ensure_sqlite_schema()

app = FastAPI(
    title="AI-Powered Eyewear Order Management System",
    version="1.0.0",
    description="Order, inventory, SLA, prediction, and alert APIs for an eyewear operations team.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/alerts", response_model=list[AlertRead])
def list_alerts(db: Session = Depends(get_db)):
    return db.scalars(select(Alert).order_by(Alert.created_at.desc()).limit(50)).all()


@app.post("/api/prescription/parse")
async def parse_prescription(file: UploadFile = File(...)):
    content_type = file.content_type or ""
    if content_type != "application/pdf" and not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload must be a PDF or image file")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY or GEMINI_API_KEY is not configured")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            [
                (
                    "Extract prescription data and return only JSON: "
                    "{sph_od, sph_os, add_power, suggested_lens_type, coating_suggestion, notes}. "
                    "suggested_lens_type must be one of: Single Vision, Bifocal, Progressive. "
                    "If add_power > 0 suggest Progressive."
                ),
                {
                    "inline_data": {
                        "mime_type": content_type,
                        "data": base64.b64encode(file_bytes).decode("utf-8"),
                    }
                },
            ],
            generation_config={"response_mime_type": "application/json"},
        )
        response_text = response.text.strip()
        json_text = re.sub(r"^```(?:json)?|```$", "", response_text, flags=re.IGNORECASE | re.MULTILINE).strip()
        return json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="Gemini response was not valid JSON") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prescription parsing failed: {exc}") from exc


@app.post("/predict-risk", response_model=PredictionRead)
@app.post("/api/predict-risk", response_model=PredictionRead)
def predict_risk(payload: RiskPredictionRequest):
    try:
        return predict_breach(payload.model_dump())
    except PredictionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
