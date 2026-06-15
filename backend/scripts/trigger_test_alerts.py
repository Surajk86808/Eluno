import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend directory to sys.path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.crud import update_order_status, refresh_prediction
from app.models import Order
from app.services.alerts import evaluate_and_send_alert
from app.constants import ORDER_STATUSES, DELAY_REASONS

def trigger_test_alerts():
    db = SessionLocal()
    try:
        # Get some active orders
        orders = db.query(Order).filter(Order.status.not_in(['Shipped', 'Delivered'])).limit(15).all()
        
        if not orders:
            print("No active orders found to test.")
            return

        print(f"Found {len(orders)} orders for testing.")

        # Scenario 1: Force SLA Breach (Set created_at to 100 hours ago)
        # We'll do this for the first 5 orders
        for i in range(min(5, len(orders))):
            order = orders[i]
            print(f"Updating Order #{order.id} to be BREACHED (SLA)...")
            order.created_at = datetime.utcnow() - timedelta(hours=100)
            order.alert_sent_at = None # Reset alert status for testing
            db.add(order)
            db.commit()
            
            # Refresh prediction and trigger alert evaluation
            refresh_prediction(db, order)
            evaluate_and_send_alert(db, order)

        # Scenario 2: Force High ML Risk (Set status to 'Coating' with 'Machine Breakdown' and Reworks)
        # We'll do this for the next 5-10 orders
        for i in range(5, min(15, len(orders))):
            order = orders[i]
            print(f"Updating Order #{order.id} to HIGH RISK (ML)...")
            
            # Reset alert status
            order.alert_sent_at = None
            order.qc_failures = 3
            order.rework_count = 2
            db.add(order)
            db.commit()

            # Update status via CRUD to trigger prediction refresh and alerts
            # We use 'Coating' or 'Quality Check' and 'Machine Breakdown' or 'QC Failure'
            status = "Quality Check"
            reason = "Machine Breakdown"
            
            update_order_status(db, order.id, status, reason)
            # update_order_status calls refresh_prediction, but we need to call evaluate_and_send_alert
            evaluate_and_send_alert(db, order)

        print("\nTest updates complete. Check 'backend/app/alerts.log' for results.")

    finally:
        db.close()

if __name__ == "__main__":
    trigger_test_alerts()
