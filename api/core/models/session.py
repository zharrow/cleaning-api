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
    
    date = Column(Date, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.EN_COURS)
    notes = Column(Text)

class CleaningLog(BaseModel):
    __tablename__ = "cleaning_logs"
    
    session_id = Column(UUID(as_uuid=True), ForeignKey("cleaning_sessions.id"))
    assigned_task_id = Column(UUID(as_uuid=True), ForeignKey("assigned_tasks.id"))
    performer_id = Column(UUID(as_uuid=True), ForeignKey("performers.id"))
    status = Column(Enum(LogStatus), default=LogStatus.FAIT)
    notes = Column(Text)
    photos = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("CleaningSession")
    assigned_task = relationship("AssignedTask")
    performer = relationship("Performer")
