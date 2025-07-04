#!/bin/bash

# 🏗️ Script de création de l'architecture modulaire
# API Nettoyage Micro-Crèche - Structure modulaire et scalable

set -e

echo "🏗️ Création de l'architecture modulaire FastAPI"
echo "=============================================="

# Demander le répertoire de destination
read -p "📁 Répertoire de destination (défaut: cleaning-backend-modular): " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-cleaning-backend-modular}

# Créer le répertoire principal
echo "📂 Création du répertoire $PROJECT_NAME..."
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Créer la structure de répertoires
echo "📁 Création de la structure modulaire..."
mkdir -p {app/{core,models,schemas,routers,services,utils,tasks},uploads}

# Créer les fichiers __init__.py
echo "📄 Création des fichiers __init__.py..."
touch app/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/routers/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py
touch app/tasks/__init__.py
touch uploads/.gitkeep

# === FICHIER PRINCIPAL ===

echo "📄 Création du fichier principal..."

cat > app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine
from app.core.scheduler import scheduler, setup_scheduler
from app.models import Base
from app.routers import (
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
EOF

# === CORE ===

echo "📄 Création des fichiers core..."

cat > app/core/config.py << 'EOF'
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
EOF

cat > app/core/database.py << 'EOF'
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency pour obtenir une session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF

cat > app/core/security.py << 'EOF'
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# Initialisation Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.firebase_credentials_path)
    firebase_admin.initialize_app(cred)

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency pour obtenir l'utilisateur actuel authentifié"""
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        firebase_uid = decoded_token['uid']
        
        user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )
EOF

cat > app/core/scheduler.py << 'EOF'
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.tasks.background_tasks import generate_daily_sessions

scheduler = AsyncIOScheduler()

def setup_scheduler():
    """Configure les tâches planifiées"""
    scheduler.add_job(
        func=generate_daily_sessions,
        trigger=CronTrigger(hour=0, minute=0),
        id="generate_sessions",
        replace_existing=True
    )
EOF

# === MODELS ===

echo "📄 Création des modèles..."

