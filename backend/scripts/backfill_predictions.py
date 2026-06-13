from pathlib import Path
import sys

from sqlalchemy import select


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app import crud  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import Order  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        orders = list(db.scalars(select(Order).order_by(Order.id)))
        for order in orders:
            crud.refresh_prediction(db, order)
        print(f"Backfilled predictions for {len(orders)} orders.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
