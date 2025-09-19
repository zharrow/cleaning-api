# api/routers/dashboard.py - CORRECTION DU DOUBLE PREFIX

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import date, datetime, timedelta
from typing import Dict, Any, List

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.user import User
from api.models.session import CleaningSession, CleaningLog, SessionStatus, LogStatus
from api.models.task import AssignedTask
from api.models.performer import Performer

# ✅ CORRIGÉ: Supprimer les tags ici car ils sont gérés dans main.py
router = APIRouter()

@router.get("")
async def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Récupère toutes les données pour le tableau de bord principal."""
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Session du jour
    today_session = db.query(CleaningSession).filter(
        CleaningSession.date == today
    ).first()
    
    today_stats = None
    if today_session:
        logs = db.query(CleaningLog).filter(
            CleaningLog.session_id == today_session.id
        ).all()
        
        today_stats = {
            "session_id": str(today_session.id),
            "status": today_session.status.value,
            "total_tasks": len(logs),
            "completed": len([l for l in logs if l.status == LogStatus.FAIT]),
            "pending": len([l for l in logs if l.status == LogStatus.REPORTE]),
            "completion_rate": 0
        }
        
        if today_stats["total_tasks"] > 0:
            today_stats["completion_rate"] = round(
                (today_stats["completed"] / today_stats["total_tasks"]) * 100, 1
            )
    
    # Statistiques de la semaine
    week_sessions = db.query(CleaningSession).filter(
        CleaningSession.date >= week_ago
    ).all()
    
    week_stats = {
        "total_sessions": len(week_sessions),
        "completed_sessions": len([s for s in week_sessions if s.status == SessionStatus.COMPLETEE]),
        "total_tasks": 0,
        "completed_tasks": 0,
        "average_completion_rate": 0
    }
    
    completion_rates = []
    for session in week_sessions:
        logs = db.query(CleaningLog).filter(CleaningLog.session_id == session.id).all()
        week_stats["total_tasks"] += len(logs)
        completed = len([l for l in logs if l.status == LogStatus.FAIT])
        week_stats["completed_tasks"] += completed
        
        if logs:
            completion_rates.append((completed / len(logs)) * 100)
    
    if completion_rates:
        week_stats["average_completion_rate"] = round(
            sum(completion_rates) / len(completion_rates), 1
        )
    
    # Top performers du mois
    month_logs = db.query(CleaningLog).join(CleaningSession).filter(
        and_(
            CleaningSession.date >= month_ago,
            CleaningLog.status == LogStatus.FAIT
        )
    ).all()
    
    performer_counts = {}
    for log in month_logs:
        if log.performed_by_id:
            if log.performed_by_id not in performer_counts:
                performer_counts[log.performed_by_id] = 0
            performer_counts[log.performed_by_id] += 1
    
    top_performers = []
    for performer_id, count in sorted(
        performer_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]:
        performer = db.query(Performer).filter(Performer.id == performer_id).first()
        if performer:
            top_performers.append({
                "id": str(performer_id),
                "name": performer.name,
                "tasks_completed": count
            })
    
    # Tâches les plus reportées
    postponed_tasks = db.query(
        AssignedTask.id,
        AssignedTask.task_template_id,
        func.count(CleaningLog.id).label('postpone_count')
    ).join(
        CleaningLog,
        AssignedTask.id == CleaningLog.assigned_task_id
    ).join(
        CleaningSession,
        CleaningLog.session_id == CleaningSession.id
    ).filter(
        and_(
            CleaningSession.date >= week_ago,
            CleaningLog.status == LogStatus.REPORTE
        )
    ).group_by(
        AssignedTask.id,
        AssignedTask.task_template_id
    ).order_by(
        func.count(CleaningLog.id).desc()
    ).limit(5).all()
    
    from sqlalchemy.orm import joinedload
    
    most_postponed = []
    for task in postponed_tasks:
        assigned_task = db.query(AssignedTask).options(
            joinedload(AssignedTask.task_template),
            joinedload(AssignedTask.room)
        ).filter(AssignedTask.id == task.id).first()
        
        if assigned_task:
            most_postponed.append({
                "task_name": assigned_task.task_template.name,
                "room_name": assigned_task.room.name,
                "postpone_count": task.postpone_count
            })
    
    # Sessions récentes
    recent_sessions = []
    for session in db.query(CleaningSession).order_by(
        CleaningSession.date.desc()
    ).limit(7).all():
        logs = db.query(CleaningLog).filter(
            CleaningLog.session_id == session.id
        ).all()
        
        completed = len([l for l in logs if l.status == LogStatus.FAIT])
        total = len(logs)
        
        recent_sessions.append({
            "id": str(session.id),
            "date": session.date.isoformat(),
            "status": session.status.value,
            "completion_rate": round((completed / total * 100) if total > 0 else 0, 1),
            "tasks_count": total
        })
    
    return {
        "today": today_stats,
        "week_statistics": week_stats,
        "top_performers": top_performers,
        "most_postponed_tasks": most_postponed,
        "recent_sessions": recent_sessions,
        "last_updated": datetime.utcnow().isoformat()
    }

@router.get("/metrics")
async def get_metrics(
    period: str = Query("week", regex="^(day|week|month|year)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Récupère les métriques selon la période demandée."""
    
    today = date.today()
    
    if period == "day":
        start_date = today
    elif period == "week":
        start_date = today - timedelta(days=7)
    elif period == "month":
        start_date = today - timedelta(days=30)
    else:  # year
        start_date = today - timedelta(days=365)
    
    sessions = db.query(CleaningSession).filter(
        CleaningSession.date >= start_date
    ).all()
    
    daily_metrics = []
    for session in sessions:
        logs = db.query(CleaningLog).filter(
            CleaningLog.session_id == session.id
        ).all()
        
        completed = len([l for l in logs if l.status == LogStatus.FAIT])
        total = len(logs)
        
        daily_metrics.append({
            "date": session.date.isoformat(),
            "completed_tasks": completed,
            "total_tasks": total,
            "completion_rate": round((completed / total * 100) if total > 0 else 0, 1)
        })
    
    if daily_metrics:
        avg_completion = sum(m["completion_rate"] for m in daily_metrics) / len(daily_metrics)
        avg_tasks = sum(m["total_tasks"] for m in daily_metrics) / len(daily_metrics)
    else:
        avg_completion = 0
        avg_tasks = 0
    
    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": today.isoformat(),
        "daily_metrics": daily_metrics,
        "averages": {
            "completion_rate": round(avg_completion, 1),
            "tasks_per_day": round(avg_tasks, 1)
        }
    }