cat > app/models/base.py << 'EOF'
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class BaseModel(Base):
    """Modèle de base avec des champs communs"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)

class TimestampedModel(BaseModel):
    """Modèle avec timestamps de création et modification"""
    __abstract__ = True
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
EOF

cat > app/models/__init__.py << 'EOF'
from app.core.database import Base
from app.models.user import User
from app.models.performer import Performer
from app.models.room import Room
from app.models.task import TaskTemplate, AssignedTask
from app.models.session import CleaningSession, CleaningLog
from app.models.export import Export

__all__ = [
    "Base", "User", "Performer", "Room", 
    "TaskTemplate", "AssignedTask", 
    "CleaningSession", "CleaningLog", "Export"
]
EOF

cat > app/models/user.py << 'EOF'
from sqlalchemy import Column, String, Enum
from enum import Enum as PyEnum
from app.models.base import TimestampedModel

class UserRole(PyEnum):
    GERANTE = "gerante"

class User(TimestampedModel):
    __tablename__ = "users"
    
    firebase_uid = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.GERANTE)
EOF

cat > app/models/performer.py << 'EOF'
from sqlalchemy import Column, String, Boolean
from app.models.base import BaseModel

class Performer(BaseModel):
    __tablename__ = "performers"
    
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
EOF

cat > app/models/room.py << 'EOF'
from sqlalchemy import Column, String, Text, Integer, Boolean
from app.models.base import BaseModel

class Room(BaseModel):
    __tablename__ = "rooms"
    
    name = Column(String, nullable=False)
    description = Column(Text)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
EOF

cat > app/models/task.py << 'EOF'
from sqlalchemy import Column, String, Text, Boolean, Integer, Time, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class TaskTemplate(BaseModel):
    __tablename__ = "task_templates"
    
    name = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

class AssignedTask(BaseModel):
    __tablename__ = "assigned_tasks"
    
    task_template_id = Column(UUID(as_uuid=True), ForeignKey("task_templates.id"))
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"))
    default_performer_id = Column(UUID(as_uuid=True), ForeignKey("performers.id"))
    frequency_days = Column(Integer, default=1)
    times_per_day = Column(Integer, default=1)
    suggested_time = Column(Time)
    is_active = Column(Boolean, default=True)
    
    task_template = relationship("TaskTemplate")
    room = relationship("Room")
    default_performer = relationship("Performer")
EOF

cat > app/models/session.py << 'EOF'
from sqlalchemy import Column, Date, Text, Enum, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime
from app.models.base import BaseModel, TimestampedModel

class SessionStatus(PyEnum):
    EN_COURS = "en_cours"
    COMPLETEE = "completee"
    INCOMPLETE = "incomplete"

class LogStatus(PyEnum):
    FAIT = "fait"
    PARTIEL = "partiel"
    REPORTE = "reporte"
    IMPOSSIBLE = "impossible"

class CleaningSession(TimestampedModel):
    __tablename__ = "cleaning_sessions"
    
    date = Column(Date, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.EN_COURS)
    notes = Column(Text)

class CleaningLog(BaseModel):
    __tablename__ = "cleaning_logs"
    
    session_id = Column(UUID(as_uuid=True), ForeignKey("cleaning_sessions.id"))
    assigned_task_id = Column(UUID(as_uuid=True), ForeignKey("assigned_tasks.id"))
    performer_id = Column(UUID(as_uuid=True), ForeignKey("performers.id"))
    status = Column(Enum(LogStatus), default=LogStatus.FAIT)
    notes = Column(Text)
    photos = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("CleaningSession")
    assigned_task = relationship("AssignedTask")
    performer = relationship("Performer")
EOF

cat > app/models/export.py << 'EOF'
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Export(BaseModel):
    __tablename__ = "exports"
    
    session_id = Column(UUID(as_uuid=True), ForeignKey("cleaning_sessions.id"))
    export_type = Column(String)  # "pdf" ou "zip"
    filename = Column(String)
    file_path = Column(String)
    
    session = relationship("CleaningSession")
EOF

# === SCHEMAS ===

echo "📄 Création des schémas..."

cat > app/schemas/__init__.py << 'EOF'
from app.schemas.user import UserCreate, UserResponse
from app.schemas.performer import PerformerCreate, PerformerResponse
from app.schemas.room import RoomCreate, RoomResponse
from app.schemas.task import TaskTemplateCreate, TaskTemplateResponse, AssignedTaskCreate, AssignedTaskResponse
from app.schemas.session import CleaningSessionResponse, CleaningLogCreate, CleaningLogResponse

__all__ = [
    "UserCreate", "UserResponse",
    "PerformerCreate", "PerformerResponse",
    "RoomCreate", "RoomResponse",
    "TaskTemplateCreate", "TaskTemplateResponse",
    "AssignedTaskCreate", "AssignedTaskResponse",
    "CleaningSessionResponse",
    "CleaningLogCreate", "CleaningLogResponse"
]
EOF

cat > app/schemas/user.py << 'EOF'
import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.user import UserRole

class UserCreate(BaseModel):
    firebase_uid: str
    full_name: str
    role: UserRole = UserRole.GERANTE

class UserResponse(BaseModel):
    id: uuid.UUID
    firebase_uid: str
    full_name: str
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True
EOF

cat > app/schemas/performer.py << 'EOF'
import uuid
from datetime import datetime
from pydantic import BaseModel

class PerformerCreate(BaseModel):
    name: str

class PerformerResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
EOF

cat > app/schemas/room.py << 'EOF'
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class RoomCreate(BaseModel):
    name: str
    description: Optional[str] = None
    display_order: int = 0

class RoomResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    display_order: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
EOF

cat > app/schemas/task.py << 'EOF'
import uuid
from datetime import datetime, time
from typing import Optional
from pydantic import BaseModel
from app.schemas.performer import PerformerResponse
from app.schemas.room import RoomResponse

class TaskTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TaskTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AssignedTaskCreate(BaseModel):
    task_template_id: uuid.UUID
    room_id: uuid.UUID
    default_performer_id: uuid.UUID
    frequency_days: int = 1
    times_per_day: int = 1
    suggested_time: Optional[time] = None

class AssignedTaskResponse(BaseModel):
    id: uuid.UUID
    task_template: TaskTemplateResponse
    room: RoomResponse
    default_performer: PerformerResponse
    frequency_days: int
    times_per_day: int
    suggested_time: Optional[time]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
EOF

cat > app/schemas/session.py << 'EOF'
import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel
from app.models.session import SessionStatus, LogStatus
from app.schemas.performer import PerformerResponse
from app.schemas.task import AssignedTaskResponse

class CleaningSessionResponse(BaseModel):
    id: uuid.UUID
    date: date
    status: SessionStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CleaningLogCreate(BaseModel):
    session_id: uuid.UUID
    assigned_task_id: uuid.UUID
    performer_id: uuid.UUID
    status: LogStatus = LogStatus.FAIT
    notes: Optional[str] = None

class CleaningLogResponse(BaseModel):
    id: uuid.UUID
    session: CleaningSessionResponse
    assigned_task: AssignedTaskResponse
    performer: PerformerResponse
    status: LogStatus
    notes: Optional[str]
    photos: Optional[List[str]]
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
EOF

# === ROUTERS ===

echo "📄 Création des routers..."

cat > app/routers/users.py << 'EOF'
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.post("", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.firebase_uid == user.firebase_uid).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Utilisateur déjà existant")
    
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
EOF

cat > app/routers/performers.py << 'EOF'
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.performer import Performer
from app.schemas.performer import PerformerCreate, PerformerResponse

router = APIRouter()

@router.post("", response_model=PerformerResponse)
async def create_performer(
    performer: PerformerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_performer = Performer(**performer.dict())
    db.add(db_performer)
    db.commit()
    db.refresh(db_performer)
    return db_performer

@router.get("", response_model=List[PerformerResponse])
async def get_performers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Performer).filter(Performer.is_active == True).all()
EOF

cat > app/routers/rooms.py << 'EOF'
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.room import Room
from app.schemas.room import RoomCreate, RoomResponse

router = APIRouter()

@router.post("", response_model=RoomResponse)
async def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_room = Room(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@router.get("", response_model=List[RoomResponse])
async def get_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Room).filter(Room.is_active == True).order_by(Room.display_order).all()
EOF

cat > app/routers/tasks.py << 'EOF'
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.task import TaskTemplate, AssignedTask
from app.schemas.task import TaskTemplateCreate, TaskTemplateResponse, AssignedTaskCreate, AssignedTaskResponse

router = APIRouter()
assigned_router = APIRouter()

# Task Templates
@router.post("", response_model=TaskTemplateResponse)
async def create_task_template(
    task: TaskTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_task = TaskTemplate(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("", response_model=List[TaskTemplateResponse])
async def get_task_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(TaskTemplate).filter(TaskTemplate.is_active == True).all()

# Assigned Tasks
@assigned_router.post("", response_model=AssignedTaskResponse)
async def create_assigned_task(
    task: AssignedTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_task = AssignedTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@assigned_router.get("", response_model=List[AssignedTaskResponse])
async def get_assigned_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(AssignedTask).filter(AssignedTask.is_active == True).all()
EOF

cat > app/routers/sessions.py << 'EOF'
import uuid
from typing import List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.session import CleaningSession, SessionStatus
from app.schemas.session import CleaningSessionResponse

router = APIRouter()

@router.get("", response_model=List[CleaningSessionResponse])
async def get_sessions(
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(CleaningSession).order_by(desc(CleaningSession.date)).limit(limit).all()

@router.get("/{session_id}", response_model=CleaningSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    return session

@router.get("/today", response_model=CleaningSessionResponse)
async def get_today_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    session = db.query(CleaningSession).filter(CleaningSession.date == today).first()
    
    if not session:
        session = CleaningSession(date=today)
        db.add(session)
        db.commit()
        db.refresh(session)
    
    return session

@router.patch("/{session_id}/status")
async def update_session_status(
    session_id: uuid.UUID,
    status: SessionStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    session.status = status
    session.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Statut mis à jour"}
EOF

cat > app/routers/logs.py << 'EOF'
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.session import CleaningLog
from app.schemas.session import CleaningLogCreate, CleaningLogResponse
from app.utils.file_utils import save_uploaded_file

router = APIRouter()

@router.post("", response_model=CleaningLogResponse)
async def create_cleaning_log(
    log: CleaningLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_log = CleaningLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@router.get("", response_model=List[CleaningLogResponse])
async def get_cleaning_logs(
    session_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(CleaningLog)
    if session_id:
        query = query.filter(CleaningLog.session_id == session_id)
    
    return query.order_by(desc(CleaningLog.timestamp)).all()

@router.post("/{log_id}/photos")
async def upload_photo(
    log_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = db.query(CleaningLog).filter(CleaningLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log non trouvé")
    
    filename = save_uploaded_file(file, log_id)
    
    photos = log.photos or []
    photos.append(filename)
    log.photos = photos
    db.commit()
    
    return {"message": "Photo uploadée", "filename": filename}
EOF

cat > app/routers/exports.py << 'EOF'
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.session import CleaningSession
from app.models.export import Export
from app.services.export_service import generate_pdf_report_task, generate_zip_photos_task
import os

router = APIRouter()

@router.post("/pdf/{session_id}")
async def generate_pdf_report(
    session_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    background_tasks.add_task(generate_pdf_report_task, session_id)
    return {"message": "Génération du PDF en cours"}

@router.post("/zip/{session_id}")
async def generate_zip_photos(
    session_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    background_tasks.add_task(generate_zip_photos_task, session_id)
    return {"message": "Génération du ZIP en cours"}

@router.get("/{export_id}/download")
async def download_export(
    export_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    export = db.query(Export).filter(Export.id == export_id).first()
    if not export:
        raise HTTPException(status_code=404, detail="Export non trouvé")
    
    if not os.path.exists(export.file_path):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    return FileResponse(
        path=export.file_path,
        filename=export.filename,
        media_type='application/octet-stream'
    )
EOF

# === SERVICES ===

echo "📄 Création des services..."

cat > app/services/export_service.py << 'EOF'
import uuid
import zipfile
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.session import CleaningSession, CleaningLog
from app.models.export import Export

def generate_pdf_report_task(session_id: uuid.UUID):
    """Génère un rapport PDF pour une session"""
    db = SessionLocal()
    try:
        from weasyprint import HTML
        from jinja2 import Template
        
        session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
        logs = db.query(CleaningLog).filter(CleaningLog.session_id == session_id).all()
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Rapport de Nettoyage</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; margin-bottom: 30px; }
                .task { margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; }
                .status { font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Rapport de Nettoyage</h1>
                <h2>{{ session.date.strftime('%d %B %Y') }}</h2>
            </div>
            {% for log in logs %}
            <div class="task">
                <h3>{{ log.assigned_task.task_template.name }}</h3>
                <p><strong>Pièce:</strong> {{ log.assigned_task.room.name }}</p>
                <p><strong>Exécutant:</strong> {{ log.performer.name }}</p>
                <p><strong>Statut:</strong> <span class="status">{{ log.status.value }}</span></p>
                {% if log.notes %}
                <p><strong>Notes:</strong> {{ log.notes }}</p>
                {% endif %}
                <p><strong>Heure:</strong> {{ log.timestamp.strftime('%H:%M') }}</p>
            </div>
            {% endfor %}
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(session=session, logs=logs)
        
        date_str = session.date.strftime('%d_%B_%Y')
        filename = f"rapport_nettoyage_{date_str}.pdf"
        file_path = settings.uploads_dir / filename
        
        HTML(string=html_content).write_pdf(file_path)
        
        export = Export(
            session_id=session_id,
            export_type="pdf",
            filename=filename,
            file_path=str(file_path)
        )
        db.add(export)
        db.commit()
        
        print(f"PDF généré: {filename}")
        
    except Exception as e:
        print(f"Erreur génération PDF: {e}")
    finally:
        db.close()

def generate_zip_photos_task(session_id: uuid.UUID):
    """Génère un ZIP avec toutes les photos d'une session"""
    db = SessionLocal()
    try:
        session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
        logs = db.query(CleaningLog).filter(
            CleaningLog.session_id == session_id, 
            CleaningLog.photos.isnot(None)
        ).all()
        
        date_str = session.date.strftime('%d_%B_%Y')
        filename = f"photos_{date_str}.zip"
        file_path = settings.uploads_dir / filename
        
        with zipfile.ZipFile(file_path, 'w') as zipf:
            for log in logs:
                if log.photos:
                    for photo in log.photos:
                        photo_path = settings.uploads_dir / photo
                        if photo_path.exists():
                            zipf.write(photo_path, photo)
        
        export = Export(
            session_id=session_id,
            export_type="zip",
            filename=filename,
            file_path=str(file_path)
        )
        db.add(export)
        db.commit()
        
        print(f"ZIP généré: {filename}")
        
    except Exception as e:
        print(f"Erreur génération ZIP: {e}")
    finally:
        db.close()
