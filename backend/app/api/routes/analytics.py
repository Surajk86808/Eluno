from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.constants import LENS_TYPES, ORDER_STATUSES, STORE_LOCATIONS
from app.database import get_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/operations")
def operations_analytics(db: Session = Depends(get_db)):
    orders = [crud.serialize_order(order) for order in crud.get_orders(db)]
    return {
        "by_status": {status: sum(1 for order in orders if order["status"] == status) for status in ORDER_STATUSES},
        "by_lens_type": {lens_type: sum(1 for order in orders if order["lens_type"] == lens_type) for lens_type in LENS_TYPES},
        "by_store": {store: sum(1 for order in orders if order["store_location"] == store) for store in STORE_LOCATIONS},
        "risk_levels": {
            "High": sum(1 for order in orders if order["risk_level"] == "High"),
            "Medium": sum(1 for order in orders if order["risk_level"] == "Medium"),
            "Low": sum(1 for order in orders if order["risk_level"] == "Low"),
        },
    }
