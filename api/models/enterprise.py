from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from api.models.base import TimestampedModel

class Enterprise(TimestampedModel):
    """
    Enterprise entity - 1 admin = 1 enterprise = 1 daycare
    """
    __tablename__ = "enterprises"

    # Relation 1:1 avec Admin (daycare manager)
    admin_id = Column(
        UUID(as_uuid=True),
        ForeignKey("admin.id"),
        unique=True,
        nullable=False,
        index=True
    )

    # Données de l'entreprise
    name = Column(String(255), nullable=False, comment="Nom de l'entreprise")
    logo_url = Column(String(500), nullable=True, comment="URL du logo de l'entreprise")
    legal_form = Column(String(100), nullable=True, comment="Forme juridique (SARL, SAS, etc.)")
    siret = Column(String(14), nullable=True, comment="Numéro SIRET")

    # Relationships
    admin = relationship("Admin", back_populates="enterprise")
    users = relationship("User", back_populates="enterprise")
    rooms = relationship("Room", back_populates="enterprise")
    task_templates = relationship("TaskTemplate", back_populates="enterprise")
    cleaning_sessions = relationship("CleaningSession", back_populates="enterprise")

    # HACCP relationships
    children = relationship("Child", back_populates="enterprise")
    suppliers = relationship("Supplier", back_populates="enterprise")
    products = relationship("Product", back_populates="enterprise")
    meals = relationship("Meal", back_populates="enterprise")
    equipment = relationship("Equipment", back_populates="enterprise")
    cleaning_haccp = relationship("CleaningHaccp", back_populates="enterprise")
    non_compliances = relationship("NonCompliance", back_populates="enterprise")
    documents = relationship("Document", back_populates="enterprise")

    # Communication relationships
    notifications = relationship("Notification", back_populates="enterprise")

    def __repr__(self):
        return f"<Enterprise(id='{self.id}', name='{self.name}', admin_id='{self.admin_id}')>"

    @property
    def is_complete(self) -> bool:
        """Vérifie si toutes les données essentielles sont renseignées"""
        return bool(self.name and self.siret and self.legal_form)