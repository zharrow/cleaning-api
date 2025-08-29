import uuid
from datetime import datetime, time
from typing import Optional
from pydantic import BaseModel
from api.schemas.performer import PerformerResponse
from api.schemas.room import RoomResponse
from typing import List
from pydantic import Field, field_validator, model_serializer
from enum import Enum

class FrequencyType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    OCCASIONAL = "occasional"

class FrequencyConfig(BaseModel):
    type: FrequencyType = FrequencyType.DAILY
    times_per_day: int = Field(1, ge=1, le=10)
    days: List[int] = Field(default_factory=list)
    
    @field_validator('days')
    @classmethod
    def validate_days(cls, v):
        # Note: Pour l'instant on simplifie la validation 
        # car on n'a pas accès aux autres champs dans Pydantic v2
        return v

class TaskTemplateCreate(BaseModel):
    name: str  # Le frontend envoie 'name', on le mappe vers 'title' dans le modèle
    description: Optional[str] = None
    category: Optional[str] = None  # Nouveau champ 
    estimated_duration: Optional[int] = None  # Nouveau champ

class TaskTemplateResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    category: Optional[str]
    estimated_duration: Optional[int]
    default_duration: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AssignedTaskCreate(BaseModel):
    task_template_id: str  # Accepter string, sera converti en UUID côté API
    room_id: str  # Accepter string, sera converti en UUID côté API
    default_performer_id: Optional[str] = None  # Optionnel maintenant
    frequency_days: FrequencyConfig = Field(default_factory=lambda: FrequencyConfig())
    times_per_day: int = 1
    suggested_time: Optional[time] = None
    
    @field_validator('task_template_id', 'room_id')
    @classmethod
    def validate_required_uuid_strings(cls, v):
        if isinstance(v, str) and v:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError(f'Invalid UUID string: {v}')
        return str(v)
    
    @field_validator('default_performer_id')
    @classmethod
    def validate_optional_uuid_string(cls, v):
        if v and isinstance(v, str):
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError(f'Invalid UUID string: {v}')
        return v

class AssignedTaskResponse(BaseModel):
    id: uuid.UUID
    task_template: TaskTemplateResponse
    room: RoomResponse
    default_performer: PerformerResponse
    frequency_days: FrequencyConfig = Field(default_factory=lambda: FrequencyConfig())
    times_per_day: int
    suggested_time: Optional[time]
    is_active: bool
    created_at: datetime
    
    @classmethod
    def from_orm_model(cls, obj):
        """Custom factory method to create AssignedTaskResponse from ORM model"""
        frequency = obj.frequency or {}
        
        return cls(
            id=obj.id,
            task_template=obj.task_template,
            room=obj.room,
            default_performer=obj.default_performer,
            frequency_days=frequency,
            times_per_day=frequency.get('times_per_day', 1),
            suggested_time=obj.suggested_time,
            is_active=obj.is_active,
            created_at=obj.created_at
        )
    
    class Config:
        from_attributes = True