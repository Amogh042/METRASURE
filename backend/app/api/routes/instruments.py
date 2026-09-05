from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import Instrument, RoleEnum, User
from app.schemas import InstrumentCreate, InstrumentUpdate, InstrumentResponse
from app.api.deps import get_current_active_user, require_role

router = APIRouter(prefix="/instruments", tags=["Instruments"])

@router.get("/", response_model=List[InstrumentResponse])
def get_instruments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return db.query(Instrument).offset(skip).limit(limit).all()

@router.post("/", response_model=InstrumentResponse, status_code=status.HTTP_201_CREATED)
def create_instrument(
    instrument_in: InstrumentCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.LAB_OFFICER, RoleEnum.TECHNICIAN]))
):
    if db.query(Instrument).filter(Instrument.instrument_id == instrument_in.instrument_id).first():
        raise HTTPException(status_code=400, detail="Instrument with this ID already exists")
    if db.query(Instrument).filter(Instrument.serial_number == instrument_in.serial_number).first():
        raise HTTPException(status_code=400, detail="Instrument with this serial number already exists")
        
    db_obj = Instrument(**instrument_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/{id}", response_model=InstrumentResponse)
def get_instrument(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    inst = db.query(Instrument).filter(Instrument.id == id).first()
    if not inst: raise HTTPException(status_code=404, detail="Instrument not found")
    return inst

@router.put("/{id}", response_model=InstrumentResponse)
def update_instrument(
    id: int, 
    instrument_in: InstrumentUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.LAB_OFFICER]))
):
    inst = db.query(Instrument).filter(Instrument.id == id).first()
    if not inst: raise HTTPException(status_code=404, detail="Instrument not found")
    
    update_data = instrument_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(inst, key, value)
        
    db.commit()
    db.refresh(inst)
    return inst

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instrument(id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.ADMIN]))):
    inst = db.query(Instrument).filter(Instrument.id == id).first()
    if not inst: raise HTTPException(status_code=404, detail="Instrument not found")
    db.delete(inst)
    db.commit()
    return None
