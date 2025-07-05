from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.models.user import User
from api.models.performer import Performer
from api.schemas.performer import PerformerCreate, PerformerResponse

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Performer).filter(Performer.is_active == True).all()
