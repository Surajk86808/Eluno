from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import ORDER_STATUSES, SLA_HOURS_BY_LENS_TYPE, TERMINAL_STATUSES
from app.models import DelayLog, Inventory, Order
from app.schemas import OrderCreate
from app.services.ml_predictor import predict_breach
from app.services.sla import calculate_order_age_hours, calculate_remaining_sla_hours, is_sla_breached


def serialize_order(order: Order) -> dict:
    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "lens_type": order.lens_type,
        "power": order.power,
        "frame_name": order.frame_name,
        "store_location": order.store_location,
        "status": order.status,
        "sla_hours": order.sla_hours,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "order_age_hours": round(calculate_order_age_hours(order), 2),
        "remaining_sla_hours": calculate_remaining_sla_hours(order),
        "is_breached": is_sla_breached(order),
        "risk_level": order.risk_level or "Low",
        "breach_percentage": round((order.breach_probability or 0.0) * 100, 2),
        "latest_delay_reason": order.latest_delay_reason or "None",
        "qc_failures": order.qc_failures or 0,
        "rework_count": order.rework_count or 0,
    }


def build_prediction_payload(db: Session, order: Order) -> dict:
    availability = get_inventory_availability(db, order.lens_type, order.power)
    return {
        "lens_type": order.lens_type,
        "current_stage": order.status,
        "order_age_hours": calculate_order_age_hours(order),
        "sla_hours": order.sla_hours,
        "inventory_available": 1 if availability["available_quantity"] > 0 else 0,
        "qc_failures": order.qc_failures,
        "store_location": order.store_location,
        "rework_count": order.rework_count,
        "delay_reason": order.latest_delay_reason or "None",
    }


def refresh_prediction(db: Session, order: Order) -> Order:
    prediction = predict_breach(build_prediction_payload(db, order))
    order.risk_level = str(prediction["risk_level"])
    order.breach_probability = float(prediction["breach_probability"])
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_inventory(db: Session) -> list[Inventory]:
    return list(db.scalars(select(Inventory).order_by(Inventory.lens_type, Inventory.power)))


def get_inventory_availability(db: Session, lens_type: str, power: float) -> dict:
    item = db.scalar(
        select(Inventory).where(
            Inventory.lens_type == lens_type,
            Inventory.power == power,
        )
    )
    quantity = item.quantity if item else 0
    return {
        "lens_type": lens_type,
        "power": power,
        "exists": item is not None,
        "available_quantity": quantity,
        "in_stock": quantity > 0,
        "quantity": quantity,
    }


def create_order(db: Session, payload: OrderCreate) -> Order:
    order = Order(
        customer_name=payload.customer_name,
        lens_type=payload.lens_type,
        power=payload.power,
        frame_name=payload.frame_name,
        store_location=payload.store_location,
        status=ORDER_STATUSES[0],
        sla_hours=SLA_HOURS_BY_LENS_TYPE[payload.lens_type],
        qc_failures=payload.qc_failures,
        rework_count=payload.rework_count,
        latest_delay_reason=payload.delay_reason or "None",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    if payload.delay_reason and payload.delay_reason != "None":
        db.add(DelayLog(order_id=order.id, reason=payload.delay_reason))
        db.commit()
        db.refresh(order)
    return refresh_prediction(db, order)


def get_orders(
    db: Session,
    status: str | None = None,
    lens_type: str | None = None,
    store_location: str | None = None,
) -> list[Order]:
    stmt = select(Order).order_by(Order.created_at.desc())
    if status:
        stmt = stmt.where(Order.status == status)
    if lens_type:
        stmt = stmt.where(Order.lens_type == lens_type)
    if store_location:
        stmt = stmt.where(Order.store_location == store_location)
    return list(db.scalars(stmt))


def get_active_orders(db: Session) -> list[Order]:
    return list(
        db.scalars(
            select(Order)
            .where(Order.status.not_in(TERMINAL_STATUSES))
            .order_by(Order.created_at.desc())
        )
    )


def get_delayed_orders(db: Session) -> list[Order]:
    return [order for order in get_active_orders(db) if is_sla_breached(order)]


def update_order_status(db: Session, order_id: int, status: str, reason: str | None = None) -> Order | None:
    order = db.get(Order, order_id)
    if order is None:
        return None
    order.status = status
    order.updated_at = datetime.utcnow()
    if reason:
        order.latest_delay_reason = reason
        db.add(DelayLog(order_id=order.id, reason=reason))
    db.add(order)
    db.commit()
    db.refresh(order)
    return refresh_prediction(db, order)


def get_delay_history(db: Session, order_id: int) -> list[DelayLog]:
    return list(
        db.scalars(
            select(DelayLog)
            .where(DelayLog.order_id == order_id)
            .order_by(DelayLog.created_at.desc())
        )
    )
