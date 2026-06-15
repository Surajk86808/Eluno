import base64
import json
import logging
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
from app.database import Base, engine, get_db
from app.models import Alert, Inventory, Order
from app import crud
from app.schemas import AlertRead, OrderRead, PredictionRead, RiskPredictionRequest
from app.services.ml_predictor import PredictionError, predict_breach

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI-Powered Eyewear Order Management System",
    version="1.0.0",
    description="Order, inventory, SLA, prediction, and alert APIs for an eyewear operations team.",
)

# Load allowed origins from environment variable, fallback to common defaults
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


@app.on_event("startup")
def create_database_tables() -> None:
    if os.getenv("AUTO_CREATE_TABLES", "").lower() not in {"1", "true", "yes"}:
        return

    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        logger.exception("Database table initialization failed")


@app.get("/api/inventory/low-stock")
def get_low_stock(db: Session = Depends(get_db)):
    """Query inventory items where quantity < 25."""
    items = db.scalars(select(Inventory).where(Inventory.quantity < 25)).all()
    return [
        {"lens_type": i.lens_type, "power": i.power, "quantity": i.quantity}
        for i in items
    ]


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/orders/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    # Query: db.query(Order).filter(Order.id == order_id).first()
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        # If not found return 404 with message: "Order not found"
        raise HTTPException(status_code=404, detail="Order not found")
    
    # If found return the order with all fields including sla_left_hours and breach_probability computed fresh.
    # refresh_prediction updates breach_probability and risk_level
    order = crud.refresh_prediction(db, order)
    # serialize_order computes remaining_sla_hours fresh
    return crud.serialize_order(order)


@app.get("/api/alerts", response_model=list[AlertRead])
def list_alerts(db: Session = Depends(get_db)):
    alerts = db.scalars(select(Alert).order_by(Alert.created_at.desc()).limit(50)).all()
    return [
        {
            "id": a.id,
            "order_id": a.order_id,
            "customer_name": a.customer_name,
            "breach_percentage": round(a.breach_probability * 100, 2),
            "alert_type": a.alert_type,
            "created_at": a.created_at
        }
        for a in alerts
    ]


@app.post("/api/prescription/parse")
async def parse_prescription(file: UploadFile = File(...)):
    try:
        # Verify GEMINI_API_KEY or GOOGLE_API_KEY is loaded from .env
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY not configured")

        # Verify file is read correctly: contents = await file.read() then base64.b64encode(contents).decode()
        contents = await file.read()
        encoded_data = base64.b64encode(contents).decode()

        import google.generativeai as genai
        # Verify genai.configure(api_key=...) is called before model instantiation
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.5-flash")
        
        content_type = file.content_type or "application/pdf"

        response = model.generate_content(
            [
                (
                    "Extract prescription data and return only JSON: "
                    "{sph_od, sph_os, add_power, suggested_lens_type, coating_suggestion, notes, partial}. "
                    "suggested_lens_type must be one of: Single Vision, Bifocal, Progressive. "
                    "If add_power > 0 suggest Progressive. If this is not a prescription, set partial=true."
                ),
                {
                    "inline_data": {
                        "mime_type": content_type,
                        "data": encoded_data,
                    }
                },
            ],
            generation_config={"response_mime_type": "application/json"},
        )
        
        # If Gemini response is empty or not valid JSON, return 400 with error: "Could not parse prescription"
        if not response or not response.text:
            raise Exception("Could not parse prescription")
            
        try:
            data = json.loads(response.text)
            if data.get("partial") is True:
                 raise Exception("Could not parse prescription")
            return data
        except json.JSONDecodeError:
            raise Exception("Could not parse prescription")

    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/predict-risk", response_model=PredictionRead)
@app.post("/api/predict-risk", response_model=PredictionRead)
def predict_risk(payload: RiskPredictionRequest):
    try:
        prediction = predict_breach(payload.model_dump())
        return {
            "risk_level": prediction["risk_level"],
            "breach_percentage": round(prediction["breach_probability"] * 100, 2)
        }
    except PredictionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
