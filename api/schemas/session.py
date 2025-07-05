import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel
from api.models.session import SessionStatus, LogStatus
from api.schemas.performer import PerformerResponse
from api.schemas.task import AssignedTaskResponse

class CleaningSessionResponse(BaseModel):
    id: uuid.UUID
    date: date
    status: SessionStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CleaningLogCreate(BaseModel):
    session_id: uuid.UUID
    assigned_task_id: uuid.UUID
    performer_id: uuid.UUID
    status: LogStatus = LogStatus.FAIT
    notes: Optional[str] = None

class CleaningLogResponse(BaseModel):
    id: uuid.UUID
    session: CleaningSessionResponse
    assigned_task: AssignedTaskResponse
    performer: PerformerResponse
    status: LogStatus
    notes: Optional[str]
    photos: Optional[List[str]]
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
