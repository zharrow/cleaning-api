import uuid
from datetime import datetime, time
from typing import Optional
from pydantic import BaseModel
from app.schemas.performer import PerformerResponse
from app.schemas.room import RoomResponse

class TaskTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TaskTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AssignedTaskCreate(BaseModel):
    task_template_id: uuid.UUID
    room_id: uuid.UUID
    default_performer_id: uuid.UUID
    frequency_days: int = 1
    times_per_day: int = 1
    suggested_time: Optional[time] = None

class AssignedTaskResponse(BaseModel):
    id: uuid.UUID
    task_template: TaskTemplateResponse
    room: RoomResponse
    default_performer: PerformerResponse
    frequency_days: int
    times_per_day: int
    suggested_time: Optional[time]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
