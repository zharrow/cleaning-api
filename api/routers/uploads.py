"""
Router pour la gestion des uploads de fichiers (photos)
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from ..services.local_storage import local_storage
from ..schemas.upload import (
    PhotoUploadResponse,
    MultiplePhotoUploadResponse,
    PhotoDeleteRequest,
    PhotoDeleteResponse
)
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


@router.post(
    "/photo",
    response_model=PhotoUploadResponse,
    summary="Upload une photo",
    description="""
    Upload une seule photo vers Firebase Storage.
    
    **Paramètres optionnels :**
    - `task_id` : ID de la tâche associée (pour organiser les photos)
    - `session_id` : ID de la session associée (pour organiser les photos)
    
    **Contraintes :**
    - Formats acceptés : JPEG, PNG, GIF, WebP
    - Taille maximum : 10 MB
    - L'image sera automatiquement optimisée et redimensionnée si nécessaire
    
    **Retour :**
    - URL publique de l'image uploadée
    - Nom du fichier généré avec timestamp
    - Taille du fichier
    """
)
async def upload_photo(
    file: UploadFile = File(..., description="Fichier image à uploader"),
    task_id: Optional[str] = Form(None, description="ID de la tâche associée"),
    session_id: Optional[str] = Form(None, description="ID de la session associée"),
    current_user: User = Depends(get_current_user)
):
    """Upload une photo vers Firebase Storage"""
    
    try:
        logger.info(f"Début upload photo pour utilisateur {current_user.firebase_uid}")
        
        # Vérifier que le fichier a été fourni
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Aucun fichier fourni"
            )
        
        # Upload vers stockage local
        photo_url = await local_storage.upload_photo(
            file=file,
            folder="photos",
            task_id=task_id,
            session_id=session_id
        )
        
        # Calculer la taille du fichier
        await file.seek(0)  # Reset pour relire
        file_content = await file.read()
        file_size = len(file_content)
        
        # Extraire le nom du fichier depuis l'URL
        filename = photo_url.split('/')[-1].split('?')[0]  # Enlever les paramètres de requête
        
        logger.info(f"Photo uploadée avec succès: {filename}")
        
        return PhotoUploadResponse(
            photo_url=photo_url,
            filename=filename,
            size=file_size
        )
        
    except HTTPException:
        # Re-lever les erreurs HTTP déjà formatées
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'upload: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne lors de l'upload: {str(e)}"
        )


@router.post(
    "/photos",
    response_model=MultiplePhotoUploadResponse,
    summary="Upload plusieurs photos",
    description="""
    Upload plusieurs photos en une seule requête.
    
    **Paramètres optionnels :**
    - `task_id` : ID de la tâche associée (appliqué à toutes les photos)
    - `session_id` : ID de la session associée (appliqué à toutes les photos)
    
    **Contraintes :**
    - Maximum 10 fichiers par requête
    - Chaque fichier suit les mêmes contraintes que l'upload simple
    
    **Retour :**
    - Liste des photos uploadées avec succès
    - Liste des fichiers ayant échoué (le cas échéant)
    - Nombre total de photos traitées
    """
)
async def upload_multiple_photos(
    files: List[UploadFile] = File(..., description="Liste des fichiers images à uploader"),
    task_id: Optional[str] = Form(None, description="ID de la tâche associée"),
    session_id: Optional[str] = Form(None, description="ID de la session associée"),
    current_user: User = Depends(get_current_user)
):
    """Upload plusieurs photos vers Firebase Storage"""
    
    try:
        # Vérifier le nombre de fichiers
        if len(files) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 fichiers autorisés par requête"
            )
        
        if not files or all(not f.filename for f in files):
            raise HTTPException(
                status_code=400,
                detail="Aucun fichier valide fourni"
            )
        
        logger.info(f"Début upload de {len(files)} photos pour utilisateur {current_user.firebase_uid}")
        
        uploaded_photos = []
        failed_uploads = []
        
        for file in files:
            try:
                if not file.filename:
                    failed_uploads.append("Fichier sans nom")
                    continue
                
                # Upload du fichier
                photo_url = await local_storage.upload_photo(
                    file=file,
                    folder="photos",
                    task_id=task_id,
                    session_id=session_id
                )
                
                # Calculer la taille
                await file.seek(0)
                file_content = await file.read()
                file_size = len(file_content)
                
                # Extraire le nom du fichier
                filename = photo_url.split('/')[-1].split('?')[0]
                
                uploaded_photos.append(PhotoUploadResponse(
                    photo_url=photo_url,
                    filename=filename,
                    size=file_size
                ))
                
            except Exception as e:
                logger.warning(f"Erreur upload fichier {file.filename}: {e}")
                failed_uploads.append(file.filename or "Fichier inconnu")
                continue
        
        logger.info(f"Upload terminé: {len(uploaded_photos)} succès, {len(failed_uploads)} échecs")
        
        return MultiplePhotoUploadResponse(
            photos=uploaded_photos,
            total_uploaded=len(uploaded_photos),
            failed_uploads=failed_uploads
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'upload multiple: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne lors de l'upload multiple: {str(e)}"
        )


@router.delete(
    "/photo",
    response_model=PhotoDeleteResponse,
    summary="Supprimer une photo",
    description="""
    Supprime une photo du stockage Firebase Storage.
    
    **Paramètres :**
    - URL complète de la photo à supprimer
    
    **Attention :** Cette action est irréversible !
    """
)
async def delete_photo(
    request: PhotoDeleteRequest,
    current_user: User = Depends(get_current_user)
):
    """Supprimer une photo du stockage"""
    
    try:
        logger.info(f"Demande suppression photo par utilisateur {current_user.firebase_uid}: {request.photo_url}")
        
        # Supprimer la photo
        success = await local_storage.delete_photo(request.photo_url)
        
        if success:
            return PhotoDeleteResponse(
                success=True,
                message="Photo supprimée avec succès",
                photo_url=request.photo_url
            )
        else:
            return PhotoDeleteResponse(
                success=False,
                message="Erreur lors de la suppression de la photo",
                photo_url=request.photo_url
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la suppression: {e}")
        return PhotoDeleteResponse(
            success=False,
            message=f"Erreur interne: {str(e)}",
            photo_url=request.photo_url
        )


@router.get(
    "/health",
    summary="Vérifier la santé du service d'upload",
    description="Endpoint pour vérifier que Firebase Storage est accessible"
)
async def upload_service_health():
    """Vérifier la santé du service d'upload"""
    
    try:
        # Tester le stockage local
        storage_info = local_storage.get_storage_info()

        if storage_info.get("available", False):
            return {
                "status": "healthy",
                "service": "local_storage",
                "storage_info": storage_info,
                "timestamp": "2024-12-11T14:30:22.123456"
            }
        else:
            raise HTTPException(
                status_code=503,
                detail="Service de stockage local non disponible"
            )
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service non disponible: {str(e)}"
        )