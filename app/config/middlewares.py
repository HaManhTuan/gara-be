from typing import Any, List

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.middlewares.auth_middleware import AuthMiddleware
from app.middlewares.context_middleware import RequestContextMiddleware
from app.middlewares.language_middleware import LanguageDetectionMiddleware
from app.middlewares.logging_middleware import LoggingMiddleware


def collect_protected_routes(api_router: Any) -> List[str]:
    """
    Collect all protected route patterns from the API router.

    This function traverses the router tree to find all routes that require authentication
    and returns their patterns for use by the AuthMiddleware.

    Args:
        api_router: The main API router to collect routes from

    Returns:
        List of route patterns that require authentication
    """
    protected_routes: List[str] = []

    def collect_from_router(router: Any, prefix: str = "") -> None:
        """Collect protected routes using router flags and recorded protected prefixes."""
        current_prefix = prefix + (getattr(router, "prefix", "") or "")

        # 1) If this router is marked as requiring auth, mark all its routes
        if getattr(router, "requires_auth", False):
            for route in getattr(router, "routes", []):
                if hasattr(route, "path"):
                    route_path = current_prefix + route.path
                    pattern = route_path.replace("{", "*").replace("}", "*")
                    protected_routes.append(pattern)

        # 2) Use any explicit protected patterns recorded by the custom router during includes
        protected_patterns = getattr(router, "protected_patterns", [])
        if protected_patterns:
            protected_routes.extend(protected_patterns)

        # 3) Best-effort recursion if any nested routers exist
        for route in getattr(router, "routes", []):
            nested_router = getattr(route, "router", None)
            if nested_router and hasattr(nested_router, "routes"):
                sub_prefix = current_prefix + (getattr(route, "path", "") or "")
                collect_from_router(nested_router, sub_prefix)

    # Start collecting from the main API router
    collect_from_router(api_router)

    return protected_routes


def setup_middlewares(app: FastAPI, api_router: Any) -> None:
    """Setup all middleware for the application"""
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add other middlewares here
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(LanguageDetectionMiddleware)

    # Collect protected routes and add auth middleware
    protected_routes = collect_protected_routes(api_router)
    app.add_middleware(AuthMiddleware, protected_routes=protected_routes)

    return None
