import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.models.user import User
from api.models.session import CleaningSession
from api.models.export import Export
from api.services.export_service import generate_pdf_report_task, generate_zip_photos_task
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
