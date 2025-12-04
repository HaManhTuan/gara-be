"""
Utility functions for generating trace IDs and working with request context.

This module provides helper functions for request tracing and context management.
"""
import uuid
from typing import TYPE_CHECKING, Optional

from fastapi import Request, Response

from app.utils.logger import get_logger, set_request_id

if TYPE_CHECKING:
    from loguru import Logger


def generate_request_id() -> str:
    """
    Generate a unique request ID using UUID4.

    Returns:
        A string containing a unique request ID
    """
    return str(uuid.uuid4())


def get_trace_logger(name: Optional[str] = None) -> "Logger":
    """
    Get a logger that includes the current request ID if available.

    This is a convenience function that can be used anywhere in the application
    to get a logger that will automatically include the current request ID
    in all log messages, if there is an active request context.

    Args:
        name: The logger name (e.g., component name)

    Returns:
        A logger instance with request ID bound
    """
    return get_logger(name)  # The get_logger function already binds the request ID


def set_trace_context_from_request(request: Request) -> str:
    """
    Set tracing context based on a FastAPI request.

    This function extracts the request ID from the request object
    (or generates a new one) and sets it in the context.

    Args:
        request: The FastAPI request object

    Returns:
        The request ID that was set
    """
    # Use existing request ID from headers if available
    request_id: Optional[str] = request.headers.get("X-Request-ID")

    # If no request ID in headers, check if it was already set in request.state
    if not request_id:
        request_id = getattr(request.state, "request_id", None)

    # If still no request ID, generate a new one
    if not request_id:
        request_id = generate_request_id()

    # Set the request ID in the request.state for other middleware/handlers
    request.state.request_id = request_id

    # Set the request ID in the context for logging
    set_request_id(request_id)

    return request_id


def add_trace_headers_to_response(response: Response, request_id: str) -> None:
    """
    Add tracing headers to a FastAPI response.

    Args:
        response: The FastAPI response object
        request_id: The request ID to include in headers
    """
    response.headers["X-Request-ID"] = request_id
