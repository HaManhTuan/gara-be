from app.config.constants import API_V1_PREFIX
from app.config.custom_router import APIRouter as CustomAPIRouter
from app.controllers import auth_controller, health_controller, language_controller

# Main API router using custom router
api_router = CustomAPIRouter()

# Include sub-routers
# System routers (auth, health, language) - placed at top
api_router.include_router(health_controller.router, tags=["Health"])
# Language routes
api_router.include_router(language_controller.router, prefix=f"{API_V1_PREFIX}/language", tags=["Language"])
# Public auth routes (login, register)
api_router.include_router(auth_controller.public_router, prefix=f"{API_V1_PREFIX}/auth", tags=["Authentication"])
# Protected auth routes (profile)
api_router.include_router(
    auth_controller.protected_router, prefix=f"{API_V1_PREFIX}/auth", tags=["Authentication"], requires_auth=True
)
