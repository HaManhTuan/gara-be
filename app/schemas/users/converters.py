"""
User schema conversion utilities.

This module provides functions to convert between user request schemas (API input)
and internal schemas (application logic).
"""

from app.schemas.users.request import UserCreateRequest, UserRegistrationRequest, UserUpdateRequest
from app.schemas.users.schema import UserCreate, UserUpdate


def convert_user_registration_to_internal(request: UserRegistrationRequest) -> UserCreate:
    """Convert user registration request to internal user creation schema"""
    return UserCreate(
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=None,
        is_superuser=False,
    )


def convert_user_create_request_to_internal(request: UserCreateRequest) -> UserCreate:
    """Convert user creation request to internal user creation schema"""
    return UserCreate(
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        is_superuser=request.is_superuser,
    )


def convert_user_update_request_to_internal(request: UserUpdateRequest) -> UserUpdate:
    """Convert user update request to internal user update schema"""
    return UserUpdate(
        username=request.username,
        email=request.email,
        full_name=request.full_name,
        updated_at=request.updated_at,
    )
