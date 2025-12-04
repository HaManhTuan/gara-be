"""
Central FastAPI exception handler.

This module provides a single exception_handler(request, exc) function used by
app.add_exception_handler to format errors consistently across the API.
"""

import traceback

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from app.exceptions import (
    AppException,
    TokenExpiredException,
    TokenInvalidException,
    TokenMissingException,
    UnauthorizedException,
)
from app.schemas.common import ResponseBuilder
from app.utils.i18n import __
from app.utils.logger import get_logger

logger = get_logger("exception-handler")


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Central exception handler.

    Handles different types of exceptions and returns appropriate HTTP responses.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    method = request.method
    url = str(request.url)

    # Pass through HTTPException (let FastAPI handle it normally)
    if isinstance(exc, HTTPException):
        logger.warning(
            f"HTTP Exception [{request_id}]: {exc.status_code} - {exc.detail}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "status_code": exc.status_code,
                "detail": exc.detail,
            },
        )
        raise exc

    # Application-specific exceptions
    if isinstance(exc, AppException):
        if isinstance(
            exc, (UnauthorizedException, TokenExpiredException, TokenInvalidException, TokenMissingException)
        ):
            logger.debug(
                f"Auth Exception [{request_id}]: {exc.status_code} - {exc.message}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "status_code": exc.status_code,
                    "message": exc.message,
                    "details": exc.details,
                },
            )
        else:
            logger.debug(
                f"Application Exception [{request_id}]: {exc.status_code} - {exc.message}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "status_code": exc.status_code,
                    "message": exc.message,
                    "details": exc.details,
                },
            )

        return JSONResponse(
            status_code=exc.status_code,
            content=ResponseBuilder.error(
                message=exc.message, code=exc.status_code, details=exc.details, request_id=request_id
            ).model_dump(mode="json"),
        )

    # SQLAlchemy integrity violations
    if isinstance(exc, IntegrityError):
        logger.error(
            f"Database Integrity Error [{request_id}]: {str(exc)}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "error_type": "integrity_error",
                "error_message": str(exc),
            },
        )

        error_message = str(exc.orig) if hasattr(exc, "orig") else str(exc)
        if "unique constraint" in error_message.lower():
            return JSONResponse(
                status_code=409,
                content=ResponseBuilder.conflict(
                    message=__("general.resource_already_exists"),
                    details={"constraint_violation": True},
                    request_id=request_id,
                ).model_dump(mode="json"),
            )
        elif "foreign key constraint" in error_message.lower():
            return JSONResponse(
                status_code=422,
                content=ResponseBuilder.validation_error(
                    message=__("general.invalid_reference"),
                    details={"foreign_key_violation": True},
                    request_id=request_id,
                ).model_dump(mode="json"),
            )
        else:
            return JSONResponse(
                status_code=422,
                content=ResponseBuilder.validation_error(
                    message=__("general.database_constraint_error"),
                    details={"constraint_error": True},
                    request_id=request_id,
                ).model_dump(mode="json"),
            )

    # Not found from ORM
    if isinstance(exc, NoResultFound):
        logger.warning(
            f"Resource Not Found [{request_id}]: {str(exc)}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "error_type": "not_found",
                "error_message": str(exc),
            },
        )

        return JSONResponse(
            status_code=404,
            content=ResponseBuilder.not_found(message=__("general.not_found"), request_id=request_id).model_dump(
                mode="json"
            ),
        )

    # Other SQLAlchemy errors
    if isinstance(exc, SQLAlchemyError):
        logger.error(
            f"Database Error [{request_id}]: {str(exc)}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "error_type": "database_error",
                "error_message": str(exc),
            },
        )

        return JSONResponse(
            status_code=500,
            content=ResponseBuilder.internal_error(
                message=__("general.database_error"), request_id=request_id
            ).model_dump(mode="json"),
        )

    # Validation errors
    if isinstance(exc, ValueError):
        logger.warning(
            f"Validation Error [{request_id}]: {str(exc)}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "error_type": "validation_error",
                "error_message": str(exc),
            },
        )

        return JSONResponse(
            status_code=422,
            content=ResponseBuilder.validation_error(
                message=str(exc), details={"validation_error": True}, request_id=request_id
            ).model_dump(mode="json"),
        )

    # Catch-all
    logger.error(
        f"Unhandled Exception [{request_id}]: {str(exc)}",
        extra={
            "request_id": request_id,
            "method": method,
            "url": url,
            "error_type": "unhandled_exception",
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )
    logger.error(f"Unhandled exception in request {request_id}: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content=ResponseBuilder.internal_error(
            message=__("general.unexpected_error"), request_id=request_id
        ).model_dump(mode="json"),
    )
