"""
Standardized response format for API endpoints.

This module provides consistent response structures for all API endpoints,
ensuring uniform error handling and success responses.
"""

from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import Field

from app.schemas.common.base_schema import BaseSchema

T = TypeVar("T")


class ErrorDetail(BaseSchema):
    """Standard error detail structure"""

    message: str = Field(..., description="Error message")
    code: int = Field(..., description="HTTP status code")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class ErrorResponse(BaseSchema):
    """Standard error response structure"""

    error: ErrorDetail = Field(..., description="Error details")
    success: bool = Field(False, description="Success flag")
    data: Optional[Any] = Field(None, description="Data payload (null for errors)")


class SuccessResponse(BaseSchema, Generic[T]):
    """Standard success response structure"""

    success: bool = Field(True, description="Success flag")
    message: str = Field(..., description="Success message")
    data: Optional[T] = Field(None, description="Response data")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class PaginationMeta(BaseSchema):
    """Pagination metadata"""

    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response structure"""

    success: bool = Field(True, description="Success flag")
    message: str = Field(..., description="Success message")
    data: list[T] = Field(..., description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ResponseBuilder:
    """Builder class for creating standardized responses"""

    @staticmethod
    def success(message: str, data: Optional[T] = None, meta: Optional[Dict[str, Any]] = None) -> SuccessResponse[T]:
        """Create a success response"""
        return SuccessResponse[T](success=True, message=message, data=data, meta=meta)

    @staticmethod
    def error(
        message: str, code: int, details: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create an error response"""
        return ErrorResponse(
            error=ErrorDetail(message=message, code=code, details=details or {}, request_id=request_id),
            success=False,
            data=None,
        )

    @staticmethod
    def paginated(message: str, data: list[T], page: int, per_page: int, total: int) -> PaginatedResponse[T]:
        """Create a paginated response"""
        pages = (total + per_page - 1) // per_page  # Ceiling division
        has_next = page < pages
        has_prev = page > 1

        return PaginatedResponse[T](
            success=True,
            message=message,
            data=data,
            pagination=PaginationMeta(
                page=page, per_page=per_page, total=total, pages=pages, has_next=has_next, has_prev=has_prev
            ),
        )

    @staticmethod
    def created(message: str, data: Optional[T] = None) -> SuccessResponse[T]:
        """Create a success response for resource creation"""
        return ResponseBuilder.success(message, data)

    @staticmethod
    def updated(message: str, data: Optional[T] = None) -> SuccessResponse[T]:
        """Create a success response for resource updates"""
        return ResponseBuilder.success(message, data)

    @staticmethod
    def deleted(message: str) -> SuccessResponse[None]:
        """Create a success response for resource deletion"""
        return ResponseBuilder.success(message, None)

    @staticmethod
    def not_found(message: str, request_id: Optional[str] = None) -> ErrorResponse:
        """Create a not found error response"""
        return ResponseBuilder.error(message=message, code=404, request_id=request_id)

    @staticmethod
    def validation_error(
        message: str, details: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a validation error response"""
        return ResponseBuilder.error(message=message, code=400, details=details, request_id=request_id)

    @staticmethod
    def conflict(
        message: str, details: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a conflict error response"""
        return ResponseBuilder.error(message=message, code=409, details=details, request_id=request_id)

    @staticmethod
    def unauthorized(message: str, request_id: Optional[str] = None) -> ErrorResponse:
        """Create an unauthorized error response"""
        return ResponseBuilder.error(message=message, code=401, request_id=request_id)

    @staticmethod
    def forbidden(message: str, request_id: Optional[str] = None) -> ErrorResponse:
        """Create a forbidden error response"""
        return ResponseBuilder.error(message=message, code=403, request_id=request_id)

    @staticmethod
    def internal_error(message: str, request_id: Optional[str] = None) -> ErrorResponse:
        """Create an internal server error response"""
        return ResponseBuilder.error(message=message, code=500, request_id=request_id)
