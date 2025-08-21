from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from api.models.base import TimestampedModel

class Performer(TimestampedModel):
    __tablename__ = "performers"
    
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Clé étrangère vers users avec le bon type UUID
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relation vers l'utilisateur qui a créé ce performer
    created_by = relationship("User", backref="created_performers")