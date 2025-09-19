"""
Service de stockage local pour les uploads de photos
Alternative gratuite à Firebase Storage
"""

import os
import uuid
import logging
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import aiofiles
from fastapi import UploadFile, HTTPException
from PIL import Image
import io

logger = logging.getLogger(__name__)

class LocalStorageService:
    """Service de stockage local pour les photos"""

    def __init__(self):
        # Répertoire de stockage dans le container Render
        self.upload_dir = Path("/app/uploads")
        self.photos_dir = self.upload_dir / "photos"

        # Créer les répertoires s'ils n'existent pas
        self.photos_dir.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        self.max_image_size = (1920, 1080)  # Redimensionner si plus grand
        self.compression_quality = 85

        logger.info(f"LocalStorageService initialisé - Répertoire: {self.photos_dir}")

    def _generate_filename(self, original_filename: str, task_id: Optional[str] = None,
                          session_id: Optional[str] = None) -> str:
        """Génère un nom de fichier unique"""

        # Extraire l'extension
        ext = Path(original_filename).suffix.lower()
        if ext not in self.allowed_extensions:
            raise HTTPException(400, f"Extension non autorisée: {ext}")

        # Créer un nom unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]

        # Préfixe optionnel basé sur les IDs
        prefix = ""
        if session_id:
            prefix += f"session_{session_id}_"
        if task_id:
            prefix += f"task_{task_id}_"

        filename = f"{prefix}{timestamp}_{unique_id}{ext}"
        return filename

    def _validate_file(self, file: UploadFile) -> None:
        """Valide le fichier uploadé"""

        # Vérifier l'extension
        ext = Path(file.filename).suffix.lower()
        if ext not in self.allowed_extensions:
            raise HTTPException(
                400,
                f"Format de fichier non autorisé. Autorisés: {', '.join(self.allowed_extensions)}"
            )

    async def _optimize_image(self, file_content: bytes, filename: str) -> bytes:
        """Optimise et compresse l'image"""

        try:
            # Ouvrir l'image avec Pillow
            image = Image.open(io.BytesIO(file_content))

            # Convertir en RGB si nécessaire (pour JPEG)
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')

            # Redimensionner si trop grande
            if image.size[0] > self.max_image_size[0] or image.size[1] > self.max_image_size[1]:
                image.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
                logger.info(f"Image redimensionnée à {image.size}")

            # Sauvegarder en mémoire avec compression
            output = io.BytesIO()

            # Déterminer le format de sortie
            ext = Path(filename).suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                image.save(output, format='JPEG', quality=self.compression_quality, optimize=True)
            elif ext == '.png':
                image.save(output, format='PNG', optimize=True)
            elif ext == '.webp':
                image.save(output, format='WEBP', quality=self.compression_quality, optimize=True)
            else:
                # Fallback vers JPEG
                image.save(output, format='JPEG', quality=self.compression_quality, optimize=True)

            return output.getvalue()

        except Exception as e:
            logger.warning(f"Impossible d'optimiser l'image {filename}: {e}")
            # Retourner l'image originale si l'optimisation échoue
            return file_content

    async def upload_photo(self, file: UploadFile, folder: str = "photos",
                          task_id: Optional[str] = None,
                          session_id: Optional[str] = None) -> str:
        """
        Upload une photo vers le stockage local

        Returns:
            str: URL relative de la photo uploadée
        """

        try:
            # Validation
            self._validate_file(file)

            # Lire le contenu du fichier
            file_content = await file.read()

            # Vérifier la taille
            if len(file_content) > self.max_file_size:
                raise HTTPException(
                    400,
                    f"Fichier trop volumineux. Maximum: {self.max_file_size // (1024*1024)}MB"
                )

            # Générer le nom de fichier
            filename = self._generate_filename(file.filename, task_id, session_id)

            # Optimiser l'image
            optimized_content = await self._optimize_image(file_content, filename)

            # Chemin de destination
            file_path = self.photos_dir / filename

            # Sauvegarder le fichier
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(optimized_content)

            # URL relative pour l'API
            photo_url = f"/uploads/photos/{filename}"

            logger.info(f"Photo sauvegardée: {filename} ({len(optimized_content)} bytes)")

            return photo_url

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur upload photo: {e}")
            raise HTTPException(500, f"Erreur interne lors de l'upload: {str(e)}")

    async def delete_photo(self, photo_url: str) -> bool:
        """
        Supprime une photo du stockage local

        Args:
            photo_url: URL relative de la photo (/uploads/photos/filename.jpg)

        Returns:
            bool: True si suppression réussie
        """

        try:
            # Extraire le nom de fichier de l'URL
            filename = Path(photo_url).name
            file_path = self.photos_dir / filename

            # Vérifier que le fichier existe
            if not file_path.exists():
                logger.warning(f"Fichier non trouvé pour suppression: {file_path}")
                return False

            # Supprimer le fichier
            file_path.unlink()

            logger.info(f"Photo supprimée: {filename}")
            return True

        except Exception as e:
            logger.error(f"Erreur suppression photo {photo_url}: {e}")
            return False

    def get_storage_info(self) -> dict:
        """Retourne des informations sur le stockage"""

        try:
            # Compter les fichiers
            photo_files = list(self.photos_dir.glob("*"))
            total_files = len(photo_files)

            # Calculer la taille totale
            total_size = sum(f.stat().st_size for f in photo_files if f.is_file())
            total_size_mb = total_size / (1024 * 1024)

            return {
                "storage_type": "local",
                "photos_directory": str(self.photos_dir),
                "total_files": total_files,
                "total_size_mb": round(total_size_mb, 2),
                "available": True
            }

        except Exception as e:
            logger.error(f"Erreur info stockage: {e}")
            return {
                "storage_type": "local",
                "error": str(e),
                "available": False
            }

# Instance globale du service
local_storage = LocalStorageService()