"""
Celery worker configuration
Handles asynchronous job execution for builds and simulations
"""
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app with Redis backend
celery_app = Celery(
    "a6hub_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.workers.tasks']
)

# Celery configuration optimized for long-running build tasks
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # Timezone
    timezone='UTC',
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_acks_late=True,  # Acknowledge task after completion, not before
    task_reject_on_worker_lost=True,

    # Time limits
    task_time_limit=settings.MAX_JOB_DURATION_SECONDS,
    task_soft_time_limit=settings.MAX_JOB_DURATION_SECONDS - 60,

    # Worker configuration
    worker_prefetch_multiplier=1,  # Don't prefetch tasks
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    worker_disable_rate_limits=False,

    # Result backend
    result_backend_transport_options={
        'retry_policy': {
            'timeout': 5.0
        }
    },
    result_expires=3600 * 24,  # Results expire after 24 hours

    # Redis connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # Task routing
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
)

# Task routing - separate queues for different job types
celery_app.conf.task_routes = {
    'app.workers.tasks.run_simulation': {
        'queue': 'simulation',
        'routing_key': 'simulation.run',
    },
    'app.workers.tasks.run_build': {
        'queue': 'build',
        'routing_key': 'build.run',
    },
    'app.workers.tasks.run_python_script': {
        'queue': 'python',
        'routing_key': 'python.run',
    },
}

# Configure queue priorities (build jobs have higher priority)
celery_app.conf.task_queue_max_priority = 10
celery_app.conf.task_default_priority = 5


# Task event handlers for logging
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """Log when a task starts"""
    logger.info(f"Task {task.name} [{task_id}] starting with args={args}, kwargs={kwargs}")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kw):
    """Log when a task completes"""
    logger.info(f"Task {task.name} [{task_id}] completed with state={state}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **kw):
    """Log when a task fails"""
    logger.error(f"Task {sender.name} [{task_id}] failed with exception: {exception}")
    logger.error(f"Traceback: {traceback}")
