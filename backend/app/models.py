from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lens_type: Mapped[str] = mapped_column(String(40), index=True)
    power: Mapped[float] = mapped_column(Float, index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    reorder_level: Mapped[int] = mapped_column(Integer, default=20)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(120), index=True)
    lens_type: Mapped[str] = mapped_column(String(40), index=True)
    power: Mapped[float] = mapped_column(Float, index=True)
    frame_name: Mapped[str] = mapped_column(String(120))
    store_location: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    sla_hours: Mapped[int] = mapped_column(Integer)
    qc_failures: Mapped[int] = mapped_column(Integer, default=0)
    rework_count: Mapped[int] = mapped_column(Integer, default=0)
    latest_delay_reason: Mapped[str] = mapped_column(String(120), default="None")
    risk_level: Mapped[str] = mapped_column(String(20), default="Low")
    breach_probability: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    alert_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delay_logs: Mapped[list["DelayLog"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class DelayLog(Base):
    __tablename__ = "delay_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    reason: Mapped[str] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    order: Mapped[Order] = relationship(back_populates="delay_logs")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    breach_probability: Mapped[float] = mapped_column(Float, default=0.0)
    alert_type: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[str] = mapped_column(String(80), index=True)
    role: Mapped[str] = mapped_column(String(20))  # "user" or "assistant"
    content: Mapped[str] = mapped_column(String(4000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
