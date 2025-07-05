from sqlalchemy import Column, String, Enum
from enum import Enum as PyEnum
from api.models.base import TimestampedModel

class UserRole(PyEnum):
    GERANTE = "gerante"

class User(TimestampedModel):
    __tablename__ = "users"
    
    firebase_uid = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.GERANTE)
