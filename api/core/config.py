import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    """Configuration de l'application avec gestion simplifiée"""
    
    # Base de données
    database_url: str = "postgresql://user:password@localhost/cleaning_db"
    
    # Redis (optionnel)
    redis_url: Optional[str] = None
    
    # Firebase
    firebase_credentials_path: Optional[str] = None
    firebase_project_id: Optional[str] = None
    firebase_private_key: Optional[str] = None
    firebase_client_email: Optional[str] = None
    
    # Upload
    uploads_dir: str = "uploads"
    max_file_size: int = 10485760  # 10MB
    allowed_file_types: str = "image/jpeg,image/png,image/webp"
    
    # Sécurité
    secret_key: str = "your-secret-key-here"
    allowed_hosts: str = "localhost,127.0.0.1"
    cors_origins: str = "http://localhost:4200,http://localhost:3000,http://localhost:5173,http://localhost:8080"

    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60
    
    # Environnement
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Scheduled tasks
    enable_scheduler: bool = True
    
    # Email (pour futures notifications)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: str = "noreply@cleaning-api.com"
    
    @property
    def uploads_path(self) -> Path:
        """Retourne le Path pour les uploads"""
        return Path(self.uploads_dir)
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Parse allowed_hosts en liste"""
        if not self.allowed_hosts:
            return ["*"]
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse cors_origins en liste"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Parse allowed_file_types en liste"""
        return [ft.strip() for ft in self.allowed_file_types.split(",") if ft.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Instance globale
settings = Settings()

# Créer le répertoire uploads s'il n'existe pas
settings.uploads_path.mkdir(exist_ok=True)