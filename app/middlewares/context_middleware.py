from typing import Any, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import get_logger, set_request_id

logger = get_logger("context-middleware")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that propagates request context throughout the application.

    This middleware ensures that request context (especially request ID)
    is properly propagated during the entire request lifecycle and is
    available to all services called by the controllers.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        request_id = getattr(request.state, "request_id", None)

        # Make sure we have access to the request ID in this context
        if request_id:
            # Set request ID in the context var for the current execution
            # context
            set_request_id(request_id)

            # Create a logger for this context
            context_logger = get_logger("context")
            context_logger.debug(f"Setting request context: request_id={request_id}")

            # Process the request with the context
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                context_logger.error(f"Error processing request: {str(e)}")
                raise
        else:
            # No request ID available (should not happen if LoggingMiddleware
            # runs first)
            logger.warning("No request_id available in request context")
            return await call_next(request)


def setup_context_middleware(app: FastAPI) -> None:
    """
    Set up the request context middleware for a FastAPI app

    Args:
        app: The FastAPI application instance
    """
    app.add_middleware(RequestContextMiddleware)
    return None
