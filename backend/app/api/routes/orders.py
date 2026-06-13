from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.constants import LENS_TYPES, ORDER_STATUSES, STORE_LOCATIONS
from app.database import get_db
from app.schemas import DelayLogRead, OrderCreate, OrderRead, OrderStatusUpdate, PredictionRead, ReferenceData
from app.services.alerts import evaluate_and_send_alert
from app.services.ml_predictor import predict_breach

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=list[OrderRead])
def list_orders(
    status: str | None = None,
    lens_type: str | None = None,
    store_location: str | None = None,
    db: Session = Depends(get_db),
):
    orders = crud.get_orders(db, status=status, lens_type=lens_type, store_location=store_location)
    return [crud.serialize_order(order) for order in orders]


@router.post("", response_model=OrderRead, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    if payload.lens_type not in LENS_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported lens type")
    if payload.store_location not in STORE_LOCATIONS:
        raise HTTPException(status_code=400, detail="Unsupported store location")

    availability = crud.get_inventory_availability(db, payload.lens_type, payload.power)
    if not availability["exists"]:
        raise HTTPException(status_code=400, detail="Requested lens power is not available in inventory")

    order = crud.create_order(db, payload)
    evaluate_and_send_alert(db, order)
    return crud.serialize_order(order)


@router.patch("/{order_id}/status", response_model=OrderRead)
def update_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    if payload.status not in ORDER_STATUSES:
        raise HTTPException(status_code=400, detail="Unsupported order status")
    order = crud.update_order_status(db, order_id, payload.status, payload.reason)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    evaluate_and_send_alert(db, order)
    return crud.serialize_order(order)


@router.get("/{order_id}/delay-history", response_model=list[DelayLogRead])
def delay_history(order_id: int, db: Session = Depends(get_db)):
    if db.get(crud.Order, order_id) is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return crud.get_delay_history(db, order_id)


@router.get("/{order_id}/prediction", response_model=PredictionRead)
def get_prediction(order_id: int, db: Session = Depends(get_db)):
    order = db.get(crud.Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return predict_breach(crud.build_prediction_payload(db, order))


@router.get("/meta/reference-data", response_model=ReferenceData)
def get_reference_data():
    return ReferenceData()
