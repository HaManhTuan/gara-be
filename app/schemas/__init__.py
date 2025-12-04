"""
Schemas package.

This package provides organized access to all application schemas.
"""

# Common schemas
from .common import (
    BaseSchema,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationMeta,
    ResponseBuilder,
    SuccessResponse,
)

# User schemas
from .users import (  # Internal schemas; Request/Response schemas; Converters
    UserBase,
    UserCreate,
    UserCreateRequest,
    UserInDB,
    UserProfileResponse,
    UserRegistrationRequest,
    UserResponse,
    UserUpdate,
    UserUpdateRequest,
    convert_user_create_request_to_internal,
    convert_user_registration_to_internal,
    convert_user_update_request_to_internal,
)

__all__ = [
    # Common
    "BaseSchema",
    "ErrorDetail",
    "ErrorResponse",
    "SuccessResponse",
    "PaginationMeta",
    "PaginatedResponse",
    "ResponseBuilder",
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserRegistrationRequest",
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserResponse",
    "UserProfileResponse",
    "convert_user_registration_to_internal",
    "convert_user_create_request_to_internal",
    "convert_user_update_request_to_internal",
]
