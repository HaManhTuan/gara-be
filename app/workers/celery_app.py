from celery import Celery

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("celery")

# Configure Celery app
celery_app = Celery(
    "app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

# Configure Celery settings
# Note: Worker pool type is specified via command line: --pool=gevent
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_hijack_root_logger=False,
    task_send_sent_event=True,
    # Gevent pool configuration for IO-intensive tasks
    # Note: Worker pool type is specified via command line: --pool=gevent
    # Performance tuning for IO tasks
    worker_prefetch_multiplier=1,  # One task at a time for better distribution
    task_acks_late=True,  # Ack after completion for better reliability
    worker_max_tasks_per_child=1000,  # Restart after N tasks to prevent memory leaks
    worker_max_memory_per_child=200000,  # Restart if >200MB (in KB)
)


# Initialize Celery app
def initialize_celery() -> Celery:
    logger.info("Initializing Celery app")
    return celery_app
