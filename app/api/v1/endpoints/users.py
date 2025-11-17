"""
User API endpoints.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate
from app.api import deps


router = APIRouter()


@router.post(
    "/",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user account"
)
async def create_user(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_in: UserCreate
) -> User:
    """
    Create a new user account (Public endpoint - no authentication required).

    This endpoint allows anyone to sign up for a new account.

    Parameters:
    - **email**: Valid email address (must be unique)
    - **password**: Password (will be securely hashed)

    Returns:
    - User object with id, email, is_active, and timestamps
    - Password is never returned for security

    Example Request:
    ```json
    {
        "email": "newuser@example.com",
        "password": "securePassword123"
    }
    ```

    Example Response:
    ```json
    {
        "id": 1,
        "email": "newuser@example.com",
        "is_active": true,
        "created_at": "2025-01-17T10:30:00",
        "updated_at": "2025-01-17T10:30:00"
    }
    ```

    Raises:
    - **400 Bad Request**: If email already exists
    """
    # Check if user already exists
    existing_user = await user_crud.get_user_by_email(db, email=user_in.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{user_in.email}' already exists"
        )

    # Create new user (password will be hashed in CRUD function)
    user = await user_crud.create_user(db, user=user_in)

    return user


@router.get(
    "/me",
    response_model=UserSchema,
    summary="Get current user information"
)
async def read_users_me(
    current_user: Annotated[User, Depends(deps.get_current_active_user)]
) -> User:
    """
    Get the currently authenticated user's information (Protected endpoint).

    This endpoint requires a valid JWT token in the Authorization header.

    Returns:
    - User object for the authenticated user

    Example Request:
    ```
    GET /api/v1/users/me
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    ```

    Example Response:
    ```json
    {
        "id": 1,
        "email": "user@example.com",
        "is_active": true,
        "created_at": "2025-01-17T10:30:00",
        "updated_at": "2025-01-17T10:30:00"
    }
    ```

    Raises:
    - **401 Unauthorized**: If token is invalid or missing
    - **400 Bad Request**: If user account is inactive
    """
    return current_user
