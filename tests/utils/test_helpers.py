"""
Utility functions for testing.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.user import User
from app.repositories.concrete.user_repository import user_repository


async def create_test_user(
    db: AsyncSession,
    email: str = "test@example.com",
    password: str = "password123",
    username: str = None,
    is_admin: bool = False,
    deleted_at: Optional[datetime] = None,
) -> User:
    """
    Create a test user in the database.
    """
    # Generate username from email if not provided
    if username is None:
        username = email.split("@")[0]

    # Check if user already exists using direct query to ensure tables exist
    try:
        result = await db.execute(select(User).filter(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            return existing_user
    except Exception as e:
        # If there's an error, log it and continue to create a new user
        print(f"Error checking for existing user: {str(e)}")
        # This likely means the table doesn't exist yet

    # Create a new user
    # The User constructor expects username, email, password, full_name, is_superuser
    user = User(
        username=username,
        email=email,
        password=password,  # The model will hash it
        is_superuser=is_admin,
    )
    # Set deleted_at if provided (for testing soft-deleted users)
    if deleted_at is not None:
        user.deleted_at = deleted_at

    db.add(user)
    await db.commit()

    return user


def create_test_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a test JWT token for a user.
    """
    # For backward compatibility, we'll use a default username
    # This function should be used with create_test_token_for_user instead
    username = f"testuser_{user_id}"

    to_encode = {"sub": username}

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return encoded_jwt


def create_test_token_for_user(user, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a test JWT token for a user object.
    """
    to_encode = {"sub": user.username}

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return encoded_jwt


def get_auth_headers(token: str) -> Dict[str, str]:
    """
    Create authorization headers with the given token.
    """
    return {"Authorization": f"Bearer {token}"}
