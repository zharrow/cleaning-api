from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc
import uuid

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.user import User
from api.models.session import CleaningSession, CleaningLog, SessionStatus, LogStatus
from api.models.task import AssignedTask
from api.schemas.session import CleaningSessionResponse
from api.services.task_scheduler import should_task_be_done_today, get_tasks_for_date
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload


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

@router.post("/today", response_model=CleaningSessionResponse)
async def create_today_session(
    force_recreate: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée ou récupère la session du jour avec toutes les tâches assignées.
    
    - **force_recreate**: Si True, recrée la session même si elle existe
    """
    today = date.today()
    
    # Vérifier si une session existe déjà
    existing_session = db.query(CleaningSession).filter(
        CleaningSession.date == today
    ).first()
    
    if existing_session and not force_recreate:
        return existing_session
    
    if existing_session and force_recreate:
        # Supprimer la session existante et ses logs
        db.delete(existing_session)
        db.commit()
    
    # Créer la nouvelle session
    session = CleaningSession(
        date=today,
        status=SessionStatus.EN_COURS
    )
    db.add(session)
    db.flush()  # Pour obtenir l'ID de la session
    
    # Récupérer toutes les tâches assignées actives
    assigned_tasks = db.query(AssignedTask).filter(
        AssignedTask.is_active == True
    ).all()
    
    # Créer les logs pour les tâches du jour
    logs_created = 0
    for task in assigned_tasks:
        # Vérifier si cette tâche doit être faite aujourd'hui
        if should_task_be_done_today(task, today):
            log = CleaningLog(
                session_id=session.id,
                assigned_task_id=task.id,
                performed_by_id=task.default_performer_id,
                recorded_by_id=current_user.id,
                status=LogStatus.REPORTE,  # Par défaut en attente
                performed_at=None
            )
            db.add(log)
            logs_created += 1
    
    db.commit()
    db.refresh(session)
    
    # Ajouter le nombre de logs créés à la réponse
    session.logs_count = logs_created
    
    return session

@router.get("/{session_id}/statistics")
async def get_session_statistics(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Récupère les statistiques détaillées d'une session.
    """
    session = db.query(CleaningSession).filter(
        CleaningSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    # Récupérer tous les logs avec les relations
    logs = db.query(CleaningLog).options(
        joinedload(CleaningLog.assigned_task).joinedload(AssignedTask.room),
        joinedload(CleaningLog.assigned_task).joinedload(AssignedTask.task_template),
        joinedload(CleaningLog.performed_by)
    ).filter(CleaningLog.session_id == session_id).all()
    
    # Calculer les statistiques
    total_tasks = len(logs)
    completed_tasks = len([l for l in logs if l.status == LogStatus.FAIT])
    partial_tasks = len([l for l in logs if l.status == LogStatus.PARTIEL])
    postponed_tasks = len([l for l in logs if l.status == LogStatus.REPORTE])
    impossible_tasks = len([l for l in logs if l.status == LogStatus.IMPOSSIBLE])
    
    # Statistiques par pièce
    stats_by_room = {}
    for log in logs:
        room_name = log.assigned_task.room.name
        if room_name not in stats_by_room:
            stats_by_room[room_name] = {
                "total": 0,
                "completed": 0,
                "partial": 0,
                "postponed": 0,
                "impossible": 0
            }
        
        stats_by_room[room_name]["total"] += 1
        
        if log.status == LogStatus.FAIT:
            stats_by_room[room_name]["completed"] += 1
        elif log.status == LogStatus.PARTIEL:
            stats_by_room[room_name]["partial"] += 1
        elif log.status == LogStatus.REPORTE:
            stats_by_room[room_name]["postponed"] += 1
        elif log.status == LogStatus.IMPOSSIBLE:
            stats_by_room[room_name]["impossible"] += 1
    
    # Top performers
    performer_stats = {}
    for log in logs:
        if log.performed_by_id and log.status in [LogStatus.FAIT, LogStatus.PARTIEL]:
            if log.performed_by_id not in performer_stats:
                performer_stats[log.performed_by_id] = {
                    "id": str(log.performed_by_id),
                    "name": log.performed_by.name if log.performed_by else "Inconnu",
                    "tasks_completed": 0,
                    "tasks_partial": 0,
                    "total_duration": 0
                }
            
            if log.status == LogStatus.FAIT:
                performer_stats[log.performed_by_id]["tasks_completed"] += 1
            else:
                performer_stats[log.performed_by_id]["tasks_partial"] += 1
            
            # Calculer la durée si disponible
            if log.performed_at and log.created_at:
                duration = (log.performed_at - log.created_at).total_seconds() / 60
                performer_stats[log.performed_by_id]["total_duration"] += duration
    
    top_performers = sorted(
        performer_stats.values(),
        key=lambda x: x["tasks_completed"],
        reverse=True
    )[:5]
    
    # Temps moyen par tâche
    durations = []
    for log in logs:
        if log.performed_at and log.created_at and log.status == LogStatus.FAIT:
            duration = (log.performed_at - log.created_at).total_seconds() / 60
            durations.append(duration)
    
    average_duration = sum(durations) / len(durations) if durations else 0
    
    return {
        "session_id": str(session_id),
        "date": session.date.isoformat(),
        "status": session.status.value,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "partial_tasks": partial_tasks,
        "postponed_tasks": postponed_tasks,
        "impossible_tasks": impossible_tasks,
        "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        "average_duration_minutes": round(average_duration, 1),
        "stats_by_room": stats_by_room,
        "top_performers": top_performers,
        "has_photos": any(log.photo_urls for log in logs),
        "notes_count": len([l for l in logs if l.note])
    }