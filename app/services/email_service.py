"""Email service for sending emails via SMTP"""

import random
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config.settings import settings
from app.utils.logger import get_logger
from app.utils.redis_client import redis_client

logger = get_logger("email-service")


class EmailService:
    """Service for sending emails with OTP and other notifications"""

    def __init__(self) -> None:
        """Initialize email service with SMTP configuration"""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.smtp_use_ssl = settings.SMTP_USE_SSL
        self.email_from = settings.EMAIL_FROM
        self.email_from_name = settings.EMAIL_FROM_NAME
        
        # Setup Jinja2 template environment
        self.template_env = Environment(
            loader=FileSystemLoader("app/templates/email"),
            autoescape=select_autoescape(["html", "xml"])
        )

    def generate_otp(self, length: int = 6) -> str:
        """
        Generate a random OTP code
        
        Args:
            length: Length of OTP code (default 6)
            
        Returns:
            OTP code as string
        """
        return "".join([str(random.randint(0, 9)) for _ in range(length)])

    def store_otp(self, email: str, otp: str, expiry_minutes: int = 5) -> None:
        """
        Store OTP with expiry time (temporary implementation)
    async def store_otp(self, email: str, otp: str, expiry_minutes: int = 5) -> bool:
        """
        Store OTP in Redis with expiry time
        
        Args:
            email: Email address
            otp: OTP code
            expiry_minutes: Expiry time in minutes
            
        Returns:
            True if OTP stored successfully
        """
        key = f"otp:{email}"
        expiry_seconds = expiry_minutes * 60
        
        success = await redis_client.set(key, otp, expiry_seconds)
        
    async def verify_otp(self, email: str, otp: str) -> bool:
        """
        Verify OTP code from Redis
        
        Args:
            email: Email address
            otp: OTP code to verify
            
        Returns:
            True if OTP is valid, False otherwise
        """
        key = f"otp:{email}"
        stored_otp = await redis_client.get(key)
        
        if not stored_otp:
            logger.warning(f"No OTP found in Redis for email: {email}")
            return False
            
        if stored_otp != otp:
            logger.warning(f"Invalid OTP for email: {email}")
            return False
            
        # OTP is valid, remove it from Redis
        await redis_client.delete(key)
        logger.info(f"OTP verified and deleted from Redis for email: {email}")
        return True
        # OTP is valid, remove it
        del self._otp_storage[email]
        logger.info(f"OTP verified successfully for email: {email}")
        return True

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of email
            text_content: Plain text content (optional)
            from_email: Sender email (optional, uses default)
            from_name: Sender name (optional, uses default)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{from_name or self.email_from_name} <{from_email or self.email_from}>"
            message["To"] = to_email
            
            # Add plain text part
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)
            
            # Add HTML part
            part2 = MIMEText(html_content, "html")
            message.attach(part2)
            
            # Send email
            smtp_client = aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.smtp_use_ssl
            )
            
            await smtp_client.connect()
            
            if self.smtp_use_tls and not self.smtp_use_ssl:
                await smtp_client.starttls()
            
            if self.smtp_username and self.smtp_password:
                await smtp_client.login(self.smtp_username, self.smtp_password)
            
            await smtp_client.send_message(message)
            await smtp_client.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_otp_email(
        self,
        to_email: str,
        otp: Optional[str] = None,
        expiry_minutes: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Send OTP code via email
        
        Args:
            to_email: Recipient email address
            otp: OTP code (generates if not provided)
            expiry_minutes: OTP expiry time in minutes (uses default if not provided)
            
        Returns:
            Dictionary with status and OTP (for testing/debugging)
        """
        try:
            # Generate OTP if not provided
            if not otp:
                otp = self.generate_otp(settings.OTP_LENGTH)
            
            # Store OTP
            expiry = expiry_minutes or settings.OTP_EXPIRY_MINUTES
            self.store_otp(to_email, otp, expiry)
            
            # Store OTP
            expiry = expiry_minutes or settings.OTP_EXPIRY_MINUTES
            await self.store_otp(to_email, otp, expiry)
                otp=otp,
                expiry_minutes=expiry,
                email=to_email
            )
            
            # Plain text fallback
            text_content = f"""
            Your OTP code is: {otp}
            
            This code will expire in {expiry} minutes.
            
            If you didn't request this code, please ignore this email.
            """
            
            # Send email
            success = await self.send_email(
                to_email=to_email,
                subject="Your OTP Code",
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                return {
                    "success": True,
                    "message": "OTP sent successfully",
                    "otp": otp if settings.DEBUG else None,  # Only return OTP in debug mode
                    "expiry_minutes": expiry
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to send OTP email"
                }
                
        except Exception as e:
            logger.error(f"Error sending OTP email to {to_email}: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }

    async def send_welcome_email(self, to_email: str, name: str) -> bool:
        """
        Send welcome email to new user
        
        Args:
            to_email: Recipient email address
            name: User's name
            
        Returns:
            True if email sent successfully
        """
        try:
            template = self.template_env.get_template("welcome.html")
            html_content = template.render(name=name)
            
            text_content = f"""
            Welcome {name}!
            
            Thank you for joining Gara API.
            """
            
            return await self.send_email(
                to_email=to_email,
                subject="Welcome to Gara API",
                html_content=html_content,
                text_content=text_content
            )
        except Exception as e:
            logger.error(f"Error sending welcome email to {to_email}: {str(e)}")
            return False

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        reset_url: str
    ) -> bool:
        """
        Send password reset email
        
        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            reset_url: Password reset URL
            
        Returns:
            True if email sent successfully
        """
        try:
            template = self.template_env.get_template("password_reset.html")
            html_content = template.render(
                reset_url=reset_url,
                reset_token=reset_token
            )
            
            text_content = f"""
            Password Reset Request
            
            Click the link below to reset your password:
            {reset_url}
            
            If you didn't request this, please ignore this email.
            """
            
            return await self.send_email(
                to_email=to_email,
                subject="Password Reset Request",
                html_content=html_content,
                text_content=text_content
            )
        except Exception as e:
            logger.error(f"Error sending password reset email to {to_email}: {str(e)}")
            return False


# Create singleton instance
email_service = EmailService()
