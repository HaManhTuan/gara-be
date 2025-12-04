from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.core import RepositoryImpl
from app.repositories.factory import repository_factory


class UserRepository(RepositoryImpl[User]):
    """Repository for User model extending from unified repository"""

    def __init__(self) -> None:
        # Create unified repository using factory and inherit its components
        unified_repo = repository_factory.create_repository(User)
        # Initialize the base class with the same components
        super().__init__(
            model=User,
            query_builder=unified_repo.query_builder,
            optimistic_lock_validator=unified_repo.optimistic_lock_validator,
        )

    # User-specific methods that can't be handled by base repository
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_by_phone_number(self, db: AsyncSession, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        result = await db.execute(select(User).filter(User.phone_number == phone_number))
        return result.scalar_one_or_none()  # type: ignore[no-any-return]


# Create instance for dependency injection
user_repository = UserRepository()
