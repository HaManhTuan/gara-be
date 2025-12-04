"""
User schemas package.

This package contains all user-related schemas including internal schemas,
request/response schemas, and conversion utilities.
"""

# Converters
from .converters import (
    convert_user_create_request_to_internal,
    convert_user_registration_to_internal,
    convert_user_update_request_to_internal,
)

# Request/Response schemas
from .request import UserCreateRequest, UserProfileResponse, UserRegistrationRequest, UserResponse, UserUpdateRequest

# Internal schemas
from .schema import UserBase, UserCreate, UserInDB, UserUpdate

__all__ = [
    # Internal schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    # Request/Response schemas
    "UserRegistrationRequest",
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserResponse",
    "UserProfileResponse",
    # Converters
    "convert_user_registration_to_internal",
    "convert_user_create_request_to_internal",
    "convert_user_update_request_to_internal",
]