EOF

cat > app/services/session_service.py << 'EOF'
from datetime import date
from sqlalchemy.orm import Session
from app.models.session import CleaningSession

def get_or_create_today_session(db: Session) -> CleaningSession:
    """Récupère ou crée la session du jour"""
    today = date.today()
    session = db.query(CleaningSession).filter(CleaningSession.date == today).first()
    
    if not session:
        session = CleaningSession(date=today)
        db.add(session)
        db.commit()
        db.refresh(session)
    
    return session
EOF

# === UTILS ===

echo "📄 Création des utilitaires..."

cat > app/utils/file_utils.py << 'EOF'
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings

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
EOF

# === TASKS ===

echo "📄 Création des tâches en arrière-plan..."

cat > app/tasks/background_tasks.py << 'EOF'
from datetime import date
from app.core.database import SessionLocal
from app.models.session import CleaningSession

async def generate_daily_sessions():
    """Génère automatiquement les sessions de nettoyage quotidiennes"""
    db = SessionLocal()
    try:
        today = date.today()
        
        existing_session = db.query(CleaningSession).filter(
            CleaningSession.date == today
        ).first()
        
        if not existing_session:
            session = CleaningSession(date=today)
            db.add(session)
            db.commit()
            print(f"Session créée pour {today}")
            
    except Exception as e:
        print(f"Erreur lors de la génération de session: {e}")
    finally:
        db.close()
