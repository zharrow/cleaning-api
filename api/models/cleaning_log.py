from sqlalchemy import Column, Text, ForeignKey, Enum, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from api.models.base import BaseModel
from api.models.session import LogStatus

class CleaningLog(BaseModel):
    """
    Permanent record of completed cleaning tasks
    """
    __tablename__ = "cleaning_logs"

    # Foreign keys
    session_id = Column(UUID(as_uuid=True), ForeignKey("cleaning_sessions.id"), nullable=True, index=True)
    assigned_task_id = Column(UUID(as_uuid=True), ForeignKey("assigned_tasks.id"), nullable=True)

    # Who performed the task and who recorded it (both reference User table now)
    performed_by_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True, index=True)
    recorded_by_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)

    status = Column(Enum(LogStatus), default=LogStatus.REPORTE, nullable=False)
    note = Column(Text, nullable=True)
    photo_urls = Column(JSON, default=list, nullable=True)  # Liste des URLs de photos

    # Timestamp for when task was actually performed
    performed_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("CleaningSession", back_populates="logs")
    assigned_task = relationship("AssignedTask", back_populates="cleaning_logs")
    performed_by = relationship("User", foreign_keys=[performed_by_id], back_populates="performed_logs")
    recorded_by = relationship("User", foreign_keys=[recorded_by_id], back_populates="recorded_logs")