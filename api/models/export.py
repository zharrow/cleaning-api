from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from api.models.base import BaseModel

class Export(BaseModel):
    __tablename__ = "exports"
    
    session_id = Column(UUID(as_uuid=True), ForeignKey("cleaning_sessions.id"))
    export_type = Column(String)  # "pdf" ou "zip"
    filename = Column(String)
    file_path = Column(String)
    
    session = relationship("CleaningSession")
