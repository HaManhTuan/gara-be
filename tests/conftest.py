"""
Test configuration and fixtures for the FastAPI application.
"""
import asyncio
import os
from typing import AsyncGenerator, Dict, Generator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

# Set the environment to test
os.environ["APP_ENV"] = "test"

# Import after setting APP_ENV
from app.config.database import Base, engine, get_db
from app.models.user import User
from main import app as application

# Import all models to ensure they're registered with SQLAlchemy metadata
from tests.models.test_models import *  # This is critical for table creation

# Create session factory using the shared engine
TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for tests.
    Uses the tables created by setup_test_db.
    """
    # Create session using the existing database with tables already created
    async with TestingSessionLocal() as session:
        try:
            yield session
        except Exception:
            # Roll back in case of error
            await session.rollback()
            raise
        finally:
            # Close the session
            await session.close()


@pytest.fixture
def event_loop() -> Generator:
    """
    Create an instance of the default event loop for each test case.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Return the test database instead of the production database.
    """
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture
def app() -> FastAPI:
    """
    Create a fresh app instance for testing.
    """
    # Replace the production database dependency with the test database
    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Setup function that runs once before all tests.
    Creates tables and prepares the test database.
    This replaces the need for Alembic migrations in the test environment.
    """
    # Import all models to ensure they're properly registered with Base.metadata
    # The models are already imported via test_models.py

    # Import any other models here
    # Log that we're setting up the test database
    print("\nSetting up test database and creating all tables...")

    # Create all tables at the beginning of the test session
    async with engine.begin() as conn:
        # Drop all tables first to ensure a clean state
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables based on the imported models
        await conn.run_sync(Base.metadata.create_all)
        print(f"Created tables: {', '.join(Base.metadata.tables.keys())}")

    yield

    # Clean up after all tests are done
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(app: FastAPI) -> Generator:
    """
    Create a test client for the app.
    """
    # Using TestClient for synchronous testing
    with TestClient(app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def async_client(app: FastAPI) -> AsyncGenerator:
    """
    Create an async test client for the app.
    """
    # Using httpx.AsyncClient for async testing
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ===== AUTHENTICATION FIXTURES =====

@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """
    Create a test user for authentication.
    """
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> Dict[str, str]:
    """
    Create authentication headers for API requests.
    """
    import jwt
    from datetime import datetime, timedelta
    from app.config.settings import settings

    token_data = {"sub": test_user.username}
    to_encode = token_data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def authenticated_client(client: TestClient, auth_headers: Dict[str, str]) -> TestClient:
    """
    Create a test client with authentication headers pre-configured.
    """
    # Set default headers for all requests
    client.headers.update(auth_headers)
    return client
