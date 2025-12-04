from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import get_logger

if TYPE_CHECKING:
    from loguru import Logger

# Context variable to store the current user data from JWT token
_current_user_data: ContextVar[Optional[Dict[str, Any]]] = ContextVar("current_user_data", default=None)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that makes request context available throughout the request lifecycle.
    This allows accessing request info like the request_id from anywhere in the code.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        # The request ID is already set in LoggingMiddleware,
        # but we could add more request context here if needed

        # Continue processing the request
        response = await call_next(request)
        return response


def get_context_logger(name: Optional[str] = None) -> "Logger":
    """
    Get a logger with the current request ID and optional name

    This is a convenience wrapper around get_logger that ensures
    we're using the current request ID from the context.

    Args:
        name: Optional name for the logger context

    Returns:
        Logger instance with request ID bound
    """
    # The request ID should already be set in the context by the LoggingMiddleware
    # This function just makes it easier to get a logger with that ID
    return get_logger(name)


def get_request_context(request: Request) -> Dict[str, Any]:
    """
    Dependency to extract and return important context data from the request.
    Can be used in route functions to access request context.

    Args:
        request: The FastAPI request object

    Returns:
        Dict containing request context information
    """
    request_id = getattr(request.state, "request_id", None)

    # You could add more context data here if needed
    context = {
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
    }

    return context


def set_current_user_data(user_data: Dict[str, Any]) -> None:
    """
    Store decoded JWT token data in request context.

    This function is called by the AuthMiddleware to store user information
    extracted from the JWT token, making it available throughout the request.

    Args:
        user_data: Decoded JWT payload containing user information
    """
    _current_user_data.set(user_data)


def get_current_user_data() -> Optional[Dict[str, Any]]:
    """
    Get decoded JWT token data from request context.

    This function retrieves user information that was stored by the AuthMiddleware
    from the JWT token. This avoids the need to decode the token again in endpoints.

    Returns:
        Decoded JWT payload containing user information, or None if not available
    """
    return _current_user_data.get()


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    This is a convenience function to get the request ID that was set by
    the LoggingMiddleware.

    Returns:
        The current request ID, or None if not available
    """
    from app.utils.logger import get_request_id as logger_get_request_id

    return logger_get_request_id()
