from datetime import datetime

from app.constants import TERMINAL_STATUSES
from app.models import Order


def calculate_order_age_hours(order: Order, now: datetime | None = None) -> float:
    current_time = now or datetime.utcnow()
    return max((current_time - order.created_at).total_seconds() / 3600, 0)


def calculate_remaining_sla_hours(order: Order, now: datetime | None = None) -> float:
    if order.status in TERMINAL_STATUSES:
        return 0
    return round(order.sla_hours - calculate_order_age_hours(order, now), 2)


def is_sla_breached(order: Order, now: datetime | None = None) -> bool:
    if order.status in TERMINAL_STATUSES:
        return False
    return calculate_order_age_hours(order, now) > order.sla_hours


def calculate_sla_consumed_percent(order: Order, now: datetime | None = None) -> float:
    if order.sla_hours <= 0:
        return 100
    return min((calculate_order_age_hours(order, now) / order.sla_hours) * 100, 100)

