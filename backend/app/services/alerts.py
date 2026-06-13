from datetime import datetime
from email.message import EmailMessage
import logging
import os
from pathlib import Path
import smtplib

from sqlalchemy.orm import Session

from app.models import Order
from app.services.sla import calculate_remaining_sla_hours, is_sla_breached


logger = logging.getLogger(__name__)
ALERT_LOG_PATH = Path(__file__).resolve().parents[1] / "alerts.log"
ALERT_THRESHOLD = 80.0


def should_send_alert(order: Order) -> bool:
    return (order.breach_probability or 0.0) >= ALERT_THRESHOLD or is_sla_breached(order)


def _alert_body(order: Order) -> str:
    return (
        "High Risk SLA Breach Alert\n\n"
        f"Order ID: {order.id}\n"
        f"Current Status: {order.status}\n"
        f"Risk Level: {order.risk_level}\n"
        f"Probability: {round(order.breach_probability or 0.0, 2)}%\n"
        f"Time Remaining: {calculate_remaining_sla_hours(order)} hours\n"
    )


def _write_alert_log(order: Order, note: str) -> None:
    message = (
        f"{datetime.utcnow().isoformat()} | SLA ALERT | order_id={order.id} | "
        f"status={order.status} | risk={order.risk_level} | "
        f"probability={round(order.breach_probability or 0.0, 2)} | {note}\n"
    )
    ALERT_LOG_PATH.write_text(
        ALERT_LOG_PATH.read_text(encoding="utf-8") + message if ALERT_LOG_PATH.exists() else message,
        encoding="utf-8",
    )


def send_email_alert(order: Order) -> bool:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("ALERT_RECIPIENT", smtp_user or "")

    if not all([smtp_host, smtp_user, smtp_password, recipient]):
        logger.warning("SMTP configuration is incomplete; alert recorded in local log")
        _write_alert_log(order, "email_not_sent=smtp_not_configured")
        return False

    message = EmailMessage()
    message["Subject"] = "High Risk SLA Breach Alert"
    message["From"] = smtp_user
    message["To"] = recipient
    message.set_content(_alert_body(order))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(message)
        _write_alert_log(order, "email_sent=true")
        return True
    except Exception:
        logger.exception("Failed to send SLA alert email for order %s", order.id)
        _write_alert_log(order, "email_sent=false")
        return False


def evaluate_and_send_alert(db: Session, order: Order) -> None:
    if order.alert_sent_at is None and should_send_alert(order):
        if send_email_alert(order):
            order.alert_sent_at = datetime.utcnow()
            db.add(order)
            db.commit()
            db.refresh(order)
