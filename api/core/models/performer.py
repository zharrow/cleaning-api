from sqlalchemy import Column, String, Boolean
from api.models.base import BaseModel

class Performer(BaseModel):
    __tablename__ = "performers"
    
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
