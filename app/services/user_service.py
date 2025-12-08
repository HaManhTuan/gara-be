from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictException
from app.models.user import User
from app.repositories.concrete.user_repository import UserRepository, user_repository
from app.schemas.users import UserCreate
from app.services.base_service import BaseService
from app.utils.i18n import __
from app.utils.logger import get_logger

# Initialize logger
logger = get_logger("user-service")


class UserService(BaseService[User, UserRepository]):
    """Service for user-related operations"""

    def __init__(self) -> None:
        super().__init__(user_repository)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        logger.debug(f"Looking up user by email: {email}")
        return await user_repository.get_by_email(db, email=email)

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        logger.debug(f"Looking up user by username: {username}")
        return await user_repository.get_by_username(db, username=username)

    async def get_by_phone_number(self, db: AsyncSession, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        logger.debug(f"Looking up user by phone number: {phone_number}")
        return await user_repository.get_by_phone_number(db, phone_number=phone_number)

    async def create_user(
        self,
        db: AsyncSession,
        user_data: UserCreate,
    ) -> User:
        """Create a new user"""
        logger.info(f"Creating new user with username: {user_data.username}, email: {user_data.email}")

        # Check if email already exists
        if await self.get_by_email(db, email=user_data.email):
            logger.warning(f"Attempt to create user with existing email: {user_data.email}")
            raise ConflictException(__("user.email_already_exists"))

        # Check if username already exists
        if await self.get_by_username(db, username=user_data.username):
            logger.warning(f"Attempt to create user with existing username: {user_data.username}")
            raise ConflictException(__("user.username_already_exists"))

        # Create user using the schema
        return await user_repository.create(db, obj_in=user_data)

    async def authenticate_user(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password"""
        logger.debug(f"Authenticating user: {username}")
        user = await self.get_by_username(db, username=username)

        if not user:
            logger.warning(f"Authentication failed: user not found: {username}")
            return None

        if not user.check_password(password):
            logger.warning(f"Authentication failed: incorrect password for user: {username}")
            return None

        return user

    async def update_user_with_optimistic_lock(
        self,
        db: AsyncSession,
        user_id: str,
        update_data: dict,
        expected_updated_at: Optional[str] = None,
    ) -> User:
        """Update user with optimistic locking"""
        logger.debug(f"Updating user {user_id} with optimistic lock")
        return await user_repository.update_with_optimistic_lock(
            db=db,
            id=user_id,
            obj_in=update_data,
            expected_updated_at=expected_updated_at,
        )

    async def get_or_create_firebase_user(
        self,
        db: AsyncSession,
        firebase_uid: str,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        name: Optional[str] = None,
        picture: Optional[str] = None,
    ) -> Tuple[User, bool]:
        """
        Get or create user from Firebase authentication data

        Args:
            db: Database session
            firebase_uid: Firebase user UID
            email: User email from Firebase (optional for phone auth)
            phone_number: User phone number from Firebase (optional for email auth)
            name: User display name from Firebase
            picture: User profile picture URL from Firebase

        Returns:
            Tuple of (User, is_new_user)
        """
        # Try to find existing user by email or phone
        user = None
        
        if email:
            user = await self.get_by_email(db, email=email)
            if user:
                logger.info(f"Existing user found by email for Firebase UID {firebase_uid}: {email}")
                return user, False
        
        if phone_number:
            user = await self.get_by_phone_number(db, phone_number=phone_number)
            if user:
                logger.info(f"Existing user found by phone for Firebase UID {firebase_uid}: {phone_number}")
                return user, False

        # Create new user
        logger.info(f"Creating new user from Firebase authentication: {email or phone_number}")

        # Generate username from email or phone
        if email:
            username = email.split("@")[0]
        elif phone_number:
            # Remove + and other characters from phone, keep only digits
            username = "user_" + "".join(filter(str.isdigit, phone_number))
        else:
            # Fallback to firebase UID
            username = f"user_{firebase_uid[:8]}"

        # Check if username exists, if so append a number
        base_username = username
        counter = 1
        while await self.get_by_username(db, username=username):
            username = f"{base_username}{counter}"
            counter += 1

        # Create user data - email can be None for phone auth
        user_data = UserCreate(
            username=username,
            email=email,  # Can be None
            password=firebase_uid,  # Use Firebase UID as password (won't be used for login)
            full_name=name or email or phone_number or username,
            phone_number=phone_number,
            phone_verified=bool(phone_number),  # If phone login, mark as verified
        )

        user = await user_repository.create(db, obj_in=user_data)
        logger.info(f"New user created from Firebase: {email or phone_number}")

        return user, True

    async def get_or_create_user_by_email(
        self,
        db: AsyncSession,
        email: str,
        full_name: Optional[str] = None,
    ) -> Tuple[User, bool]:
        """
        Get or create user by email (for email OTP login)

        Args:
            db: Database session
            email: User email
            full_name: User full name (optional)

        Returns:
            Tuple of (User, is_new_user)
        """
        # Try to find existing user by email
        user = await self.get_by_email(db, email=email)
        
        if user:
            logger.info(f"Existing user found by email: {email}")
            return user, False

        # Create new user
        logger.info(f"Creating new user from email login: {email}")

        # Generate username from email
        username = email.split("@")[0]
        
        # Check if username exists, if so append a number
        base_username = username
        counter = 1
        while await self.get_by_username(db, username=username):
            username = f"{base_username}{counter}"
            counter += 1

        # Create user data
        user_data = UserCreate(
            username=username,
            email=email,
            password=email,  # Use email as password (won't be used for login with OTP)
            full_name=full_name or username,
        )

        user = await user_repository.create(db, obj_in=user_data)
        logger.info(f"New user created from email OTP login: {email}")

        return user, True


# Create instance for dependency injection
user_service = UserService()
