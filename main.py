import uvicorn
from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError

from app.config.middlewares import setup_middlewares
from app.config.settings import settings
from app.controllers import api_router
from app.handlers.exception_handler import exception_handler
from app.utils.model_relationship_manager import initialize_model_relationships

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize model relationships
initialize_model_relationships()

# Setup middlewares
setup_middlewares(app, api_router)  # This middleware handles CORS and other middlewares

# Add exception handler
app.add_exception_handler(Exception, exception_handler)
app.add_exception_handler(IntegrityError, exception_handler)

# Include API router
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
