import uuid
from datetime import datetime, time
from typing import Optional
from pydantic import BaseModel
from api.schemas.performer import PerformerResponse
from api.schemas.room import RoomResponse
from typing import List
from pydantic import Field, field_validator
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
    def validate_days(cls, v, values):
        freq_type = values.get('type')
        if freq_type == FrequencyType.WEEKLY:
            for day in v:
                if not 0 <= day <= 6:
                    raise ValueError(f"Pour une fréquence hebdomadaire, les jours doivent être entre 0 et 6. Reçu: {day}")
        elif freq_type == FrequencyType.MONTHLY:
            for day in v:
                if not 1 <= day <= 31:
                    raise ValueError(f"Pour une fréquence mensuelle, les jours doivent être entre 1 et 31. Reçu: {day}")
        return v

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
    frequency_days: FrequencyConfig = Field(default_factory=lambda: FrequencyConfig())
    times_per_day: int = 1
    suggested_time: Optional[time] = None

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
    
    class Config:
        from_attributes = True