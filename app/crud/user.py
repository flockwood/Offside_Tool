"""
CRUD operations for User model.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Fetch a user by their email address.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User object if found, None otherwise

    Example:
        >>> user = await get_user_by_email(db, "user@example.com")
        >>> if user:
        >>>     print(f"Found user: {user.email}")
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Fetch a user by their ID.

    Args:
        db: Database session
        user_id: User's ID

    Returns:
        User object if found, None otherwise

    Example:
        >>> user = await get_user_by_id(db, 1)
        >>> if user:
        >>>     print(f"Found user: {user.email}")
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """
    Create a new user with hashed password.

    IMPORTANT: This function hashes the password before storing it.
    Never store plain passwords in the database.

    Args:
        db: Database session
        user: UserCreate schema with email and plain password

    Returns:
        Created User object

    Example:
        >>> user_in = UserCreate(email="new@example.com", password="secret123")
        >>> new_user = await create_user(db, user_in)
        >>> print(f"Created user: {new_user.email}")
    """
    hashed_password = get_password_hash(user.password)

    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=True
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User's email
        password: Plain text password to verify

    Returns:
        User object if authentication successful, None otherwise

    Example:
        >>> user = await authenticate_user(db, "user@example.com", "password123")
        >>> if user:
        >>>     print("Authentication successful")
        >>> else:
        >>>     print("Invalid credentials")
    """
    from app.core.security import verify_password

    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
