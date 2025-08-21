# api/schemas/statistics.py - NOUVEAU FICHIER

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import date

class SessionStatistics(BaseModel):
    session_id: str
    date: str
    status: str
    total_tasks: int
    completed_tasks: int
    partial_tasks: int
    postponed_tasks: int
    impossible_tasks: int
    completion_rate: float
    average_duration_minutes: float
    stats_by_room: Dict[str, Dict[str, int]]
    top_performers: List[Dict[str, Any]]
    has_photos: bool
    notes_count: int

class DashboardToday(BaseModel):
    session_id: str
    status: str
    total_tasks: int
    completed: int
    pending: int
    completion_rate: float

class DashboardWeekStats(BaseModel):
    total_sessions: int
    completed_sessions: int
    total_tasks: int
    completed_tasks: int
    average_completion_rate: float

class DashboardPerformer(BaseModel):
    id: str
    name: str
    tasks_completed: int

class DashboardPostponedTask(BaseModel):
    task_name: str
    room_name: str
    postpone_count: int

class DashboardRecentSession(BaseModel):
    id: str
    date: str
    status: str
    completion_rate: float
    tasks_count: int

class DashboardData(BaseModel):
    today: Optional[DashboardToday]
    week_statistics: DashboardWeekStats
    top_performers: List[DashboardPerformer]
    most_postponed_tasks: List[DashboardPostponedTask]
    recent_sessions: List[DashboardRecentSession]
    last_updated: str

class MetricsPeriod(BaseModel):
    period: str
    start_date: str
    end_date: str
    daily_metrics: List[Dict[str, Any]]
    averages: Dict[str, float]

class TaskScheduleItem(BaseModel):
    task_id: str
    task_name: str
    room_name: str
    scheduled_time: str
    duration_minutes: int
    performer_name: Optional[str]
    frequency: Dict[str, Any]

class WorkloadDistribution(BaseModel):
    performer_id: str
    performer_name: str
    total_tasks: int
    total_duration_minutes: int
    average_tasks_per_day: float
    average_duration_per_day: float
    tasks_by_day: Dict[str, int]