from app.models import Order
from app.services.ml_predictor import predict_breach
from app.services.sla import calculate_order_age_hours, calculate_remaining_sla_hours


def predict_sla_risk(order: Order) -> dict:
    prediction = predict_breach(
        {
            "lens_type": order.lens_type,
            "current_stage": order.status,
            "order_age_hours": calculate_order_age_hours(order),
            "sla_hours": order.sla_hours,
            "inventory_available": 1,
            "qc_failures": order.qc_failures,
            "store_location": order.store_location,
            "rework_count": order.rework_count,
            "delay_reason": order.latest_delay_reason,
        }
    )
    return {**prediction, "remaining_time": calculate_remaining_sla_hours(order)}
