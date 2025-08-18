from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from api.models.base import BaseModel

class Export(BaseModel):
    __tablename__ = "exports"
    
    session_id = Column(UUID(as_uuid=True), ForeignKey("cleaning_sessions.id"), index=True)
    pdf_url = Column(String(500), nullable=True)  # Chemin vers le PDF généré
    zip_url = Column(String(500), nullable=True)  # Chemin vers le ZIP des photos
    exported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relations
    session = relationship("CleaningSession", back_populates="exports")