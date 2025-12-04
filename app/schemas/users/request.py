"""
User request and response schemas.

This module contains schemas for API requests and responses
for user-related operations.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import EmailStr, Field, field_validator

from app.schemas.common.base_schema import BaseSchema

# ===== REQUEST SCHEMAS (Data In) =====


class UserRegistrationRequest(BaseSchema):
    """Schema for user registration request from API"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserCreateRequest(BaseSchema):
    """Schema for user creation request from API"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    password_confirm: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    is_superuser: bool = False

    @field_validator("password_confirm")  # type: ignore[misc]
    @classmethod
    def passwords_match(cls, v: str, info: Any) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class UserUpdateRequest(BaseSchema):
    """Schema for user update request from API"""

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    updated_at: Optional[str] = Field(None, description="Required for optimistic locking")


# ===== RESPONSE SCHEMAS (Data Out) =====


class UserResponse(BaseSchema):
    """Schema for user response to API clients"""

    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_superuser: bool = False
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class UserProfileResponse(BaseSchema):
    """Schema for user profile response (includes sensitive fields)"""

    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_superuser: bool = False
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
