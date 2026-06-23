"""
Stockout Forecasting Service

For each SKU (Inventory row), computes average daily consumption from order
line items over the last 30–60 days, then projects days_until_stockout using
a simple linear regression (or moving average fallback).

Model choice: scikit-learn LinearRegression on cumulative-demand vs. day index.
This intentionally replaces the static reorder_level threshold logic for
forward-looking stockout alerts.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Inventory, Order
from app.constants import TERMINAL_STATUSES

logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 60  # how far back to measure consumption
MIN_DAYS_DATA = 3   # minimum days of data before we trust the regression


def _daily_consumption(db: Session, lens_type: str, power: float) -> float:
    """
    Estimate average daily consumption for a (lens_type, power) pair.

    Strategy:
    1. Count delivered orders for this SKU in the last LOOKBACK_DAYS days.
    2. Divide by the number of active days (days where at least one order exists),
       floored to LOOKBACK_DAYS to avoid inflating the rate.
    3. If fewer than MIN_DAYS_DATA data points, fall back to 0 (unknown rate).
    """
    cutoff = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)

    # Count orders (each order consumes 1 unit of the matching lens+power SKU)
    total_orders = db.scalar(
        select(func.count(Order.id))
        .where(Order.lens_type == lens_type)
        .where(Order.power == power)
        .where(Order.created_at >= cutoff)
        .where(Order.status.not_in(["Cancelled", "Rejected"]))
    ) or 0

    if total_orders < MIN_DAYS_DATA:
        # Not enough data — return a minimal non-zero rate to surface low-stock items
        return max(total_orders / LOOKBACK_DAYS, 0.0)

    # Use LinearRegression on (day_index, cumulative_count) to estimate rate
    try:
        from sklearn.linear_model import LinearRegression

        # Fetch order dates
        order_dates = db.scalars(
            select(Order.created_at)
            .where(Order.lens_type == lens_type)
            .where(Order.power == power)
            .where(Order.created_at >= cutoff)
            .where(Order.status.not_in(["Cancelled", "Rejected"]))
            .order_by(Order.created_at.asc())
        ).all()

        if not order_dates:
            return 0.0

        base = order_dates[0].date() if hasattr(order_dates[0], "date") else order_dates[0]
        if isinstance(base, datetime):
            base = base.date()

        day_indices = []
        cumulative = []
        count = 0
        for dt in order_dates:
            d = dt.date() if hasattr(dt, "date") else dt
            if isinstance(d, datetime):
                d = d.date()
            idx = (d - base).days
            count += 1
            day_indices.append([idx])
            cumulative.append(count)

        if len(day_indices) < 2:
            return total_orders / LOOKBACK_DAYS

        X = np.array(day_indices, dtype=float)
        y = np.array(cumulative, dtype=float)
        reg = LinearRegression().fit(X, y)
        daily_rate = float(reg.coef_[0])
        return max(daily_rate, 0.0)

    except Exception:
        logger.exception("LinearRegression fallback to simple average for %s %.2f", lens_type, power)
        return total_orders / LOOKBACK_DAYS


def compute_forecasts(db: Session) -> list[dict]:
    """
    Compute stockout forecast for every SKU in the inventory table.
    Returns a list sorted by days_remaining ascending (most urgent first).
    """
    items = db.scalars(select(Inventory)).all()
    today = date.today()
    results = []

    for item in items:
        avg_daily = _daily_consumption(db, item.lens_type, item.power)

        if avg_daily > 0:
            days_remaining = item.quantity / avg_daily
            stockout_date = (today + timedelta(days=days_remaining)).isoformat()
        else:
            # No consumption → won't stock out (or unknown)
            days_remaining = None
            stockout_date = None

        results.append(
            {
                "sku_id": item.id,
                "lens_type": item.lens_type,
                "power": item.power,
                "current_stock": item.quantity,
                "avg_daily_consumption": round(avg_daily, 4),
                "predicted_stockout_date": stockout_date,
                "days_remaining": round(days_remaining, 1) if days_remaining is not None else None,
            }
        )

    # Sort: items with a days_remaining first (most urgent), then no-consumption items
    results.sort(
        key=lambda r: (r["days_remaining"] is None, r["days_remaining"] or float("inf"))
    )
    return results
