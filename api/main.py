from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from api.core.config import settings
from api.core.database import engine
from api.core.scheduler import scheduler, setup_scheduler
from api.core.middlewares import (
    RequestIDMiddleware,
    TimingMiddleware,
    LoggingMiddleware,
    ErrorHandlingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    DatabaseTransactionMiddleware
)
from api.core.logging_config import setup_logging
from api.models import Base
from api.routers import (
    auth, users, performers, rooms, tasks, 
    sessions, logs, exports
)

# Configuration du logging
setup_logging(settings.environment)
logger = logging.getLogger(__name__)

# Créer le dossier logs s'il n'existe pas
Path("logs").mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    logger.info("🚀 Démarrage de l'application")
    
    # Startup
    try:
        scheduler.start()
        setup_scheduler()
        logger.info("✅ Scheduler démarré")
    except Exception as e:
        logger.error(f"❌ Erreur démarrage scheduler: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Arrêt de l'application")
    try:
        scheduler.shutdown()
        logger.info("✅ Scheduler arrêté")
    except Exception as e:
        logger.error(f"❌ Erreur arrêt scheduler: {e}")

def create_app() -> FastAPI:
    """Factory pour créer l'application FastAPI"""
    
    # Configuration personnalisée de la documentation
    app = FastAPI(
        title="API Nettoyage Micro-Crèche",
        description="""
        ## 🧼 API de gestion du nettoyage pour micro-crèche
        
        Cette API permet de gérer :
        - 👥 Les utilisateurs et exécutants
        - 🏠 Les pièces à nettoyer
        - 📋 Les tâches de nettoyage
        - 📅 Les sessions quotidiennes
        - 📸 Les logs avec photos
        - 📄 Les exports PDF/ZIP
        
        ### 🔒 Authentification
        
        L'API utilise Firebase pour l'authentification. 
        Utilisez le endpoint `/auth/login` avec un token Firebase pour vous connecter.
        
        ### 📚 Documentation
        
        - **Swagger UI** : [/docs](/docs)
        - **ReDoc** : [/redoc](/redoc)
        """,
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {"name": "authentication", "description": "🔐 Authentification et gestion des utilisateurs"},
            {"name": "users", "description": "👤 Gestion des profils utilisateurs"},
            {"name": "performers", "description": "👥 Gestion des exécutants"},
            {"name": "rooms", "description": "🏠 Gestion des pièces"},
            {"name": "task-templates", "description": "📋 Modèles de tâches"},
            {"name": "assigned-tasks", "description": "✅ Tâches assignées"},
            {"name": "sessions", "description": "📅 Sessions de nettoyage"},
            {"name": "cleaning-logs", "description": "📝 Logs de nettoyage"},
            {"name": "exports", "description": "📄 Exports PDF/ZIP"},
            {"name": "health", "description": "🏥 État de santé de l'API"}
        ]
    )

    # === MIDDLEWARES ===
    # L'ordre est important : du plus externe au plus interne
    
    # 1. Trusted Host (sécurité)
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts  # À ajouter dans config
        )
    
    # 2. CORS (doit être avant les autres pour les preflight requests)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins if hasattr(settings, 'cors_origins') else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"]
    )
    
    # 3. GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 4. Security Headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 5. Rate Limiting
    if settings.environment == "production":
        app.add_middleware(
            RateLimitMiddleware,
            calls=100,  # 100 requêtes
            period=60   # par minute
        )
    
    # 6. Request ID (doit être tôt pour tracer toute la requête)
    app.add_middleware(RequestIDMiddleware)
    
    # 7. Database Transaction
    app.add_middleware(DatabaseTransactionMiddleware)
    
    # 8. Error Handling
    app.add_middleware(ErrorHandlingMiddleware)
    
    # 9. Timing
    app.add_middleware(TimingMiddleware)
    
    # 10. Logging (doit être le plus interne pour capturer tout)
    app.add_middleware(LoggingMiddleware)

    # === EXCEPTION HANDLERS ===
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Gestion des erreurs de validation Pydantic"""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "message": "Les données fournies sont invalides",
                "details": exc.errors(),
                "request_id": getattr(request.state, "request_id", "unknown")
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Gestion des exceptions HTTP"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "request_id": getattr(request.state, "request_id", "unknown")
            }
        )

    # === ROUTES ===
    
    # Auth routes (nouvelles)
    app.include_router(auth.router)
    
    # Routes existantes
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(performers.router, prefix="/performers", tags=["performers"])
    app.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
    app.include_router(tasks.router, prefix="/task-templates", tags=["task-templates"])
    app.include_router(tasks.assigned_router, prefix="/assigned-tasks", tags=["assigned-tasks"])
    app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
    app.include_router(logs.router, prefix="/cleaning-logs", tags=["cleaning-logs"])
    app.include_router(exports.router, prefix="/exports", tags=["exports"])

    # === HEALTH & MONITORING ===
    
    @app.get("/health", tags=["health"], summary="Health Check basique")
    async def health_check():
        """Vérification rapide de l'état de l'API"""
        return {
            "status": "healthy",
            "service": "cleaning-api",
            "version": app.version
        }
    
    @app.get("/health/detailed", tags=["health"], summary="Health Check détaillé")
    async def detailed_health_check(request: Request):
        """Vérification détaillée de l'état de l'API et ses dépendances"""
        health_status = {
            "status": "healthy",
            "service": "cleaning-api",
            "version": app.version,
            "environment": settings.environment,
            "request_id": getattr(request.state, "request_id", "unknown"),
            "checks": {}
        }
        
        # Vérifier la base de données
        try:
            from api.core.database import SessionLocal
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            health_status["checks"]["database"] = {
                "status": "healthy",
                "message": "Connexion à la base de données OK"
            }
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "message": f"Erreur base de données: {str(e)}"
            }
        
        # Vérifier Firebase
        try:
            import firebase_admin
            if firebase_admin._apps:
                health_status["checks"]["firebase"] = {
                    "status": "healthy",
                    "message": "Firebase initialisé"
                }
            else:
                health_status["checks"]["firebase"] = {
                    "status": "warning",
                    "message": "Firebase non initialisé"
                }
        except Exception as e:
            health_status["checks"]["firebase"] = {
                "status": "unhealthy",
                "message": f"Erreur Firebase: {str(e)}"
            }
        
        # Vérifier le scheduler
        try:
            if scheduler.running:
                jobs_count = len(scheduler.get_jobs())
                health_status["checks"]["scheduler"] = {
                    "status": "healthy",
                    "message": f"Scheduler actif avec {jobs_count} job(s)"
                }
            else:
                health_status["checks"]["scheduler"] = {
                    "status": "warning",
                    "message": "Scheduler non actif"
                }
        except Exception as e:
            health_status["checks"]["scheduler"] = {
                "status": "unhealthy",
                "message": f"Erreur scheduler: {str(e)}"
            }
        
        # Vérifier l'espace disque pour les uploads
        try:
            import shutil
            usage = shutil.disk_usage(settings.uploads_dir)
            free_gb = usage.free / (1024**3)
            health_status["checks"]["storage"] = {
                "status": "healthy" if free_gb > 1 else "warning",
                "message": f"{free_gb:.1f} GB libres",
                "free_bytes": usage.free,
                "total_bytes": usage.total
            }
        except Exception as e:
            health_status["checks"]["storage"] = {
                "status": "unknown",
                "message": f"Impossible de vérifier l'espace disque: {str(e)}"
            }
        
        # Status global
        if any(check["status"] == "unhealthy" for check in health_status["checks"].values()):
            health_status["status"] = "unhealthy"
        elif any(check["status"] == "warning" for check in health_status["checks"].values()):
            health_status["status"] = "degraded"
        
        return health_status
    
    @app.get("/", include_in_schema=False)
    async def root():
        """Redirection vers la documentation"""
        return {
            "message": "API Nettoyage Micro-Crèche",
            "documentation": "/docs",
            "health": "/health"
        }

    return app

# Créer l'instance de l'application
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    # Configuration avancée d'uvicorn
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "access": {
                "format": '%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        },
    }
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=log_config,
        access_log=True,
        use_colors=True
    )