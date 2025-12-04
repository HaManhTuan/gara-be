from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.settings import settings
from app.exceptions import InactiveUserException, TokenExpiredException, TokenInvalidException
from app.models.user import User
from app.services.user_service import user_service
from app.utils.i18n import __
from app.utils.request_context import get_current_user_data
from app.utils.tracing import get_trace_logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
logger = get_trace_logger("auth")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time delta

    Returns:
        JWT token as string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return str(encoded_jwt)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token

    Args:
        token: JWT token

    Returns:
        Decoded token payload
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload  # type: ignore[no-any-return]
    except jwt.ExpiredSignatureError as e:
        logger.debug(f"Token expired: {str(e)}")
        raise TokenExpiredException(__("auth.token_expired"))
    except jwt.exceptions.InvalidTokenError as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise TokenInvalidException(__("auth.token_invalid"))


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """
    Verify token and return current user.

    This function first checks if user data is available in the request context
    (set by AuthMiddleware). If available, it uses that data to fetch the user
    from the database. Otherwise, it falls back to decoding the token directly.

    Args:
        token: JWT token (used as fallback if no context data)
        db: Database session

    Returns:
        Current user data

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Fallback mapping for invalid auth scenario
    credentials_exception = TokenInvalidException(__("auth.token_invalid"))

    try:
        # First, try to get user data from request context (set by AuthMiddleware)
        user_data = get_current_user_data()

        if user_data:
            # Use data from context (already validated by middleware)
            username: Optional[str] = user_data.get("sub")
            logger.debug("Using user data from request context")
        else:
            # Fallback: decode token directly (for backward compatibility)
            payload = decode_token(token)
            username = payload.get("sub")
            logger.debug("Decoding token directly (no context data available)")

        if username is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception

        # Fetch user from database
        user = await user_service.get_by_username(db, username=username)

        if user is None:
            logger.warning(f"User from token not found: {username}")
            raise credentials_exception

        return user

    except (TokenExpiredException, TokenInvalidException):
        # Re-raise known auth exceptions for middleware handling
        raise


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Verify that current user is active

    Args:
        current_user: Current user object

    Returns:
        Current active user object
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempt: {current_user.username}")
        raise InactiveUserException(__("auth.login_inactive_user"))

    return current_user
