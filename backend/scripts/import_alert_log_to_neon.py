import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
ALERT_LOG_PATH = BACKEND_DIR / "app" / "alerts.log"

sys.path.append(str(BACKEND_DIR))

from app.models import Alert, Order  # noqa: E402


LOG_PATTERN = re.compile(
    r"^(?P<created_at>[^|]+)\s+\|\s+SLA ALERT\s+\|\s+order_id=(?P<order_id>\d+)\s+\|"
    r".*?\|\s+risk=(?P<risk>[^|]+)\s+\|\s+"
    r"(?:(?:probability=(?P<probability>[0-9.]+))|(?:breach_percentage=(?P<breach_percentage>[0-9.]+)%))"
)


def parse_alert_line(line: str) -> dict | None:
    match = LOG_PATTERN.search(line)
    if not match:
        return None

    probability = match.group("probability")
    breach_percentage = match.group("breach_percentage")
    breach_probability = (
        float(probability)
        if probability is not None
        else round(float(breach_percentage) / 100, 4)
    )
    risk = match.group("risk").strip()

    return {
        "created_at": datetime.fromisoformat(match.group("created_at").strip()),
        "order_id": int(match.group("order_id")),
        "breach_probability": breach_probability,
        "alert_type": "High Risk" if risk == "High" else "SLA Alert",
    }


def main():
    load_dotenv(ROOT_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is not set.")
    if not ALERT_LOG_PATH.exists():
        raise SystemExit(f"Alert log not found: {ALERT_LOG_PATH}")

    parsed_alerts = [
        parsed
        for line in ALERT_LOG_PATH.read_text(encoding="utf-8").splitlines()
        if (parsed := parse_alert_line(line))
    ]

    engine = create_engine(database_url)
    inserted = 0
    skipped_existing = 0
    skipped_missing_order = 0

    with Session(engine) as db:
        existing_order_ids = set(db.scalars(select(Alert.order_id)).all())
        for parsed in parsed_alerts:
            if parsed["order_id"] in existing_order_ids:
                skipped_existing += 1
                continue

            order = db.get(Order, parsed["order_id"])
            if order is None:
                skipped_missing_order += 1
                continue

            db.add(
                Alert(
                    order_id=order.id,
                    customer_name=order.customer_name,
                    breach_probability=parsed["breach_probability"],
                    alert_type=parsed["alert_type"],
                    created_at=parsed["created_at"],
                )
            )
            if order.alert_sent_at is None:
                order.alert_sent_at = parsed["created_at"]
                db.add(order)
            existing_order_ids.add(order.id)
            inserted += 1

        db.commit()

    print(f"Parsed log alerts: {len(parsed_alerts)}")
    print(f"Inserted into Neon: {inserted}")
    print(f"Skipped existing order alerts: {skipped_existing}")
    print(f"Skipped missing orders: {skipped_missing_order}")


if __name__ == "__main__":
    main()
