from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

# Base pour tous les modèles
Base = declarative_base()

class BaseModel(Base):
    """Modèle de base avec des champs communs - Version UUID cohérente"""
    __abstract__ = True
    
    # ID unique en UUID (cohérent partout)
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )
    
    # Timestamp de création
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )

class TimestampedModel(BaseModel):
    """
    Modèle de base avec timestamps automatiques et ID UUID
    """
    __abstract__ = True
    
    # Timestamp de mise à jour
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id='{self.id}')>"