from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from api.tasks.background_tasks import generate_daily_sessions

scheduler = AsyncIOScheduler()

def setup_scheduler():
    """Configure les tâches planifiées"""
    scheduler.add_job(
        func=generate_daily_sessions,
        trigger=CronTrigger(hour=0, minute=0),
        id="generate_sessions",
        replace_existing=True
    )
