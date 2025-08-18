from sqlalchemy import Column, String, Text, Integer, Boolean
from api.models.base import BaseModel

class Room(BaseModel):
    __tablename__ = "rooms"
    
    name = Column(String, nullable=False)
    description = Column(Text)
    display_order = Column(Integer, default=0)
    image_key = Column(String(255), nullable=True)  # Pour stocker une image de la pièce
    is_active = Column(Boolean, default=True)