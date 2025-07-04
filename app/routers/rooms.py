from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.room import Room
from app.schemas.room import RoomCreate, RoomResponse

router = APIRouter()

@router.post("", response_model=RoomResponse)
async def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_room = Room(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@router.get("", response_model=List[RoomResponse])
async def get_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Room).filter(Room.is_active == True).order_by(Room.display_order).all()
