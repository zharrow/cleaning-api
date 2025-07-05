import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from api.core.database import Base

class BaseModel(Base):
    """Modèle de base avec des champs communs"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)

class TimestampedModel(BaseModel):
    """Modèle avec timestamps de création et modification"""
    __abstract__ = True
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
