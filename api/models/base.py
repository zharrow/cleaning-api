from sqlalchemy import UUID, Column, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

# Base pour tous les modèles
Base = declarative_base()

class BaseModel(Base):
    """Modèle de base avec des champs communs"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)

class TimestampedModel(Base):
    """
    Modèle de base avec timestamps automatiques et ID UUID
    """
    __abstract__ = True
    
    # ID unique en UUID
    id = Column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False
    )
    
    # Timestamps automatiques
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id='{self.id}')>"