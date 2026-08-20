# CredFlow Backend - Celery App

import os
from celery import Celery
from celery.schedules import crontab
from kombu import Queue

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "credflow",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.worker.tasks.tally",
        "app.worker.tasks.notifications",
        "app.worker.tasks.payments",
        "app.worker.tasks.analytics",
    ],
)

# Configuration
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=100,
    result_expires=86400,  # 24 hours
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("tally", routing_key="tally"),
        Queue("sync", routing_key="sync"),
        Queue("notifications", routing_key="notifications"),
        Queue("payments", routing_key="payments"),
        Queue("analytics", routing_key="analytics"),
    ),
    task_routes={
        "app.worker.tasks.tally.*": {"queue": "tally"},
        "app.worker.tasks.notifications.*": {"queue": "notifications"},
        "app.worker.tasks.payments.*": {"queue": "payments"},
        "app.worker.tasks.analytics.*": {"queue": "analytics"},
    },
    beat_schedule={
        # Agent heartbeat check
        "check-agent-heartbeats": {
            "task": "app.worker.tasks.analytics.check_agent_heartbeats",
            "schedule": 900.0,  # Every 15 minutes
        },
        # Reminder engine
        "run-reminder-engine": {
            "task": "app.worker.tasks.notifications.run_reminder_engine",
            "schedule": 3600.0,  # Every hour
        },
        # Aging recalculation
        "recalculate-aging": {
            "task": "app.worker.tasks.analytics.recalculate_aging",
            "schedule": 3600.0,  # Every hour
        },
        # DSO calculation
        "calculate-dso": {
            "task": "app.worker.tasks.analytics.calculate_dso",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        # Cash flow forecast
        "forecast-cash-flow": {
            "task": "app.worker.tasks.analytics.forecast_cash_flow",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        },
        # Risk score update
        "update-risk-scores": {
            "task": "app.worker.tasks.analytics.update_risk_scores",
            "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM
        },
        # Daily reports
        "generate-daily-reports": {
            "task": "app.worker.tasks.analytics.generate_daily_reports",
            "schedule": crontab(hour=6, minute=0),  # Daily at 6 AM
        },
        # Expire old payment links
        "expire-payment-links": {
            "task": "app.worker.tasks.payments.expire_old_payment_links",
            "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
        },
        # Weekly tenant usage summary
        "tenant-usage-summary": {
            "task": "app.worker.tasks.analytics.tenant_usage_summary",
            "schedule": crontab(hour=8, minute=0, day_of_week=1),  # Monday 8 AM
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.worker.tasks"])


@celery_app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")