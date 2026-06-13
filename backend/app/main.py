from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from app.api.routes import analytics, dashboard, inventory, orders
from app.database import Base, engine, ensure_sqlite_schema
from app.schemas import PredictionRead, RiskPredictionRequest
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


@app.post("/predict-risk", response_model=PredictionRead)
@app.post("/api/predict-risk", response_model=PredictionRead)
def predict_risk(payload: RiskPredictionRequest):
    try:
        return predict_breach(payload.model_dump())
    except PredictionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
