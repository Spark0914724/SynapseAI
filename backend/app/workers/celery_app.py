from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "synapseai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.document_tasks",
        "app.workers.tasks.email_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        # Monthly token reset — runs at midnight on the 1st of each month
        "reset-monthly-tokens": {
            "task": "app.workers.tasks.billing_tasks.reset_monthly_tokens",
            "schedule": 3600.0,  # placeholder; use crontab in production
        },
    },
)
