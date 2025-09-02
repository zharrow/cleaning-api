import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator

class EnterpriseCreate(BaseModel):
    """Schema pour créer une entreprise"""
    name: str = Field(..., min_length=1, max_length=255, description="Nom de l'entreprise")
    logo_url: Optional[str] = Field(None, description="URL du logo de l'entreprise")
    legal_form: Optional[str] = Field(None, max_length=100, description="Forme juridique (SARL, SAS, etc.)")
    siret: Optional[str] = Field(None, min_length=14, max_length=14, description="Numéro SIRET (14 chiffres)")
    
    @validator('siret')
    def validate_siret(cls, v):
        """Valide le format du SIRET"""
        if v is not None:
            # Supprimer les espaces et caractères non numériques
            v = ''.join(filter(str.isdigit, v))
            if len(v) != 14:
                raise ValueError('Le SIRET doit contenir exactement 14 chiffres')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Valide le nom de l'entreprise"""
        if not v or not v.strip():
            raise ValueError('Le nom de l\'entreprise est obligatoire')
        return v.strip()

class EnterpriseUpdate(BaseModel):
    """Schema pour modifier une entreprise"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Nom de l'entreprise")
    logo_url: Optional[str] = Field(None, description="URL du logo de l'entreprise")
    legal_form: Optional[str] = Field(None, max_length=100, description="Forme juridique")
    siret: Optional[str] = Field(None, min_length=14, max_length=14, description="Numéro SIRET")
    
    @validator('siret')
    def validate_siret(cls, v):
        """Valide le format du SIRET"""
        if v is not None:
            v = ''.join(filter(str.isdigit, v))
            if len(v) != 14:
                raise ValueError('Le SIRET doit contenir exactement 14 chiffres')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Valide le nom de l'entreprise"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Le nom de l\'entreprise ne peut pas être vide')
        return v.strip() if v else None

class EnterpriseResponse(BaseModel):
    """Schema pour retourner les données d'une entreprise"""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    logo_url: Optional[str] = None
    legal_form: Optional[str] = None
    siret: Optional[str] = None
    is_complete: bool = Field(description="Indique si toutes les données essentielles sont renseignées")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EnterpriseBasicInfo(BaseModel):
    """Schema pour les informations de base de l'entreprise (header)"""
    name: str
    logo_url: Optional[str] = None
    
    class Config:
        from_attributes = True