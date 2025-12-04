from typing import Any, Dict, List, Optional

from fastapi import APIRouter as FastAPIRouter


class APIRouter(FastAPIRouter):
    """
    Custom APIRouter that extends FastAPI's APIRouter to support authentication requirements.

    This allows marking entire routers as requiring authentication via the requires_auth parameter.
    """

    def __init__(self, *args: Any, requires_auth: bool = False, **kwargs: Any) -> None:
        """
        Initialize the custom APIRouter.

        Args:
            *args: Arguments passed to FastAPI's APIRouter
            requires_auth: Whether routes in this router require authentication
            **kwargs: Keyword arguments passed to FastAPI's APIRouter
        """
        super().__init__(*args, **kwargs)
        self.requires_auth = requires_auth
        # Store explicit protected route patterns registered during includes
        self.protected_patterns: List[str] = []

    def include_router(
        self,
        router: "APIRouter",
        *,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[Any]] = None,
        responses: Optional[Dict[str, Any]] = None,
        callbacks: Optional[List[Any]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        requires_auth: Optional[bool] = None,
    ) -> None:
        """
        Include a router with optional authentication requirement.

        Args:
            router: The router to include
            prefix: URL prefix for the router
            tags: Tags for OpenAPI documentation
            dependencies: Dependencies for the router
            responses: Response models for OpenAPI documentation
            callbacks: Callback functions
            deprecated: Whether the router is deprecated
            include_in_schema: Whether to include in OpenAPI schema
            requires_auth: Whether routes in this router require authentication
        """
        # If requires_auth is not specified, inherit from the router being included
        if requires_auth is None:
            requires_auth = getattr(router, "requires_auth", False)

        # Set the requires_auth flag on the router
        router.requires_auth = requires_auth

        # If this include is protected, record exact route patterns for later collection
        if requires_auth:
            normalized_prefix = prefix if prefix.startswith("/") else f"/{prefix}"
            for r in getattr(router, "routes", []):
                if hasattr(r, "path"):
                    full_path = f"{normalized_prefix}{r.path}"
                    pattern = full_path.replace("{", "*").replace("}", "*")
                    if pattern not in self.protected_patterns:
                        self.protected_patterns.append(pattern)

        # Call the parent method
        super().include_router(
            router=router,
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            responses=responses,
            callbacks=callbacks,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
        )
