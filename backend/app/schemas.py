from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.constants import DELAY_REASONS, LENS_TYPES, ORDER_STATUSES, STORE_LOCATIONS


class InventoryBase(BaseModel):
    lens_type: str
    power: float
    quantity: int = Field(ge=0)
    reorder_level: int = Field(default=20, ge=0)


class InventoryCreate(InventoryBase):
    pass


class InventoryRead(InventoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime


class InventoryAvailability(BaseModel):
    lens_type: str
    power: float
    exists: bool
    available_quantity: int


class OrderCreate(BaseModel):
    customer_name: str
    lens_type: str
    power: float
    frame_name: str
    store_location: str
    qc_failures: int = Field(default=0, ge=0)
    rework_count: int = Field(default=0, ge=0)
    delay_reason: str = "None"


class OrderStatusUpdate(BaseModel):
    status: str
    reason: str | None = None


class PredictionRead(BaseModel):
    risk_level: str
    breach_probability: float


class RiskPredictionRequest(BaseModel):
    lens_type: str
    current_stage: str
    order_age_hours: float = Field(ge=0)
    sla_hours: float = Field(gt=0)
    inventory_available: int = Field(ge=0)
    qc_failures: int = Field(default=0, ge=0)
    store_location: str
    rework_count: int = Field(default=0, ge=0)
    delay_reason: str = "None"


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    lens_type: str
    power: float
    frame_name: str
    store_location: str
    status: str
    sla_hours: int
    created_at: datetime
    updated_at: datetime
    order_age_hours: float
    remaining_sla_hours: float
    is_breached: bool
    risk_level: str
    breach_probability: float
    latest_delay_reason: str
    qc_failures: int
    rework_count: int


class DelayLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    reason: str
    created_at: datetime


class DashboardSummary(BaseModel):
    total_orders: int
    active_orders: int
    delayed_orders: int
    inventory_items: int
    low_stock_items: int
    high_risk_orders: int
    inventory_available: int
    inventory_shortage_orders: int
    risk_counts: dict[str, int]


class ReferenceData(BaseModel):
    lens_types: list[str] = LENS_TYPES
    order_statuses: list[str] = ORDER_STATUSES
    store_locations: list[str] = STORE_LOCATIONS
    delay_reasons: list[str] = DELAY_REASONS
