from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models import Inventory, Order
from app.schemas import DashboardSummary, OrderRead

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/active-orders", response_model=list[OrderRead])
def active_orders(db: Session = Depends(get_db)):
    return [crud.serialize_order(order) for order in crud.get_active_orders(db)]


@router.get("/delayed-orders", response_model=list[OrderRead])
def delayed_orders(db: Session = Depends(get_db)):
    return [crud.serialize_order(order) for order in crud.get_delayed_orders(db)]


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)):
    orders = crud.get_orders(db)
    serialized = [crud.serialize_order(order) for order in orders]
    risk_counts = {"High": 0, "Medium": 0, "Low": 0}
    for order in serialized:
        risk_counts[order["risk_level"]] = risk_counts.get(order["risk_level"], 0) + 1

    inventory_items = db.scalar(select(func.count()).select_from(Inventory)) or 0
    low_stock_items = db.scalar(select(func.count()).select_from(Inventory).where(Inventory.quantity <= Inventory.reorder_level)) or 0
    inventory_available = db.scalar(select(func.coalesce(func.sum(Inventory.quantity), 0))) or 0
    inventory_shortage_orders = sum(
        1
        for order in orders
        if crud.get_inventory_availability(db, order.lens_type, order.power)["available_quantity"] <= 0
    )

    return {
        "total_orders": len(orders),
        "active_orders": len(crud.get_active_orders(db)),
        "delayed_orders": len(crud.get_delayed_orders(db)),
        "inventory_items": inventory_items,
        "low_stock_items": low_stock_items,
        "high_risk_orders": risk_counts["High"],
        "inventory_available": inventory_available,
        "inventory_shortage_orders": inventory_shortage_orders,
        "risk_counts": risk_counts,
    }
