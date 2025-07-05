import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class RoomCreate(BaseModel):
    name: str
    description: Optional[str] = None
    display_order: int = 0

class RoomResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    display_order: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
