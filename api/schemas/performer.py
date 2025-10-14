import uuid
from datetime import datetime
from pydantic import BaseModel

class PerformerCreate(BaseModel):
    name: str

class PerformerUpdate(BaseModel):
    name: str

class PerformerResponse(BaseModel):
    id: uuid.UUID
    name: str  # Will be filled with full_name from User model
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_user(cls, user):
        """Create PerformerResponse from User model"""
        return cls(
            id=user.id,
            name=user.full_name,  # Use computed property full_name
            is_active=user.is_active,
            created_at=user.created_at
        )
