# main.py - CORRECTION DES DOUBLES PREFIXES ET TAGS
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
from contextlib import asynccontextmanager

from api.core.config import settings
from api.core.database import engine
from api.models import Base

# Import des routers
from api.routers import (
    auth,           # ✅ Corrigé: plus de double prefix
    performers,     # Gestion des employés
    rooms,          # Gestion des pièces
    tasks,          # Gestion des tâches
    sessions,       # Sessions de nettoyage
    logs,           # Logs de tâches
    exports,        # Exports PDF/ZIP
    dashboard       # ✅ Corrigé: plus de double prefix
)
from api.routers import enterprise  # Import direct du routeur enterprise

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    logger.info("🚀 Démarrage de l'API Cleaning...")
    
    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Base de données initialisée")
    
    yield
    
    # Shutdown
    logger.info("🛑 Arrêt de l'API Cleaning...")

def create_app() -> FastAPI:
    """Factory pour créer l'application FastAPI"""
    
    app = FastAPI(
        title="API Nettoyage Micro-Crèche",
        description="""
        API moderne pour la gestion du nettoyage d'une micro-crèche.
        
        🔑 **Authentification simplifiée :**
        - Compte Firebase = automatiquement Gérant
        - Accès complet à toutes les fonctionnalités
        - Gestion des employés intégrée
        
        🎯 **Concept :**
        1. Le gérant se connecte avec son compte Firebase
        2. Il peut gérer rooms, tasks, et ses employés
        3. Sélection d'employé via interface pour les sessions
        4. Reconnexion obligatoire pour revenir en mode gérant
        """,
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # ===== MIDDLEWARE DE SÉCURITÉ =====
    
    # CORS - Configuration permissive pour le développement
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted hosts
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts_list
        )
    
    # ===== ROUTES D'AUTHENTIFICATION =====
    # ✅ CORRIGÉ: auth.router n'a plus de tags, on les gère ici
    app.include_router(
        auth.router, 
        prefix="/auth", 
        tags=["🔐 Authentification"]
    )
    
    # ===== GESTION DES EMPLOYÉS =====
    app.include_router(
        performers.router, 
        prefix="/performers", 
        tags=["👥 Employés"]
    )
    
    # ===== GESTION DES RESSOURCES =====
    app.include_router(
        rooms.router, 
        prefix="/rooms", 
        tags=["🏠 Pièces"]
    )
    
    app.include_router(
        tasks.router, 
        prefix="/tasks", 
        tags=["✅ Tâches modèles"]
    )
    
    app.include_router(
        tasks.assigned_router,
        prefix="/assigned-tasks",
        tags=["📋 Tâches assignées"]
    )
    
    # ===== SESSIONS DE NETTOYAGE =====
    app.include_router(
        sessions.router, 
        prefix="/sessions", 
        tags=["🧹 Sessions"]
    )
    
    # ===== LOGS ET EXPORTS =====
    app.include_router(
        logs.router, 
        prefix="/logs", 
        tags=["📝 Logs de tâches"]
    )
    
    app.include_router(
        exports.router, 
        prefix="/exports", 
        tags=["📊 Exports"]
    )

    # ===== TABLEAU DE BORD =====
    # ✅ CORRIGÉ: dashboard.router n'a plus de tags, on les gère ici
    app.include_router(
        dashboard.router, 
        prefix="/dashboard", 
        tags=["📈 Dashboard"]
    )
    
    # ===== GESTION DES ENTREPRISES =====
    app.include_router(
        enterprise.router,
        prefix="/enterprise",
        tags=["🏢 Entreprises"]
    )
    
    # ===== ROUTES DE BASE =====
    
    @app.get("/", tags=["🏠 Accueil"])
    async def root():
        """Page d'accueil de l'API"""
        return {
            "message": "API Nettoyage Micro-Crèche",
            "version": "2.0.0",
            "status": "✅ Opérationnelle",
            "features": {
                "authentication": "Firebase auto-création",
                "user_role": "GERANTE par défaut",
                "performer_management": "Intégré",
                "routing": "✅ Préfixes corrigés"
            },
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "auth_login": "/auth/login",
                "auth_me": "/auth/me",
                "dashboard": "/dashboard",
                "performers": "/performers/",
                "sessions_today": "/sessions/today"
            }
        }
    
    @app.get("/health", tags=["🏥 Santé"])
    async def health_check():
        """Vérification de l'état de l'API"""
        try:
            # Test de connexion à la base de données
            from api.core.database import SessionLocal
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            
            return {
                "status": "healthy",
                "database": "✅ Connected",
                "routes": "✅ Fixed (no more double prefixes)",
                "timestamp": "2024-08-19T12:00:00Z"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": f"❌ Error: {str(e)}",
                "timestamp": "2024-08-19T12:00:00Z"
            }
    
    return app

# Créer l'instance de l'application
app = create_app()

# Point d'entrée pour uvicorn
if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Lancement de l'API en mode développement")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
