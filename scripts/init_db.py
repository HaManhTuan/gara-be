"""
Database initialization script.

This script runs migrations and adds seed data if needed.
Run this script when setting up the application for the first time.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from alembic import command
from alembic.config import Config
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger("db_init")


def init_db() -> None:
    """Initialize the database structure and seed data"""
    logger.info("Running database migrations...")

    # Run migrations using alembic - migrations use sync SQLAlchemy
    alembic_cfg = Config(os.path.join(Path(__file__).parent.parent, "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations completed successfully")

    # For scripts, we can use sync SQLAlchemy with the same connection string
    # Get connection string from settings
    from app.config.settings import settings

    # Create sync engine and session for scripts
    sync_engine = create_engine(
        str(settings.DATABASE_URL),
        echo=settings.DB_ECHO,
    )
    SyncSession = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

    # Create a database session
    db = SyncSession()
    try:
        # Check if we have any users
        user_count = db.query(User).count()

        # Add admin user if no users exist
        if user_count == 0:
            logger.info("Creating admin user...")
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password="adminpassword",  # nosec B106 - Development default
                full_name="Administrator",
                is_superuser=True,
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"Admin user created with username: admin, ID: {admin_user.id}")

        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting database initialization")
    init_db()
    logger.info("Database initialization script completed")
