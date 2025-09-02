from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from api.models.base import TimestampedModel

class Enterprise(TimestampedModel):
    """
    Modèle représentant une entreprise/organisation
    Relation 1:1 avec User (l'admin Firebase qui crée l'entreprise)
    """
    __tablename__ = "enterprises"
    
    # Relation avec l'utilisateur (admin Firebase)
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id"), 
        unique=True,  # 1:1 relation
        nullable=False
    )
    
    # Données de l'entreprise
    name = Column(String(255), nullable=False, comment="Nom de l'entreprise")
    logo_url = Column(Text, nullable=True, comment="URL du logo de l'entreprise")
    legal_form = Column(String(100), nullable=True, comment="Forme juridique (SARL, SAS, etc.)")
    siret = Column(String(14), nullable=True, comment="Numéro SIRET")
    
    # Relations
    user = relationship("User", backref="enterprise", uselist=False)
    
    def __repr__(self):
        return f"<Enterprise(id='{self.id}', name='{self.name}', user_id='{self.user_id}')>"
    
    @property
    def is_complete(self) -> bool:
        """Vérifie si toutes les données essentielles sont renseignées"""
        return bool(self.name and self.siret and self.legal_form)