import os

from celery import Celery
from workers.tracing import setup_tracing, instrument_celery, instrument_redis, instrument_logging, TracedTask

# Configure Celery
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery(
    "promoai_rag",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["workers.tasks.parse", "workers.tasks.chunk", "workers.tasks.embed"],
)

# Setup OpenTelemetry tracing
setup_tracing()
instrument_celery()
instrument_redis()
instrument_logging()

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
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_cls=TracedTask,  # Use traced task class
)


def create_celery_app() -> Celery:
    """Create and return Celery app instance."""
    return celery_app
