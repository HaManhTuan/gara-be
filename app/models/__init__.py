"""
Import all models here to ensure they are registered with SQLAlchemy metadata.
This is used by Alembic for auto-generating migrations.
"""

# Import base model
from app.models.base_model import BaseModel

# Import all entity models
from app.models.user import User

__all__ = [
    "BaseModel",
    "User",
]
