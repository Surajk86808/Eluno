import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[1]

# Support DATABASE_URL from environment, fallback to SQLite for local development
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"sqlite:///{BASE_DIR / 'order_management.db'}"
).strip()

# SQLite needs 'check_same_thread: False', but PostgreSQL (Neon) does not.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # Use standard engine for PostgreSQL/Neon
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
