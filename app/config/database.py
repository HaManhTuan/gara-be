import os
from typing import Any, AsyncGenerator, Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config.settings import settings

# Create a Base class for declarative models
Base = declarative_base()


def get_database_url() -> str:
    """Get the appropriate database URL based on environment."""
    if os.getenv("APP_ENV") == "test":
        # Use SQLite for testing
        return "sqlite+aiosqlite:///file:mem_db?mode=memory&cache=shared&uri=true"
    else:
        # Use the configured database URL for production/development
        return str(settings.DATABASE_URL)


def get_async_database_url() -> str:
    """Get the async database URL by adding async driver."""
    base_url = get_database_url()
    if base_url.startswith("postgresql://"):
        return base_url.replace("postgresql://", "postgresql+asyncpg://")
    elif base_url.startswith("sqlite://"):
        return base_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif base_url.startswith("mysql://"):
        return base_url.replace("mysql://", "mysql+aiomysql://")
    else:
        # Already has async driver or unsupported
        return base_url


def get_sync_database_url() -> str:
    """Get the sync database URL by removing async driver."""
    base_url = get_database_url()
    if "+asyncpg" in base_url:
        return base_url.replace("postgresql+asyncpg://", "postgresql://")
    elif "+aiosqlite" in base_url:
        return base_url.replace("sqlite+aiosqlite://", "sqlite://")
    elif "+aiomysql" in base_url:
        return base_url.replace("mysql+aiomysql://", "mysql://")
    else:
        # Already sync or unsupported
        return base_url


# Create the SQLAlchemy async engine
async_engine = create_async_engine(
    get_async_database_url(),
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    # SQLite-specific settings for testing
    connect_args={"check_same_thread": False} if "sqlite" in get_async_database_url() else {},
)

# Create the SQLAlchemy sync engine for migrations
sync_engine = create_engine(
    get_sync_database_url(),
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    # SQLite-specific settings for testing
    connect_args={"check_same_thread": False} if "sqlite" in get_sync_database_url() else {},
)

# For backward compatibility, keep 'engine' as async
engine = async_engine


# Create an async SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession)

# Create a sync SessionLocal class for migrations
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


# Async context manager for database sessions
class AsyncDBSession:
    """Async context manager for database sessions."""

    def __init__(self) -> None:
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
        self.session = SessionLocal()
        return self.session

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.session:
            await self.session.close()


# Convenience function for async database operations
def get_async_db() -> AsyncDBSession:
    """Get an async database session context manager."""
    return AsyncDBSession()


# Async dependency to get DB session (for FastAPI dependency injection)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting database session."""
    async with AsyncDBSession() as session:
        yield session


# Sync context manager for database sessions
class SyncDBSession:
    """Context manager for sync database sessions."""

    def __init__(self) -> None:
        self.session: Optional[Session] = None

    def __enter__(self) -> Session:
        self.session = SyncSessionLocal()
        return self.session

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.session:
            self.session.close()


# Convenience function for sync database operations
def get_sync_db() -> SyncDBSession:
    """Get a sync database session context manager."""
    return SyncDBSession()
