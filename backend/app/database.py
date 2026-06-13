from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_URL = f"sqlite:///{BASE_DIR / 'order_management.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_schema() -> None:
    """Apply additive SQLite schema updates for existing local databases."""
    with engine.begin() as connection:
        order_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(orders)")).fetchall()
        }
        additions = {
            "qc_failures": "ALTER TABLE orders ADD COLUMN qc_failures INTEGER DEFAULT 0",
            "rework_count": "ALTER TABLE orders ADD COLUMN rework_count INTEGER DEFAULT 0",
            "latest_delay_reason": "ALTER TABLE orders ADD COLUMN latest_delay_reason VARCHAR(120) DEFAULT 'None'",
            "risk_level": "ALTER TABLE orders ADD COLUMN risk_level VARCHAR(20) DEFAULT 'Low'",
            "breach_probability": "ALTER TABLE orders ADD COLUMN breach_probability FLOAT DEFAULT 0.0",
        }
        for column, statement in additions.items():
            if column not in order_columns:
                connection.execute(text(statement))
