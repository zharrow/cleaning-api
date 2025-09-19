from sqlalchemy import Column, String, Enum, Boolean
from enum import Enum as PyEnum
from api.models.base import TimestampedModel

class UserRole(PyEnum):
    ADMIN = "admin"
    MANAGER = "manager"

class User(TimestampedModel):
    __tablename__ = "users"
    
    firebase_uid = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MANAGER)
    is_active = Column(Boolean, default=True)
    
    @property
    def can_manage(self) -> bool:
        """Vérifie si l'utilisateur peut gérer l'application"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]