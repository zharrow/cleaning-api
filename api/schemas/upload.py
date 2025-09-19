"""
Schémas Pydantic pour les uploads de fichiers
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class PhotoUploadResponse(BaseModel):
    """Réponse après upload d'une photo"""
    
    photo_url: str = Field(
        description="URL publique de la photo uploadée"
    )
    filename: str = Field(
        description="Nom du fichier généré"
    )
    size: int = Field(
        description="Taille du fichier en octets"
    )
    uploaded_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de l'upload"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "photo_url": "https://storage.googleapis.com/cleaning-app-toulouse.appspot.com/photos/20241211_143022_abc123_s1_t5.jpg",
                "filename": "20241211_143022_abc123_s1_t5.jpg",
                "size": 245760,
                "uploaded_at": "2024-12-11T14:30:22.123456"
            }
        }


class MultiplePhotoUploadResponse(BaseModel):
    """Réponse après upload de plusieurs photos"""
    
    photos: List[PhotoUploadResponse] = Field(
        description="Liste des photos uploadées avec succès"
    )
    total_uploaded: int = Field(
        description="Nombre total de photos uploadées"
    )
    failed_uploads: List[str] = Field(
        default=[],
        description="Liste des noms de fichiers qui ont échoué"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "photos": [
                    {
                        "photo_url": "https://storage.googleapis.com/cleaning-app-toulouse.appspot.com/photos/20241211_143022_abc123.jpg",
                        "filename": "20241211_143022_abc123.jpg",
                        "size": 245760,
                        "uploaded_at": "2024-12-11T14:30:22.123456"
                    }
                ],
                "total_uploaded": 1,
                "failed_uploads": []
            }
        }


class PhotoDeleteRequest(BaseModel):
    """Requête pour supprimer une photo"""
    
    photo_url: str = Field(
        description="URL de la photo à supprimer"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "photo_url": "https://storage.googleapis.com/cleaning-app-toulouse.appspot.com/photos/20241211_143022_abc123.jpg"
            }
        }


class PhotoDeleteResponse(BaseModel):
    """Réponse après suppression d'une photo"""
    
    success: bool = Field(
        description="Indique si la suppression a réussi"
    )
    message: str = Field(
        description="Message descriptif du résultat"
    )
    photo_url: str = Field(
        description="URL de la photo supprimée"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Photo supprimée avec succès",
                "photo_url": "https://storage.googleapis.com/cleaning-app-toulouse.appspot.com/photos/20241211_143022_abc123.jpg"
            }
        }