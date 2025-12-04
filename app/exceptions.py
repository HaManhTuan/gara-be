"""
Application-specific exceptions.

This module defines custom exception classes for different types of errors
that can occur in the application, providing a consistent way to handle
and communicate errors throughout the system.
"""

from typing import Any, Dict, Optional

from fastapi import status


class AppException(Exception):
    """Base exception for application-specific errors"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """Exception for validation errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)


class NotFoundException(AppException):
    """Exception for resource not found errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND, details=details)


class ConflictException(AppException):
    """Exception for resource conflict errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT, details=details)


class UnauthorizedException(AppException):
    """Exception for unauthorized access errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED, details=details)


class ForbiddenException(AppException):
    """Exception for forbidden access errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN, details=details)


class OptimisticLockException(AppException):
    """Exception for optimistic locking conflicts"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT, details=details)


class TokenMissingException(UnauthorizedException):
    """Raised when an authentication token is missing"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class TokenExpiredException(UnauthorizedException):
    """Raised when an authentication token is expired"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class TokenInvalidException(UnauthorizedException):
    """Raised when an authentication token is invalid"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class InactiveUserException(AppException):
    """Raised when the current user is inactive"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)