EOF

# === FICHIERS DE CONFIGURATION ===

echo "📄 Création des fichiers de configuration..."

# requirements.txt avec pydantic-settings
cat > requirements.txt << 'EOF'
# FastAPI et serveur
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Base de données
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9

# Configuration avec Pydantic v2
pydantic-settings==2.0.3

# Authentification Firebase
firebase-admin==6.2.0

# Export PDF
weasyprint==60.2
jinja2==3.1.2

# Scheduler
apscheduler==3.10.4

# Utilitaires
pillow==10.1.0
aiofiles==23.2.0

# Tests (optionnel)
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Développement
black==23.11.0
flake8==6.1.0
EOF

# .env.example
cat > .env.example << 'EOF'
# Base de données
DATABASE_URL=postgresql://user:password@localhost:5432/cleaning_db

# Firebase
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# Environnement
ENVIRONMENT=development
DEBUG=true

# Uploads
UPLOADS_DIR=./uploads
MAX_FILE_SIZE=10485760

# Security
SECRET_KEY=your-secret-key-here
EOF

# run.py - Point d'entrée alternatif
cat > run.py << 'EOF'
#!/usr/bin/env python3
"""
Point d'entrée pour l'application
Usage: python run.py
"""

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
EOF

# README pour l'architecture modulaire
cat > README_ARCHITECTURE.md << 'EOF'
# 🏗️ Architecture Modulaire - API Nettoyage

