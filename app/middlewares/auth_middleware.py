import re
from typing import Any, Callable, List, Optional

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.exceptions import AppException
from app.schemas.common import ResponseBuilder
from app.utils.auth import decode_token
from app.utils.i18n import __
from app.utils.request_context import get_request_id, set_current_user_data
from app.utils.tracing import get_trace_logger

logger = get_trace_logger("auth-middleware")


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware that validates JWT tokens for protected routes.

    This middleware:
    1. Checks if the current route requires authentication
    2. Extracts JWT token from Authorization header
    3. Validates token using jwt.decode() (checks signature and expiration)
    4. Stores decoded token data in request context
    5. Returns 401 with i18n error message if token is invalid/expired/missing for protected routes
    6. Allows public routes to pass through without token validation
    """

    def __init__(self, app: ASGIApp, protected_routes: List[str]) -> None:
        """
        Initialize the authentication middleware.

        Args:
            app: The ASGI application
            protected_routes: List of route patterns that require authentication
        """
        super().__init__(app)
        self.protected_routes = protected_routes
        logger.debug(f"AuthMiddleware initialized with {len(protected_routes)} protected routes")
        logger.debug(f"Protected routes: {protected_routes}")

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process the request and validate authentication for protected routes.

        Args:
            request: The incoming request
            call_next: The next middleware/endpoint in the chain

        Returns:
            Response from the next middleware/endpoint
        """
        request_id = get_request_id()
        logger.debug(f"[{request_id}] AuthMiddleware: Processing request to {request.url.path}")

        # Skip auth for CORS preflight requests
        if request.method == "OPTIONS":
            logger.debug(f"[{request_id}] AuthMiddleware: Skipping auth for OPTIONS request")
            return await call_next(request)

        # Check if the current route requires authentication
        if self._requires_auth(request.url.path):
            logger.debug(f"[{request_id}] AuthMiddleware: Route requires authentication")

            # Extract token from Authorization header
            token = self._extract_token(request)
            if not token:
                logger.info(f"[{request_id}] AuthMiddleware: No token provided for protected route")
                return Response(
                    content=ResponseBuilder.error(
                        message=__("auth.token_missing"),
                        code=status.HTTP_401_UNAUTHORIZED,
                        details={"token_required": True},
                        request_id=request_id,
                    ).model_dump_json(),
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    media_type="application/json",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            try:
                # Validate token and decode payload
                payload = decode_token(token)
                logger.debug(f"[{request_id}] AuthMiddleware: Token validated successfully")

                # Store decoded token data in request context
                set_current_user_data(payload)
                logger.debug(f"[{request_id}] AuthMiddleware: User data stored in context")

            except AppException as e:
                # Handle known auth errors locally to avoid noisy ExceptionGroup logs
                logger.info(f"[{request_id}] Auth error: {e.message}")
                return Response(
                    content=ResponseBuilder.error(
                        message=e.message,
                        code=e.status_code,
                        details=e.details,
                        request_id=request_id,
                    ).model_dump_json(),
                    status_code=e.status_code,
                    media_type="application/json",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except Exception as e:
                logger.error(f"[{request_id}] Auth error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=__("auth.token_invalid"),
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            logger.debug(f"[{request_id}] AuthMiddleware: Route does not require authentication")

        # Call the next middleware/endpoint
        response = await call_next(request)
        return response

    def _requires_auth(self, path: str) -> bool:
        """
        Check if the given path requires authentication.

        Args:
            path: The request path

        Returns:
            True if the path requires authentication, False otherwise
        """
        for pattern in self.protected_routes:
            if self._match_pattern(pattern, path):
                return True
        return False

    def _match_pattern(self, pattern: str, path: str) -> bool:
        """
        Match a route pattern against a path.

        Supports wildcards (*) for matching any characters.

        Args:
            pattern: The route pattern (e.g., "/api/v1/users/*")
            path: The request path

        Returns:
            True if the pattern matches the path, False otherwise
        """
        # Convert pattern to regex
        # Replace * with .* for regex matching
        regex_pattern = pattern.replace("*", ".*")
        # Escape other special regex characters except . and *
        regex_pattern = re.escape(regex_pattern).replace(r"\*", ".*")

        # Add anchors to match the entire path
        regex_pattern = f"^{regex_pattern}$"

        return bool(re.match(regex_pattern, path))

    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header.

        Args:
            request: The request object

        Returns:
            The JWT token if found, None otherwise
        """
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None

        # Check if it's a Bearer token
        if not authorization.startswith("Bearer "):
            return None

        # Extract the token part
        token = authorization[7:]  # Remove "Bearer " prefix
        return token if token else None  # type: ignore[no-any-return]
