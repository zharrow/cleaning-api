from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from api.models.base import TimestampedModel

class Room(TimestampedModel):
    __tablename__ = "rooms"

    # Enterprise scoping
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=True)
    image_key = Column(String(255), nullable=True)  # Pour stocker une image de la pièce
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    enterprise = relationship("Enterprise", back_populates="rooms")
    user_rooms = relationship("UserRooms", back_populates="room", cascade="all, delete-orphan")
    assigned_tasks = relationship("AssignedTask", back_populates="room")