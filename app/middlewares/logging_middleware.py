import time
from typing import Any, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.tracing import add_trace_headers_to_response, get_trace_logger, set_trace_context_from_request

logger = get_trace_logger("http")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        # Set up request tracing context and get the request ID
        request_id = set_trace_context_from_request(request)

        # Get logger with request ID from context

        # Log the request
        logger.info(f"{request.method} {request.url.path}")

        # Process the request and track timing
        start_time = time.time()

        try:
            # Process the request
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log the response
            logger.info(
                f"{request.method} {request.url.path} - " f"Status: {response.status_code} - Time: {process_time:.4f}s"
            )

            # Add trace headers to response
            add_trace_headers_to_response(response, request_id)
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception:
            # Don't log exceptions here - let the exception middleware handle logging
            # This prevents duplicate logging for known expected cases (like 409 Conflict)
            raise


def setup_logging_middleware(app: FastAPI) -> FastAPI:
    """Setup logging middleware for FastAPI app"""
    app.add_middleware(LoggingMiddleware)
    return app
