# api/services/task_scheduler.py - NOUVEAU FICHIER COMPLET

from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from api.models.task import AssignedTask
from api.models.session import CleaningSession, CleaningLog, LogStatus
import logging

logger = logging.getLogger(__name__)

def should_task_be_done_today(task: AssignedTask, check_date: date) -> bool:
    """Détermine si une tâche doit être effectuée à une date donnée selon sa fréquence."""
    if not task.is_active:
        return False
    
    frequency = task.frequency or {"type": "daily", "times_per_day": 1}
    freq_type = frequency.get("type", "daily")
    
    if freq_type == "daily":
        return True
    
    elif freq_type == "weekly":
        weekday = check_date.weekday()
        days = frequency.get("days", [])
        return weekday in days
    
    elif freq_type == "monthly":
        day_of_month = check_date.day
        days = frequency.get("days", [])
        return day_of_month in days
    
    elif freq_type == "occasional":
        return False
    
    logger.warning(f"Type de fréquence inconnu pour la tâche {task.id}: {freq_type}")
    return False

def get_tasks_for_date(db: Session, target_date: date) -> List[AssignedTask]:
    """Récupère toutes les tâches qui doivent être effectuées à une date donnée."""
    all_tasks = db.query(AssignedTask).filter(AssignedTask.is_active == True).all()
    
    tasks_for_date = []
    for task in all_tasks:
        if should_task_be_done_today(task, target_date):
            tasks_for_date.append(task)
    
    tasks_for_date.sort(key=lambda t: (t.room_id, t.order_in_room))
    return tasks_for_date

def get_suggested_schedule(db: Session, target_date: date) -> List[Dict[str, Any]]:
    """Génère un planning suggéré pour une journée."""
    tasks = get_tasks_for_date(db, target_date)
    schedule = []
    
    current_time = datetime.combine(target_date, datetime.min.time()).replace(hour=8, minute=0)
    
    for task in tasks:
        if task.suggested_time:
            scheduled_time = datetime.combine(target_date, task.suggested_time)
        else:
            scheduled_time = current_time
        
        duration = task.expected_duration or task.task_template.default_duration or 15
        
        schedule_item = {
            "task_id": str(task.id),
            "task_name": task.task_template.name,
            "room_name": task.room.name,
            "scheduled_time": scheduled_time.isoformat(),
            "duration_minutes": duration,
            "performer_name": task.default_performer.name if task.default_performer else None,
            "frequency": task.frequency
        }
        
        schedule.append(schedule_item)
        
        if not task.suggested_time:
            current_time = scheduled_time + timedelta(minutes=duration + 5)
    
    return schedule

def calculate_workload_distribution(db: Session, start_date: date, end_date: date) -> Dict[str, Any]:
    """Calcule la distribution de la charge de travail sur une période."""
    from api.models.performer import Performer
    
    distribution = {}
    current_date = start_date
    
    while current_date <= end_date:
        tasks = get_tasks_for_date(db, current_date)
        
        for task in tasks:
            if task.default_performer_id:
                performer_id = str(task.default_performer_id)
                
                if performer_id not in distribution:
                    performer = db.query(Performer).filter(
                        Performer.id == task.default_performer_id
                    ).first()
                    
                    distribution[performer_id] = {
                        "performer_name": performer.name if performer else "Inconnu",
                        "total_tasks": 0,
                        "total_duration_minutes": 0,
                        "tasks_by_day": {}
                    }
                
                distribution[performer_id]["total_tasks"] += 1
                duration = task.expected_duration or 15
                distribution[performer_id]["total_duration_minutes"] += duration
                
                day_key = current_date.isoformat()
                if day_key not in distribution[performer_id]["tasks_by_day"]:
                    distribution[performer_id]["tasks_by_day"][day_key] = 0
                distribution[performer_id]["tasks_by_day"][day_key] += 1
        
        current_date += timedelta(days=1)
    
    days_count = (end_date - start_date).days + 1
    
    for performer_id in distribution:
        dist = distribution[performer_id]
        dist["average_tasks_per_day"] = round(dist["total_tasks"] / days_count, 1)
        dist["average_duration_per_day"] = round(dist["total_duration_minutes"] / days_count, 1)
    
    return distribution

