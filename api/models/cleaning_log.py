from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from api.models.base import TimestampedModel

class CleaningLog(TimestampedModel):
    """
    Modèle pour les logs de nettoyage - enregistrements permanents des tâches réalisées
    Contrairement aux statuts temporaires, ces logs persistent après la fin de session
    """
    __tablename__ = "cleaning_logs"
    
    # Références
    session_id = Column(UUID(as_uuid=True), ForeignKey("cleaning_sessions.id"), nullable=False)
    assigned_task_id = Column(UUID(as_uuid=True), ForeignKey("assigned_tasks.id"), nullable=False)
    task_template_id = Column(UUID(as_uuid=True), ForeignKey("task_templates.id"), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    
    # Statut final de la tâche
    status = Column(String(50), nullable=False)  # 'done', 'partial', 'skipped', 'blocked'
    performed_by = Column(String(255), nullable=True)  # Nom de l'exécutant
    
    # Données d'exécution
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Détails supplémentaires
    notes = Column(Text, nullable=True)
    photos = Column(Text, nullable=True)  # JSON array des URLs des photos
    quality_score = Column(Integer, nullable=True)  # Note qualité de 1 à 5
    
    # Relations
    session = relationship("CleaningSession", backref="cleaning_logs")
    assigned_task = relationship("AssignedTask", backref="cleaning_logs")
    task_template = relationship("TaskTemplate", backref="cleaning_logs")
    room = relationship("Room", backref="cleaning_logs")