import uuid
from datetime import datetime
from pydantic import BaseModel

class PerformerCreate(BaseModel):
    name: str

class PerformerUpdate(BaseModel):
    name: str

class PerformerResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
