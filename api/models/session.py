from sqlalchemy import Column, Date, Text, Enum, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime
from api.models.base import BaseModel, TimestampedModel

class SessionStatus(PyEnum):
    EN_COURS = "en_cours"
    COMPLETEE = "completee"
    INCOMPLETE = "incomplete"

class LogStatus(PyEnum):
    FAIT = "fait"
    PARTIEL = "partiel"
    REPORTE = "reporte"
    IMPOSSIBLE = "impossible"

class CleaningSession(TimestampedModel):
    __tablename__ = "cleaning_sessions"
    
    date = Column(Date, nullable=False, unique=True, index=True)  # Une seule session par jour
    status = Column(Enum(SessionStatus), default=SessionStatus.EN_COURS)
    notes = Column(Text)
    
    # Relations
    logs = relationship("CleaningLog", back_populates="session", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="session", cascade="all, delete-orphan")

class CleaningLog(BaseModel):
    __tablename__ = "cleaning_logs"
    
    session_id = Column(UUID(as_uuid=True), ForeignKey("cleaning_sessions.id"), index=True)
    assigned_task_id = Column(UUID(as_uuid=True), ForeignKey("assigned_tasks.id"))
    
    # Qui a fait la tâche et qui l'a enregistrée
    performed_by_id = Column(UUID(as_uuid=True), ForeignKey("performers.id"), index=True)
    recorded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    status = Column(Enum(LogStatus), default=LogStatus.REPORTE)
    note = Column(Text)
    photo_urls = Column(JSON, default=list)  # Liste des URLs de photos
    
    # Horodatage séparé pour quand la tâche a été réellement effectuée
    performed_at = Column(DateTime, nullable=True)
    
    # Relations
    session = relationship("CleaningSession", back_populates="logs")
    assigned_task = relationship("AssignedTask", backref="logs")
    performed_by = relationship("Performer", backref="performed_logs")
    recorded_by = relationship("User", backref="recorded_logs")