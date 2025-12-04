"""Schemas for Firebase authentication"""

from typing import Optional

from pydantic import BaseModel, Field


class FirebaseTokenVerifyRequest(BaseModel):
    """Request schema for Firebase token verification"""

    firebase_token: str = Field(..., description="Firebase ID token from client")

    class Config:
        json_schema_extra = {
            "example": {
                "firebase_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlOW...",
            }
        }


class FirebaseTokenVerifyResponse(BaseModel):
    """Response schema for Firebase token verification"""

    access_token: str = Field(..., description="JWT access token for API authentication")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: int = Field(..., description="User ID in the system")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="User email (nullable for phone auth)")
    phone_number: Optional[str] = Field(None, description="User phone number")
    full_name: Optional[str] = Field(None, description="User full name")
    is_new_user: bool = Field(..., description="Whether this is a newly registered user")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": 123,
                "username": "user_0912345678",
                "email": None,
                "phone_number": "+84912345678",
                "full_name": "John Doe",
                "is_new_user": False,
            }
        }
