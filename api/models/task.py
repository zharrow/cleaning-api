from sqlalchemy import Column, String, Text, Boolean, Integer, Time, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from api.models.base import TimestampedModel
import enum

class TaskType(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    OCCASIONAL = "occasional"

class TaskTemplate(TimestampedModel):
    __tablename__ = "task_templates"

    # Enterprise scoping
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    default_duration = Column(Integer, default=15, nullable=False)  # Durée en minutes
    estimated_duration = Column(Integer, default=15, nullable=False)  # Durée estimée (pour compatibilité frontend)
    type = Column(Enum(TaskType), default=TaskType.DAILY, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    enterprise = relationship("Enterprise", back_populates="task_templates")
    assigned_tasks = relationship("AssignedTask", back_populates="task_template")

class AssignedTask(TimestampedModel):
    __tablename__ = "assigned_tasks"

    # Foreign keys
    task_template_id = Column(UUID(as_uuid=True), ForeignKey("task_templates.id"), nullable=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True)
    default_performer_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)  # Changed from performers to user

    # Task scheduling
    frequency = Column(JSON, default={"type": "daily", "times_per_day": 1, "days": []})
    suggested_time = Column(Time, nullable=True)
    expected_duration = Column(Integer, default=15, nullable=False)
    order_in_room = Column(Integer, default=0, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    task_template = relationship("TaskTemplate", back_populates="assigned_tasks")
    room = relationship("Room", back_populates="assigned_tasks")
    default_performer = relationship("User", foreign_keys=[default_performer_id], back_populates="assigned_tasks")
    cleaning_logs = relationship("CleaningLog", back_populates="assigned_task")