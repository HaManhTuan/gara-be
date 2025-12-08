"""Email OTP controller for handling email OTP endpoints"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.email_otp import (
    EmailResponse,
    SendOTPRequest,
    SendOTPResponse,
    SendPasswordResetRequest,
    SendWelcomeEmailRequest,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from app.services.email_service import email_service
from app.utils.logger import get_logger

logger = get_logger("email-otp-controller")

router = APIRouter(prefix="/email", tags=["Email & OTP"])


@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Send OTP to email",
    description="Send a one-time password (OTP) to the specified email address"
)
async def send_otp(request: SendOTPRequest) -> SendOTPResponse:
    """
    Send OTP to email address
    
    Args:
        request: SendOTPRequest with email and optional expiry_minutes
        
    Returns:
        SendOTPResponse with status and OTP (in debug mode)
        
    Raises:
        HTTPException: If email sending fails
    """
    try:
        logger.info(f"Sending OTP to email: {request.email}")
        
        result = await email_service.send_otp_email(
            to_email=request.email,
            expiry_minutes=request.expiry_minutes
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        return SendOTPResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {str(e)}"
        )


@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP",
    description="Verify the OTP code sent to an email address"
)
async def verify_otp(request: VerifyOTPRequest) -> VerifyOTPResponse:
    """
    Verify OTP code
    
    Args:
        request: VerifyOTPRequest with email and otp
        
    Returns:
        VerifyOTPResponse with verification status
    """
    try:
        logger.info(f"Verifying OTP for email: {request.email}")
        
        is_valid = await email_service.verify_otp(request.email, request.otp)
        
        if is_valid:
            return VerifyOTPResponse(
                success=True,
                message="OTP verified successfully"
            )
        else:
            return VerifyOTPResponse(
                success=False,
                message="Invalid or expired OTP"
            )
            
    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        return VerifyOTPResponse(
            success=False,
            message=f"Error verifying OTP: {str(e)}"
        )


@router.post(
    "/send-welcome",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send welcome email",
    description="Send a welcome email to a new user"
)
async def send_welcome_email(request: SendWelcomeEmailRequest) -> EmailResponse:
    """
    Send welcome email
    
    Args:
        request: SendWelcomeEmailRequest with email and name
        
    Returns:
        EmailResponse with status
        
    Raises:
        HTTPException: If email sending fails
    """
    try:
        logger.info(f"Sending welcome email to: {request.email}")
        
        success = await email_service.send_welcome_email(
            to_email=request.email,
            name=request.name
        )
        
        if success:
            return EmailResponse(
                success=True,
                message="Welcome email sent successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send welcome email"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send welcome email: {str(e)}"
        )


@router.post(
    "/send-password-reset",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send password reset email",
    description="Send a password reset link to an email address"
)
async def send_password_reset(request: SendPasswordResetRequest) -> EmailResponse:
    """
    Send password reset email
    
    Args:
        request: SendPasswordResetRequest with email, reset_token, and reset_url
        
    Returns:
        EmailResponse with status
        
    Raises:
        HTTPException: If email sending fails
    """
    try:
        logger.info(f"Sending password reset email to: {request.email}")
        
        success = await email_service.send_password_reset_email(
            to_email=request.email,
            reset_token=request.reset_token,
            reset_url=request.reset_url
        )
        
        if success:
            return EmailResponse(
                success=True,
                message="Password reset email sent successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send password reset email: {str(e)}"
        )
