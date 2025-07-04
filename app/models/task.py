from sqlalchemy import Column, String, Text, Boolean, Integer, Time, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class TaskTemplate(BaseModel):
    __tablename__ = "task_templates"
    
    name = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

class AssignedTask(BaseModel):
    __tablename__ = "assigned_tasks"
    
    task_template_id = Column(UUID(as_uuid=True), ForeignKey("task_templates.id"))
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"))
    default_performer_id = Column(UUID(as_uuid=True), ForeignKey("performers.id"))
    frequency_days = Column(Integer, default=1)
    times_per_day = Column(Integer, default=1)
    suggested_time = Column(Time)
    is_active = Column(Boolean, default=True)
    
    task_template = relationship("TaskTemplate")
    room = relationship("Room")
    default_performer = relationship("Performer")
