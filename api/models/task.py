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
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # Nouveau champ pour la catégorie
    default_duration = Column(Integer, default=15, nullable=False)  # Durée en minutes
    estimated_duration = Column(Integer, default=15, nullable=False)  # Durée estimée (pour compatibilité frontend)
    type = Column(Enum(TaskType), default=TaskType.DAILY, nullable=False)
    is_active = Column(Boolean, default=True)

class AssignedTask(TimestampedModel):
    __tablename__ = "assigned_tasks"
    
    # Clés étrangères avec le bon type UUID
    task_template_id = Column(UUID(as_uuid=True), ForeignKey("task_templates.id"))
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"))
    default_performer_id = Column(UUID(as_uuid=True), ForeignKey("performers.id"), nullable=True)
    
    # Nouveau système de fréquence flexible (JSON)
    frequency = Column(JSON, default={"type": "daily", "times_per_day": 1, "days": []})
    
    suggested_time = Column(Time, nullable=True)
    expected_duration = Column(Integer, default=15, nullable=False)  # Durée attendue en minutes
    order_in_room = Column(Integer, default=0)  # Ordre d'affichage dans la pièce
    is_active = Column(Boolean, default=True)
    
    # Relations
    task_template = relationship("TaskTemplate", backref="assignments")
    room = relationship("Room", backref="assigned_tasks")
    default_performer = relationship("Performer", backref="default_tasks")