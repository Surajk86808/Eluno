from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import InventoryAvailability, InventoryRead

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=list[InventoryRead])
def list_inventory(db: Session = Depends(get_db)):
    return crud.get_inventory(db)


@router.get("/check", response_model=InventoryAvailability)
def check_inventory(lens_type: str, power: float, db: Session = Depends(get_db)):
    return crud.get_inventory_availability(db, lens_type, power)

