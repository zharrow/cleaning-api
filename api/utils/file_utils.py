import uuid
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile
from api.core.config import settings

def save_uploaded_file(file: UploadFile, log_id: uuid.UUID) -> str:
    """Sauvegarde un fichier uploadé et retourne le nom du fichier"""
    file_extension = file.filename.split('.')[-1] if file.filename else 'jpg'
    filename = f"{log_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
    file_path = settings.uploads_dir / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return filename

def get_file_path(filename: str) -> Path:
    """Retourne le chemin complet d'un fichier"""
    return settings.uploads_dir / filename
