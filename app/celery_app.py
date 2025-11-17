"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "soccer_analytics",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.scraping_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Celery Beat Schedule (Periodic Tasks)
celery_app.conf.beat_schedule = {
    "scrape-player-stats-daily": {
        "task": "app.tasks.scraping_tasks.scrape_player_statistics",
        "schedule": crontab(hour=2, minute=0),  # Run daily at 2:00 AM
    },
    "update-player-ratings-weekly": {
        "task": "app.tasks.scraping_tasks.update_player_ratings",
        "schedule": crontab(day_of_week=1, hour=3, minute=0),  # Run weekly on Monday at 3:00 AM
    },
    "cleanup-old-data-monthly": {
        "task": "app.tasks.scraping_tasks.cleanup_old_data",
        "schedule": crontab(day_of_month=1, hour=4, minute=0),  # Run monthly on the 1st at 4:00 AM
    },
}


@celery_app.task(bind=True)
def debug_task(self) -> dict:
    """
    Debug task for testing Celery configuration.

    Returns:
        Dict with task request information
    """
    return {
        "task_id": self.request.id,
        "task_name": self.request.task,
        "args": self.request.args,
        "kwargs": self.request.kwargs,
    }
