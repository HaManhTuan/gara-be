import os

from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from app.config.settings import settings
from app.jobs import scheduled_jobs  # Import scheduled job definitions
from app.utils.logger import get_logger

logger = get_logger("scheduler")

# Create job stores
jobstores = {"default": SQLAlchemyJobStore(url=str(settings.DATABASE_URL))}

# Create executors
executors = {"default": ThreadPoolExecutor(20), "processpool": ProcessPoolExecutor(5)}

# Job defaults
job_defaults = {"coalesce": False, "max_instances": 3, "misfire_grace_time": 60}

# Create scheduler
scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone="UTC")


def configure_jobs() -> None:
    """Configure and add scheduled jobs"""
    # Add scheduled jobs
    logger.info("Configuring scheduled jobs")

    # Daily cleanup task at midnight
    scheduler.add_job(
        scheduled_jobs.cleanup_old_data,
        "cron",
        hour=0,
        minute=0,
        id="cleanup_old_data",
        replace_existing=True,
        misfire_grace_time=60 * 60,  # 1 hour
    )

    # Hourly report generation
    scheduler.add_job(
        scheduled_jobs.generate_hourly_report,
        "interval",
        hours=1,
        id="generate_hourly_report",
        replace_existing=True,
    )

    # Check system health every 5 minutes
    scheduler.add_job(
        scheduled_jobs.check_system_health,
        "interval",
        minutes=5,
        id="check_system_health",
        replace_existing=True,
    )

    logger.info("Scheduled jobs configured")


def start_scheduler() -> None:
    """Start the scheduler"""
    # Skip starting scheduler in testing mode
    if os.environ.get("TESTING") == "1":
        logger.info("Testing environment detected, not starting scheduler")
        return

    try:
        # Configure jobs
        configure_jobs()

        # Start scheduler if not already running
        if not scheduler.running:
            scheduler.start()
            logger.info("Scheduler started successfully")
        else:
            logger.warning("Scheduler already running")

    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")


def stop_scheduler() -> None:
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
    else:
        logger.warning("Scheduler not running")
