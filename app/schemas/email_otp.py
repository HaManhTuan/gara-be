"""Email OTP schemas for request and response validation"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class EmailLoginRequest(BaseModel):
    """Request schema for initiating email OTP login"""
    
    email: EmailStr = Field(..., description="Email address to send OTP to")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com"
                }
            ]
        }
    }


class EmailLoginResponse(BaseModel):
    """Response schema for email OTP login initiation"""
    
    success: bool = Field(..., description="Whether OTP was sent successfully")
    message: str = Field(..., description="Status message")
    email: EmailStr = Field(..., description="Email address OTP was sent to")
    expiry_minutes: int = Field(..., description="OTP expiry time in minutes")
    otp: Optional[str] = Field(None, description="OTP code (only in debug mode)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "OTP sent successfully",
                    "email": "user@example.com",
                    "expiry_minutes": 5,
                    "otp": "123456"
                }
            ]
        }
    }


class VerifyOTPLoginRequest(BaseModel):
    """Request schema for verifying OTP and completing login"""
    
    email: EmailStr = Field(..., description="Email address associated with OTP")
    otp: str = Field(
        ...,
        min_length=4,
        max_length=8,
        description="OTP code to verify"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "otp": "123456"
                }
            ]
        }
    }


class VerifyOTPLoginResponse(BaseModel):
    """Response schema for OTP verification and login"""
    
    success: bool = Field(..., description="Whether login was successful")
    message: str = Field(..., description="Login status message")
    access_token: Optional[str] = Field(None, description="JWT access token")
    token_type: Optional[str] = Field(None, description="Token type (bearer)")
    user_id: Optional[str] = Field(None, description="User ID")
    email: Optional[EmailStr] = Field(None, description="User email")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Login successful",
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "user_id": "123",
                    "email": "user@example.com"
                }
            ]
        }
    }


class SendOTPRequest(BaseModel):
    """Request schema for sending OTP to email"""
    
    email: EmailStr = Field(..., description="Email address to send OTP to")
    expiry_minutes: Optional[int] = Field(
        None,
        ge=1,
        le=60,
        description="OTP expiry time in minutes (1-60). Uses default if not provided"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "expiry_minutes": 5
                }
            ]
        }
    }


class SendOTPResponse(BaseModel):
    """Response schema for OTP sending"""
    
    success: bool = Field(..., description="Whether OTP was sent successfully")
    message: str = Field(..., description="Status message")
    otp: Optional[str] = Field(None, description="OTP code (only in debug mode)")
    expiry_minutes: Optional[int] = Field(None, description="OTP expiry time in minutes")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "OTP sent successfully",
                    "otp": "123456",
                    "expiry_minutes": 5
                }
            ]
        }
    }


class VerifyOTPRequest(BaseModel):
    """Request schema for verifying OTP"""
    
    email: EmailStr = Field(..., description="Email address associated with OTP")
    otp: str = Field(
        ...,
        min_length=4,
        max_length=8,
        description="OTP code to verify"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "otp": "123456"
                }
            ]
        }
    }


class VerifyOTPResponse(BaseModel):
    """Response schema for OTP verification"""
    
    success: bool = Field(..., description="Whether OTP verification was successful")
    message: str = Field(..., description="Verification status message")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "OTP verified successfully"
                },
                {
                    "success": False,
                    "message": "Invalid or expired OTP"
                }
            ]
        }
    }


class SendWelcomeEmailRequest(BaseModel):
    """Request schema for sending welcome email"""
    
    email: EmailStr = Field(..., description="Email address to send welcome email to")
    name: str = Field(..., min_length=1, max_length=255, description="User's name")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "name": "John Doe"
                }
            ]
        }
    }


class SendPasswordResetRequest(BaseModel):
    """Request schema for sending password reset email"""
    
    email: EmailStr = Field(..., description="Email address to send password reset link to")
    reset_token: str = Field(..., description="Password reset token")
    reset_url: str = Field(..., description="Password reset URL")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "reset_token": "abc123def456",
                    "reset_url": "https://example.com/reset-password?token=abc123def456"
                }
            ]
        }
    }


class EmailResponse(BaseModel):
    """Generic response schema for email operations"""
    
    success: bool = Field(..., description="Whether email was sent successfully")
    message: str = Field(..., description="Status message")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Email sent successfully"
                },
                {
                    "success": False,
                    "message": "Failed to send email"
                }
            ]
        }
    }
