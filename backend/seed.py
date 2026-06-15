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
    weighted_statuses = [s for s in ORDER_STATUSES if s not in ["Delivered", "Shipped", "Cancelled", "Rejected"]]
    
    orders_created = []
    for _ in range(150):
        lens_type = random.choice(LENS_TYPES)
        sla_hours = SLA_HOURS_BY_LENS_TYPE[lens_type]
        
        # Default: created_at between 1 and 40 hours ago
        hours_ago = random.uniform(1, 40)
        status = random.choice(weighted_statuses)
        
        # Only Delivered and Shipped orders have created_at older than their SLA deadline
        if random.random() < 0.15:
            status = random.choice(["Delivered", "Shipped"])
            # Make some of them older than SLA
            if random.random() < 0.5:
                hours_ago = random.uniform(sla_hours + 1, sla_hours + 20)
        
        created_at = datetime.utcnow() - timedelta(hours=hours_ago)
        updated_at = created_at + timedelta(hours=random.uniform(0.5, min(hours_ago, 24)))
        
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
        # Backfill ML prediction (ensure breach_probability is between 0.0 and 1.0)
        crud.refresh_prediction(db, order)
        orders_created.append(order)

    # Print reporting
    from app.services.sla import calculate_remaining_sla_hours
    counts = {lt: 0 for lt in LENS_TYPES}
    total_sla_left = 0
    for o in orders_created:
        counts[o.lens_type] += 1
        total_sla_left += calculate_remaining_sla_hours(o)
    
    print("\nSeeding Report:")
    for lt, count in counts.items():
        print(f"Lens Type {lt}: {count} orders")
    print(f"Average SLA Left: {total_sla_left / len(orders_created):.2f} hours")


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
