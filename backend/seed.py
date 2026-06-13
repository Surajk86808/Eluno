from datetime import datetime, timedelta
import random

from app.constants import LENS_TYPES, ORDER_STATUSES, SLA_HOURS_BY_LENS_TYPE, STORE_LOCATIONS
from app.database import Base, SessionLocal, engine
from app.models import Inventory, Order


CUSTOMER_FIRST_NAMES = ["Ava", "Liam", "Mia", "Noah", "Sophia", "Ethan", "Isabella", "Lucas", "Amelia", "Mason"]
CUSTOMER_LAST_NAMES = ["Patel", "Johnson", "Garcia", "Kim", "Brown", "Singh", "Davis", "Chen", "Wilson", "Martinez"]
FRAME_NAMES = ["AeroFlex", "Urban Classic", "Vista Pro", "Titan Lite", "Metro Square", "Crystal Edge", "Heritage Round"]


def power_values() -> list[float]:
    return [round(-6.0 + index * 0.5, 1) for index in range(25)]


def seed_inventory(db):
    for lens_type in LENS_TYPES:
        for power in power_values():
            base_quantity = random.randint(18, 140)
            if abs(power) >= 5:
                base_quantity = random.randint(8, 60)
            db.add(
                Inventory(
                    lens_type=lens_type,
                    power=power,
                    quantity=base_quantity,
                    reorder_level=random.choice([15, 20, 25]),
                )
            )


from app import crud

def seed_orders(db):
    weighted_statuses = ORDER_STATUSES[:-1] + ["Lens Cutting", "Coating", "Quality Check", "Packing"]
    for _ in range(150):
        lens_type = random.choice(LENS_TYPES)
        sla_hours = SLA_HOURS_BY_LENS_TYPE[lens_type]
        created_at = datetime.utcnow() - timedelta(hours=random.randint(1, 96), minutes=random.randint(0, 59))
        status = random.choice(weighted_statuses)
        if random.random() < 0.12:
            status = "Delivered"
        updated_at = created_at + timedelta(hours=random.randint(1, min(24, max(sla_hours, 1))))
        order = Order(
            customer_name=f"{random.choice(CUSTOMER_FIRST_NAMES)} {random.choice(CUSTOMER_LAST_NAMES)}",
            lens_type=lens_type,
            power=random.choice(power_values()),
            frame_name=random.choice(FRAME_NAMES),
            store_location=random.choice(STORE_LOCATIONS),
            status=status,
            sla_hours=sla_hours,
            created_at=created_at,
            updated_at=min(updated_at, datetime.utcnow()),
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        # Backfill ML prediction
        crud.refresh_prediction(db, order)


def main():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_inventory(db)
        seed_orders(db)
        db.commit()
    finally:
        db.close()
    print("Seeded 75 inventory rows and 150 orders.")


if __name__ == "__main__":
    main()
