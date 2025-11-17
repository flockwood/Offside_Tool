"""
Security utilities for password hashing and JWT token management.
"""
from datetime import datetime, timedelta
from typing import Any
from jose import jwt
import bcrypt

from app.core.config import settings

# JWT configuration
ALGORITHM = "HS256"


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing claims to encode in the token (e.g., {"sub": "user@example.com"})
        expires_delta: Optional custom expiration time. If not provided, uses default from settings.

    Returns:
        Encoded JWT token as a string

    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> # Token is valid for ACCESS_TOKEN_EXPIRE_MINUTES
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its bcrypt hash.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The bcrypt hashed password from database

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = get_password_hash("secret123")
        >>> verify_password("secret123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """
    Hash a plain password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hashed password

    Example:
        >>> hashed = get_password_hash("mysecretpassword")
        >>> # Returns bcrypt hash like "$2b$12$..."
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')
