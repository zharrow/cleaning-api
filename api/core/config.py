import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # Base de données
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/cleaning_db")
    
    # Firebase
    firebase_credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    
    # Upload
    uploads_dir: Path = Path(os.getenv("UPLOADS_DIR", "uploads"))
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    # Environnement
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Créer le répertoire uploads s'il n'existe pas
settings.uploads_dir.mkdir(exist_ok=True)
