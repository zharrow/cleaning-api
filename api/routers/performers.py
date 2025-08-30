from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.models.user import User
from api.models.performer import Performer
from api.schemas.performer import PerformerCreate, PerformerUpdate, PerformerResponse

router = APIRouter()

@router.post("", response_model=PerformerResponse)
async def create_performer(
    performer: PerformerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_performer = Performer(**performer.dict())
    db.add(db_performer)
    db.commit()
    db.refresh(db_performer)
    return db_performer

@router.get("", response_model=List[PerformerResponse])
async def get_performers(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Performer)
    if not include_inactive:
        query = query.filter(Performer.is_active == True)
    return query.all()

@router.get("/{performer_id}", response_model=PerformerResponse)
async def get_performer(
    performer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    performer = db.query(Performer).filter(Performer.id == performer_id, Performer.is_active == True).first()
    if not performer:
        raise HTTPException(status_code=404, detail="Performer not found")
    return performer

@router.put("/{performer_id}", response_model=PerformerResponse)
async def update_performer(
    performer_id: str,
    performer_update: PerformerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    performer = db.query(Performer).filter(Performer.id == performer_id, Performer.is_active == True).first()
    if not performer:
        raise HTTPException(status_code=404, detail="Performer not found")
    
    for field, value in performer_update.dict(exclude_unset=True).items():
        setattr(performer, field, value)
    
    db.commit()
    db.refresh(performer)
    return performer

@router.patch("/{performer_id}/toggle", response_model=PerformerResponse)
async def toggle_performer_status(
    performer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    performer = db.query(Performer).filter(Performer.id == performer_id).first()
    if not performer:
        raise HTTPException(status_code=404, detail="Performer not found")
    
    # Toggle le statut is_active
    performer.is_active = not performer.is_active
    db.commit()
    db.refresh(performer)
    
    action = "activated" if performer.is_active else "deactivated"
    return performer

@router.delete("/{performer_id}")
async def delete_performer(
    performer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    performer = db.query(Performer).filter(Performer.id == performer_id, Performer.is_active == True).first()
    if not performer:
        raise HTTPException(status_code=404, detail="Performer not found")
    
    # Soft delete
    performer.is_active = False
    db.commit()
    return {"message": "Performer deleted successfully"}
