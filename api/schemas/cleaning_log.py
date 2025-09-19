import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class CleaningLogCreate(BaseModel):
    """Schema pour la création d'un log de nettoyage"""
    session_id: uuid.UUID
    assigned_task_id: uuid.UUID
    task_template_id: uuid.UUID
    room_id: uuid.UUID
    status: str  # 'done', 'partial', 'skipped', 'blocked'
    performed_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    photos: Optional[str] = None  # JSON string des URLs
    quality_score: Optional[int] = None

class CleaningLogResponse(BaseModel):
    """Schema pour la réponse d'un log de nettoyage"""
    id: uuid.UUID
    session_id: uuid.UUID
    assigned_task_id: uuid.UUID
    task_template_id: uuid.UUID
    room_id: uuid.UUID
    status: str
    performed_by: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_minutes: Optional[int]
    notes: Optional[str]
    photos: Optional[str]
    quality_score: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Relations incluses
    room_name: Optional[str] = None
    task_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class SessionFinalizationRequest(BaseModel):
    """Schema pour la requête de finalisation de session"""
    task_statuses: List[dict]  # Array de {task_id: string, status: TaskStatus}

class TaskStatus(BaseModel):
    """Schema pour le statut d'une tâche temporaire"""
    status: str
    performed_by: Optional[str] = None
    notes: Optional[str] = None
    photos: Optional[List[str]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None