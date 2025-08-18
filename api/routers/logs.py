import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.core.config import settings
from api.models.user import User
from api.models.session import CleaningLog, CleaningSession, LogStatus, SessionStatus
from api.schemas.session import CleaningLogCreate, CleaningLogResponse
from api.utils.file_utils import save_uploaded_file
from api.models import Base
from api.models import CleaningLog
from api.models import User
from api.models import Performer
from api.models import Room
from api.models import TaskTemplate, AssignedTask

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

@router.post("/{log_id}/complete", response_model=CleaningLogResponse)
async def complete_task(
    log_id: uuid.UUID,
    performed_by_id: uuid.UUID,
    status: LogStatus = LogStatus.FAIT,
    note: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marque une tâche comme complétée avec les détails de réalisation."""
    
    log = db.query(CleaningLog).filter(CleaningLog.id == log_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Log non trouvé")
    
    from api.models.performer import Performer
    performer = db.query(Performer).filter(Performer.id == performed_by_id).first()
    
    if not performer:
        raise HTTPException(status_code=404, detail="Exécutant non trouvé")
    
    log.performed_by_id = performed_by_id
    log.status = status
    log.performed_at = datetime.utcnow()
    log.recorded_by_id = current_user.id
    
    if note:
        log.note = note
    
    db.commit()
    
    session = db.query(CleaningSession).filter(
        CleaningSession.id == log.session_id
    ).first()
    
    all_logs = db.query(CleaningLog).filter(
        CleaningLog.session_id == session.id
    ).all()
    
    completed_count = len([l for l in all_logs if l.status == LogStatus.FAIT])
    impossible_count = len([l for l in all_logs if l.status == LogStatus.IMPOSSIBLE])
    postponed_count = len([l for l in all_logs if l.status == LogStatus.REPORTE])
    
    if completed_count + impossible_count == len(all_logs):
        session.status = SessionStatus.COMPLETEE
    elif postponed_count == len(all_logs):
        session.status = SessionStatus.EN_COURS
    else:
        session.status = SessionStatus.INCOMPLETE
    
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(log)
    
    return log

@router.post("/{log_id}/quick-complete", response_model=CleaningLogResponse)
async def quick_complete_task(
    log_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validation rapide d'une tâche avec l'exécutant par défaut."""
    
    log = db.query(CleaningLog).filter(CleaningLog.id == log_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Log non trouvé")
    
    task = db.query(AssignedTask).filter(
        AssignedTask.id == log.assigned_task_id
    ).first()
    
    if not task or not task.default_performer_id:
        raise HTTPException(
            status_code=400,
            detail="Pas d'exécutant par défaut pour cette tâche"
        )
    
    log.performed_by_id = task.default_performer_id
    log.status = LogStatus.FAIT
    log.performed_at = datetime.utcnow()
    log.recorded_by_id = current_user.id
    
    db.commit()
    db.refresh(log)
    
    return log