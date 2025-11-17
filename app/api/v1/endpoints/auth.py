"""
Authentication API endpoints.
"""
from typing import Annotated
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.crud import user as user_crud
from app.core.security import create_access_token
from app.core.config import settings
from app.schemas.user import Token


router = APIRouter()


@router.post("/login/token", response_model=Token, summary="Login to get access token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    """
    OAuth2 compatible token login endpoint.

    Authenticate with username (email) and password to receive a JWT access token.

    Parameters:
    - **username**: User's email address
    - **password**: User's password

    Returns:
    - **access_token**: JWT token for authenticated requests
    - **token_type**: Token type (always "bearer")

    Example Request:
    ```
    POST /api/v1/login/token
    Content-Type: application/x-www-form-urlencoded

    username=user@example.com&password=secret123
    ```

    Example Response:
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer"
    }
    ```

    Raises:
    - **401 Unauthorized**: If credentials are incorrect
    """
    # OAuth2PasswordRequestForm uses 'username', but we use email for authentication
    user = await user_crud.authenticate_user(
        db,
        email=form_data.username,
        password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")