def get_overdue_tasks(db: Session) -> List[Dict[str, Any]]:
    """Récupère les tâches en retard (reportées sur plusieurs jours)."""
    week_ago = date.today() - timedelta(days=7)
    
    postponed_logs = db.query(CleaningLog).join(CleaningSession).filter(
        CleaningSession.date >= week_ago,
        CleaningLog.status == LogStatus.REPORTE
    ).all()
    
    task_postpone_count = {}
    
    for log in postponed_logs:
        task_id = str(log.assigned_task_id)
        if task_id not in task_postpone_count:
            task_postpone_count[task_id] = {
                "task_id": task_id,
                "postpone_count": 0,
                "dates": []
            }
        
        task_postpone_count[task_id]["postpone_count"] += 1
        task_postpone_count[task_id]["dates"].append(log.session.date.isoformat())
    
    overdue_tasks = []
    
    for task_id, info in task_postpone_count.items():
        if info["postpone_count"] >= 2:
            task = db.query(AssignedTask).filter(AssignedTask.id == task_id).first()
            
            if task:
                overdue_tasks.append({
                    "task_id": task_id,
                    "task_name": task.task_template.name,
                    "room_name": task.room.name,
                    "postpone_count": info["postpone_count"],
                    "postponed_dates": info["dates"],
                    "default_performer": task.default_performer.name if task.default_performer else None
                })
    
    overdue_tasks.sort(key=lambda x: x["postpone_count"], reverse=True)
    return overdue_tasks

def optimize_task_schedule(db: Session, target_date: date) -> List[Dict[str, Any]]:
    """Optimise le planning des tâches pour minimiser les déplacements."""
    tasks = get_tasks_for_date(db, target_date)
    
    tasks_by_room = {}
    for task in tasks:
        room_id = str(task.room_id)
        if room_id not in tasks_by_room:
            tasks_by_room[room_id] = []
        tasks_by_room[room_id].append(task)
    
    optimized_schedule = []
    current_time = datetime.combine(target_date, datetime.min.time()).replace(hour=8, minute=0)
    
    for room_id, room_tasks in tasks_by_room.items():
        room_tasks.sort(key=lambda t: t.order_in_room)
        
        for task in room_tasks:
            duration = task.expected_duration or 15
            
            optimized_schedule.append({
                "task_id": str(task.id),
                "task_name": task.task_template.name,
                "room_id": room_id,
                "room_name": task.room.name,
                "scheduled_time": current_time.isoformat(),
                "duration_minutes": duration,
                "performer_id": str(task.default_performer_id) if task.default_performer_id else None,
                "performer_name": task.default_performer.name if task.default_performer else None
            })
            
            current_time += timedelta(minutes=duration)
    
    return optimized_schedule

def estimate_session_duration(db: Session, target_date: date) -> Dict[str, Any]:
    """Estime la durée totale d'une session de nettoyage."""
    tasks = get_tasks_for_date(db, target_date)
    
    total_duration = 0
    task_count = len(tasks)
    
    for task in tasks:
        duration = task.expected_duration or task.task_template.default_duration or 15
        total_duration += duration
    
    transition_time = task_count * 5
    breaks_count = total_duration // 120
    break_time = breaks_count * 15
    
    total_with_breaks = total_duration + transition_time + break_time
    
    start_time = datetime.combine(target_date, datetime.min.time()).replace(hour=8, minute=0)
    end_time = start_time + timedelta(minutes=total_with_breaks)
    
    return {
        "date": target_date.isoformat(),
        "task_count": task_count,
        "total_task_duration_minutes": total_duration,
        "transition_time_minutes": transition_time,
        "break_time_minutes": break_time,
        "total_duration_minutes": total_with_breaks,
        "total_duration_hours": round(total_with_breaks / 60, 1),
        "suggested_start_time": start_time.time().isoformat(),
        "suggested_end_time": end_time.time().isoformat()
    }