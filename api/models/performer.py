from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from api.models.base import BaseModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Performer(BaseModel):
    __tablename__ = "performers"
    
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", backref="created_performers")