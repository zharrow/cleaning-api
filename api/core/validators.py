"""
Validateurs personnalisés pour une validation plus stricte
"""

from typing import Optional
import re
from pydantic import validator, constr
from datetime import datetime, time

# Patterns de validation
PHONE_PATTERN = re.compile(r'^(?:\+33|0)[1-9](?:\d{8})$')
NAME_PATTERN = re.compile(r'^[a-zA-ZÀ-ÿ\s\-\']{2,50}$')
ROOM_NAME_PATTERN = re.compile(r'^[a-zA-ZÀ-ÿ0-9\s\-\']{2,50}$')

class ValidationMixin:
    """Mixin pour ajouter des validations communes"""
    
    @validator('name', 'full_name')
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Le nom ne peut pas être vide")
        
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Le nom doit contenir au moins 2 caractères")
        if len(v) > 50:
            raise ValueError("Le nom ne peut pas dépasser 50 caractères")
        if not NAME_PATTERN.match(v):
            raise ValueError("Le nom contient des caractères non autorisés")
        
        return v
    
    @validator('phone_number')
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        
        v = v.replace(' ', '').replace('.', '').replace('-', '')
        if not PHONE_PATTERN.match(v):
            raise ValueError("Numéro de téléphone invalide")
        
        return v