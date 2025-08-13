import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Dict

class Settings(BaseSettings):
    """Configuration de l'application avec nouvelles options"""

    disable_csp: bool = os.getenv("DISABLE_CSP", "false").lower() == "true"
    custom_security_headers: Optional[Dict[str, str]] = None
    
    # Base de données
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/cleaning_db")
    
    # Redis (optionnel)
    redis_url: Optional[str] = os.getenv("REDIS_URL", None)
    
    # Firebase
    firebase_credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    
    # Upload
    uploads_dir: Path = Path(os.getenv("UPLOADS_DIR", "uploads"))
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    allowed_file_types: List[str] = ["image/jpeg", "image/png", "image/webp"]
    
    # Sécurité
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    allowed_hosts: List[str] = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Rate limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_period: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    # Environnement
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Scheduled tasks
    enable_scheduler: bool = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
    
    # Email (pour futures notifications)
    smtp_host: Optional[str] = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: Optional[str] = os.getenv("SMTP_USER")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    email_from: str = os.getenv("EMAIL_FROM", "noreply@cleaning-api.com")
    
    @field_validator('allowed_hosts', 'cors_origins', mode='before')
    def split_csv_env(cls, v):
        # Permettre les valeurs .env simples: "a,b,c" pour des champs List[str]
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v

    @field_validator('cors_origins')
    def validate_cors_origins(cls, v):
        if v == ["*"]:
            return v
        # Valider que ce sont des URLs valides
        return [origin.strip() for origin in v if origin.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Créer le répertoire uploads s'il n'existe pas
settings.uploads_dir.mkdir(exist_ok=True)