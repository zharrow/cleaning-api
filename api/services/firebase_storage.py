"""
Service Firebase Storage pour l'upload d'images
"""

import uuid
import logging
from datetime import datetime
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image
from firebase_admin import storage
from fastapi import UploadFile, HTTPException
from pathlib import Path

from ..core.firebase import initialize_firebase

logger = logging.getLogger(__name__)


class FirebaseStorageService:
    """Service pour gérer les uploads d'images vers Firebase Storage"""
    
    def __init__(self):
        self.bucket = None
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialise la connexion au bucket Firebase Storage"""
        try:
            # Initialiser Firebase Admin SDK d'abord
            if not initialize_firebase():
                logger.error("Impossible d'initialiser Firebase Admin SDK")
                self.bucket = None
                return
            
            # Spécifier explicitement le nom du bucket
            bucket_name = "cleaning-app-toulouse.appspot.com"
            self.bucket = storage.bucket(bucket_name)
            logger.info(f"Firebase Storage initialisé avec succès: {bucket_name}")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation Firebase Storage: {e}")
            # Ne pas lever HTTPException dans le constructeur
            self.bucket = None
    
    def _validate_image(self, file: UploadFile) -> None:
        """Valide le fichier image uploadé"""
        # Vérifier le type MIME
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Le fichier doit être une image (JPEG, PNG, etc.)"
            )
        
        # Vérifier la taille du fichier (10 MB max)
        if hasattr(file, 'size') and file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="La taille du fichier ne doit pas dépasser 10 MB"
            )
    
    def _optimize_image(self, image_bytes: bytes, max_size: Tuple[int, int] = (1920, 1080)) -> bytes:
        """Optimise l'image pour réduire sa taille"""
        try:
            # Ouvrir l'image avec Pillow
            with Image.open(BytesIO(image_bytes)) as img:
                # Convertir en RGB si nécessaire
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensionner si l'image est trop grande
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Sauvegarder avec compression
                output = BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                return output.getvalue()
        
        except Exception as e:
            logger.warning(f"Impossible d'optimiser l'image: {e}")
            # Retourner l'image originale si l'optimisation échoue
            return image_bytes
    
    async def upload_photo(
        self, 
        file: UploadFile, 
        folder: str = "photos",
        task_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Upload une photo vers Firebase Storage et retourne l'URL publique
        
        Args:
            file: Fichier image à uploader
            folder: Dossier de destination dans le bucket
            task_id: ID de la tâche associée (optionnel)
            session_id: ID de la session associée (optionnel)
            
        Returns:
            str: URL publique de l'image uploadée
        """
        try:
            # Vérifier que Firebase Storage est initialisé
            if not self.bucket:
                raise HTTPException(
                    status_code=503,
                    detail="Service Firebase Storage non disponible"
                )
            
            # Valider le fichier
            self._validate_image(file)
            
            # Lire le contenu du fichier
            file_content = await file.read()
            
            # Optimiser l'image
            optimized_content = self._optimize_image(file_content)
            
            # Générer un nom unique pour le fichier
            file_extension = Path(file.filename or "image.jpg").suffix.lower()
            if not file_extension:
                file_extension = ".jpg"
            
            # Construire le nom du fichier avec timestamp et UUID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            
            # Ajouter les IDs si fournis
            filename_parts = [timestamp, unique_id]
            if session_id:
                filename_parts.append(f"s{session_id}")
            if task_id:
                filename_parts.append(f"t{task_id}")
            
            filename = f"{'_'.join(filename_parts)}{file_extension}"
            blob_path = f"{folder}/{filename}"
            
            # Upload vers Firebase Storage
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(
                optimized_content,
                content_type='image/jpeg'
            )
            
            # Rendre le fichier public
            blob.make_public()
            
            # Récupérer l'URL publique
            public_url = blob.public_url
            
            logger.info(f"Photo uploadée avec succès: {blob_path}")
            return public_url
            
        except HTTPException:
            # Re-lever les erreurs HTTP déjà formatées
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'upload: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'upload de l'image: {str(e)}"
            )
    
    async def delete_photo(self, photo_url: str) -> bool:
        """
        Supprime une photo du stockage Firebase
        
        Args:
            photo_url: URL de la photo à supprimer
            
        Returns:
            bool: True si supprimé avec succès
        """
        try:
            # Extraire le nom du blob depuis l'URL
            # Format URL: https://storage.googleapis.com/bucket-name/path/filename
            if "storage.googleapis.com" in photo_url:
                # Extraire le chemin après le nom du bucket
                parts = photo_url.split('/')
                blob_path = '/'.join(parts[4:])  # Skip https://storage.googleapis.com/bucket-name/
            else:
                logger.warning(f"URL non reconnue: {photo_url}")
                return False
            
            # Supprimer le blob
            blob = self.bucket.blob(blob_path)
            blob.delete()
            
            logger.info(f"Photo supprimée avec succès: {blob_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            return False


# Instance singleton du service
firebase_storage = FirebaseStorageService()