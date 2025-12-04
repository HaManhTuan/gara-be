"""
Script to start Celery worker with gevent pool.

This script runs a Celery worker that processes background tasks using gevent pool
for better IO performance.

Usage:
    poetry run python scripts/start_worker.py
    poetry run python scripts/start_worker.py --concurrency=200
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))  # noqa: E402

from app.utils.logger import get_logger  # noqa: E402
from app.workers.celery_app import celery_app  # noqa: E402

logger = get_logger("celery_worker")

if __name__ == "__main__":
    # Parse command line arguments for concurrency
    concurrency = 200  # Default concurrency for IO-intensive tasks
    if "--concurrency" in sys.argv:
        idx = sys.argv.index("--concurrency")
        concurrency = int(sys.argv[idx + 1])
        sys.argv.pop(idx)
        sys.argv.pop(idx)

    logger.info(
        f"Starting Celery worker with gevent pool (concurrency: {concurrency})"
    )

    # Start worker with gevent pool
    sys.argv = [
        "celery",
        "worker",
        "--pool=gevent",
        f"--concurrency={concurrency}",
        "--loglevel=info",
    ]
    celery_app.worker_main(sys.argv)
