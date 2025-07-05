from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.core.config import settings
from api.core.database import engine
from api.core.scheduler import scheduler, setup_scheduler
from api.models import Base
from api.routers import (
    users, performers, rooms, tasks, 
    sessions, logs, exports
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    scheduler.start()
    setup_scheduler()
    yield
    # Shutdown
    scheduler.shutdown()

def create_app() -> FastAPI:
    """Factory pour créer l'application FastAPI"""
    app = FastAPI(
        title="API Nettoyage Micro-Crèche",
        description="API pour la gestion du nettoyage d'une micro-crèche",
        version="1.0.0",
        lifespan=lifespan
    )

    # Middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inclure les routers
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(performers.router, prefix="/performers", tags=["performers"])
    app.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
    app.include_router(tasks.router, prefix="/task-templates", tags=["task-templates"])
    app.include_router(tasks.assigned_router, prefix="/assigned-tasks", tags=["assigned-tasks"])
    app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
    app.include_router(logs.router, prefix="/cleaning-logs", tags=["cleaning-logs"])
    app.include_router(exports.router, prefix="/exports", tags=["exports"])

    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
