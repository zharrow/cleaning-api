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

    # Enterprise scoping
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"), nullable=False, index=True)

    date = Column(Date, nullable=False, index=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.EN_COURS, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    enterprise = relationship("Enterprise", back_populates="cleaning_sessions")
    logs = relationship("CleaningLog", back_populates="session", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="session", cascade="all, delete-orphan")

    # Unique constraint: one session per day per enterprise
    __table_args__ = (
        {'schema': None},  # Default schema
    )