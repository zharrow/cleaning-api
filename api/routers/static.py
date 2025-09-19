"""
Router pour servir les fichiers statiques (photos)
"""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

router = APIRouter()

# Répertoire des uploads
UPLOADS_DIR = Path("/app/uploads")

@router.get("/photos/{filename}")
async def get_photo(filename: str):
    """Servir une photo depuis le stockage local"""

    try:
        file_path = UPLOADS_DIR / "photos" / filename

        # Vérifier que le fichier existe
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Photo non trouvée"
            )

        # Vérifier que c'est bien un fichier (sécurité)
        if not file_path.is_file():
            raise HTTPException(
                status_code=404,
                detail="Photo non trouvée"
            )

        # Déterminer le type MIME
        suffix = file_path.suffix.lower()
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        media_type = media_type_map.get(suffix, 'application/octet-stream')

        # Retourner le fichier
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la photo {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur interne lors de la récupération de la photo"
        )