"""Equipment Router - HACCP Module"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.core.auth_dependencies import require_manager
from api.models.user import User
from api.models.enterprise import Enterprise
from api.models.haccp_models import Equipment
from api.schemas.haccp_schemas import EquipmentCreate, EquipmentUpdate, EquipmentResponse

router = APIRouter()

@router.post("", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager)])
async def create_equipment(equipment: EquipmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    db_equipment = Equipment(enterprise_id=enterprise.id, **equipment.dict())
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

@router.get("", response_model=List[EquipmentResponse])
async def get_equipment_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    return db.query(Equipment).filter(Equipment.enterprise_id == enterprise.id).all()

@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(equipment_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id, Equipment.enterprise_id == enterprise.id).first()
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return equipment

@router.put("/{equipment_id}", response_model=EquipmentResponse, dependencies=[Depends(require_manager)])
async def update_equipment(equipment_id: str, payload: EquipmentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id, Equipment.enterprise_id == enterprise.id).first()
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(equipment, key, value)
    db.commit()
    db.refresh(equipment)
    return equipment

@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_manager)])
async def delete_equipment(equipment_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id, Equipment.enterprise_id == enterprise.id).first()
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    db.delete(equipment)
    db.commit()
    return None
