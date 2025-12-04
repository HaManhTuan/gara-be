from datetime import timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.settings import settings
from app.models.user import User
from app.schemas.common import ResponseBuilder, SuccessResponse
from app.schemas.firebase_auth import FirebaseTokenVerifyRequest, FirebaseTokenVerifyResponse
from app.schemas.users import (
    UserProfileResponse,
    UserRegistrationRequest,
    UserUpdateRequest,
    convert_user_registration_to_internal,
    convert_user_update_request_to_internal,
)
from app.services.firebase_service import firebase_service
from app.services.user_service import user_service
from app.utils.auth import create_access_token, get_current_user
from app.utils.i18n import __
from app.utils.tracing import get_trace_logger

# Public router for authentication endpoints that don't require auth
public_router = APIRouter()
# Protected router for endpoints that require authentication
protected_router = APIRouter()

logger = get_trace_logger("auth-controller")


@public_router.post("/token")  # type: ignore[misc]
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[Dict[str, str]]:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # The logger already has the request ID from our middleware

    # Authenticate user
    user = await user_service.authenticate_user(db=db, username=form_data.username, password=form_data.password)

    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=__("auth.login_failed"),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=__("auth.login_inactive_user"),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    logger.info(f"User {form_data.username} logged in successfully")

    return ResponseBuilder.success(
        message=__("auth.login_success"), data={"access_token": access_token, "token_type": "bearer"}
    )


@public_router.post("/register", response_model=SuccessResponse[Dict[str, str]])  # type: ignore[misc]
async def register(
    user_data: UserRegistrationRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[Dict[str, str]]:
    """
    Register a new user
    """
    logger.info(f"User registration attempt: {user_data.username}")

    # Convert request schema to internal schema
    internal_user_data = convert_user_registration_to_internal(user_data)

    # Create user
    user = await user_service.create_user(
        db=db,
        user_data=internal_user_data,
    )

    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    logger.info(f"User {user_data.username} registered successfully")

    return ResponseBuilder.success(
        message=__("auth.register_success"), data={"access_token": access_token, "token_type": "bearer"}
    )


@public_router.post(
    "/verify-token", response_model=SuccessResponse[FirebaseTokenVerifyResponse]
)  # type: ignore[misc]
async def verify_firebase_token(
    request: FirebaseTokenVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[FirebaseTokenVerifyResponse]:
    """
    Verify Firebase ID token and return JWT access token

    This endpoint:
    1. Verifies the Firebase ID token
    2. Gets or creates a user in the system based on Firebase user data
    3. Returns a JWT access token for API authentication

    Use this for mobile apps that authenticate with Firebase
    """
    logger.info("Firebase token verification attempt")

    # Verify Firebase token
    firebase_user = await firebase_service.verify_firebase_token(request.firebase_token)

    # Get or create user from Firebase data
    user, is_new_user = await user_service.get_or_create_firebase_user(
        db=db,
        firebase_uid=firebase_user["uid"],
        email=firebase_user.get("email"),
        phone_number=firebase_user.get("phone_number"),
        name=firebase_user.get("name"),
        picture=firebase_user.get("picture"),
    )

    # Create JWT access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    logger.info(
        f"Firebase token verified successfully. User: {user.email or user.phone_number}, "
        f"{'Registered' if is_new_user else 'Logged in'}"
    )

    response_data = FirebaseTokenVerifyResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        full_name=user.full_name,
        is_new_user=is_new_user,
    )

    message = __("auth.register_success") if is_new_user else __("auth.login_success")

    return ResponseBuilder.success(message=message, data=response_data)


@protected_router.get("/profile", response_model=SuccessResponse[UserProfileResponse])  # type: ignore[misc]
async def get_user_profile(
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[UserProfileResponse]:
    """
    Get current user profile
    """
    logger.info(f"User {current_user.username} requested profile")

    user_profile = UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        deleted_at=current_user.deleted_at,
    )

    return ResponseBuilder.success(message=__("auth.profile_retrieved"), data=user_profile)


@protected_router.put("/profile", response_model=SuccessResponse[UserProfileResponse])  # type: ignore[misc]
async def update_user_profile(
    user_update: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserProfileResponse]:
    """
    Update user profile with optimistic locking
    """
    logger.info(f"User {current_user.username} updating profile")

    # Convert request schema to internal schema
    internal_update_data = convert_user_update_request_to_internal(user_update)

    # Use optimistic locking for the update
    updated_user = await user_service.update_user_with_optimistic_lock(
        db=db,
        user_id=current_user.id,
        update_data=internal_update_data.dict(exclude_unset=True),
        expected_updated_at=internal_update_data.updated_at,
    )

    logger.info(f"User {current_user.username} profile updated successfully")

    user_profile = UserProfileResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        is_superuser=updated_user.is_superuser,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
        deleted_at=updated_user.deleted_at,
    )

    return ResponseBuilder.success(
        message=__("auth.profile_updated"),
        data=user_profile,
    )
