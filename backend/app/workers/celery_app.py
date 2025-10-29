"""
Celery worker configuration
Handles asynchronous job execution for builds and simulations
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "a6hub_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.workers.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.MAX_JOB_DURATION_SECONDS,
    task_soft_time_limit=settings.MAX_JOB_DURATION_SECONDS - 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Task routing (optional - for multiple queues)
celery_app.conf.task_routes = {
    'app.workers.tasks.run_simulation': {'queue': 'simulation'},
    'app.workers.tasks.run_build': {'queue': 'build'},
}