## 📁 Structure du projet

```
app/
├── __init__.py
├── main.py                 # Point d'entrée FastAPI
├── core/                   # Configuration et services core
│   ├── config.py          # Configuration Pydantic Settings
│   ├── database.py        # Configuration SQLAlchemy
│   ├── security.py        # Authentification Firebase
│   └── scheduler.py       # APScheduler
├── models/                 # Modèles SQLAlchemy
│   ├── base.py           # Modèles de base
│   ├── user.py           # Modèle User
│   ├── performer.py      # Modèle Performer
│   ├── room.py           # Modèle Room
│   ├── task.py           # Modèles Task*
│   ├── session.py        # Modèles Session/Log
│   └── export.py         # Modèle Export
├── schemas/               # Schémas Pydantic
│   ├── user.py
│   ├── performer.py
│   ├── room.py
│   ├── task.py
│   ├── session.py
│   └── export.py
├── routers/               # Routes FastAPI
│   ├── users.py
│   ├── performers.py
│   ├── rooms.py
│   ├── tasks.py
│   ├── sessions.py
│   ├── logs.py
│   └── exports.py
├── services/              # Logique métier
│   ├── export_service.py
│   └── session_service.py
├── utils/                 # Utilitaires
│   └── file_utils.py
└── tasks/                 # Tâches background
    └── background_tasks.py
```

