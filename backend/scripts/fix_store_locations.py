from pathlib import Path
import sys

from sqlalchemy import select


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal  # noqa: E402
from app.models import Order  # noqa: E402


STORE_LOCATION_MAP = {
    "Austin North": "Hyderabad",
    "Chicago Loop": "Delhi",
    "Miami Central": "Mumbai",
    "New York Downtown": "Bangalore",
    "San Francisco Market": "Pune",
}


def main() -> None:
    db = SessionLocal()
    updated = 0
    try:
        orders = list(
            db.scalars(
                select(Order).where(Order.store_location.in_(STORE_LOCATION_MAP.keys()))
            )
        )
        for order in orders:
            order.store_location = STORE_LOCATION_MAP[order.store_location]
            db.add(order)
            updated += 1
        db.commit()
        print(f"Updated store location for {updated} orders.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
