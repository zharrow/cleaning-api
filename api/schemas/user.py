import uuid
from datetime import datetime
from pydantic import BaseModel
from api.models.user import UserRole

class UserCreate(BaseModel):
    firebase_uid: str
    full_name: str
    role: UserRole = UserRole.GERANTE

class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None

class UserResponse(BaseModel):
    id: uuid.UUID
    firebase_uid: str
    full_name: str
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True