## 🚀 Avantages de cette architecture

✅ **Séparation des responsabilités** - Chaque module a un rôle précis
✅ **Facilité de maintenance** - Code organisé et lisible
✅ **Scalabilité** - Facile d'ajouter de nouvelles fonctionnalités
✅ **Testabilité** - Tests unitaires par module
✅ **Réutilisabilité** - Services et utilitaires réutilisables

## 🔧 Comment démarrer

1. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurer l'environnement**
   ```bash
   cp .env.example .env
   # Éditer .env avec vos configurations
   ```

3. **Démarrer l'application**
   ```bash
   # Avec uvicorn directement
   uvicorn app.main:app --reload
   
   # Ou avec le script run.py
   python run.py
   ```

## 📝 Ajout de nouvelles fonctionnalités

### Nouveau modèle
1. Créer `app/models/nouveau_modele.py`
2. Ajouter le modèle dans `app/models/__init__.py`
3. Créer les schémas dans `app/schemas/nouveau_modele.py`
4. Créer le router dans `app/routers/nouveau_modele.py`
5. Inclure le router dans `app/main.py`

### Nouveau service
1. Créer `app/services/nouveau_service.py`
2. Importer dans les routers qui en ont besoin

### Nouvelle route
1. Ajouter dans le router approprié
2. Ou créer un nouveau router si nécessaire

## 🧪 Tests

```bash
pytest tests/
```

## 📚 Documentation API

Une fois l'application démarrée :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
EOF

echo ""
echo "✅ Architecture modulaire créée avec succès !"
echo ""
echo "📁 Projet créé dans : $(pwd)"
echo ""
echo "📋 Structure créée :"
echo "   🏗️ Architecture modulaire complète"
echo "   📦 Séparation des responsabilités"
echo "   🔧 Configuration Pydantic Settings"
echo "   📄 Documentation README_ARCHITECTURE.md"
echo ""
echo "🚀 Pour démarrer :"
echo "1. cd $PROJECT_NAME"
echo "2. pip install -r requirements.txt"
echo "3. cp .env.example .env"
echo "4. Configurer Firebase et PostgreSQL"
echo "5. python run.py"
echo ""
echo "🎯 Architecture prête pour la production !"
