from typing import Optional

from sqlalchemy import Boolean, Column, String
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.base_model import BaseModel


class User(BaseModel):
    """User model for authentication"""

    # User information
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)  # Nullable for phone-only auth
    full_name = Column(String, nullable=True)
    phone_number = Column(String, unique=True, index=True, nullable=True)  # Add unique constraint
    phone_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    hashed_password = Column(String, nullable=False)

    def __init__(
        self,
        username: str = None,
        email: str = None,
        password: str = None,
        full_name: Optional[str] = None,
        is_superuser: bool = False,
        **kwargs,
    ) -> None:
        """Initialize a new user"""
        # Handle kwargs for flexibility (useful for testing and ORM)
        if kwargs:
            for key, value in kwargs.items():
                # Skip relationship fields as they should be handled separately
                if key in []:  # No relationships currently defined
                    continue
                if hasattr(self, key):
                    setattr(self, key, value)

        # Set required fields if provided
        if username is not None:
            self.username = username
        if email is not None:
            self.email = email
        if password is not None:
            self.set_password(password)
        if full_name is not None:
            self.full_name = full_name
        self.is_superuser = is_superuser

    def set_password(self, password: str) -> None:
        """Set password hash"""
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check password against stored hash"""
        return check_password_hash(self.hashed_password, password)  # type: ignore[no-any-return]

    # Relationships
    # No relationships defined - User model is standalone

    def __repr__(self) -> str:
        """String representation"""
        return f"<User(id={self.id}, username={self.username})>"
