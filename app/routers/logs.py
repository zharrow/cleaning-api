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
