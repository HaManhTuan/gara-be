"""
User internal schemas.

This module contains schemas used internally within the application
for user-related operations.
"""

from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field

from app.schemas.common.base_schema import BaseSchema


class UserBase(BaseSchema):
    """Base schema for user data used internally"""

    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None  # Optional for phone-only auth
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    phone_verified: bool = False
    is_superuser: bool = False


class UserCreate(UserBase):
    """Schema for user creation used internally in the application"""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseSchema):
    """Schema for user update used internally in the application"""

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    updated_at: Optional[str] = Field(None, description="Required for optimistic locking")


class UserInDB(UserBase):
    """Schema for user data in database"""

    id: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
