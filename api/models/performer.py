from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from api.models.base import TimestampedModel

class Performer(TimestampedModel):
    """
    DEPRECATED: Legacy model for employees
    Use User model instead (api.models.user.User)
    """
    __tablename__ = "performers"

    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    # Legacy foreign key (disabled to avoid conflicts with new user system)
    # created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by_id = Column(UUID(as_uuid=True), nullable=True)  # No FK constraint

    # Relation vers l'utilisateur qui a créé ce performer (disabled)
    # created_by = relationship("User", backref="created_performers")