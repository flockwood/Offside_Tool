"""
Reusable dependencies for FastAPI endpoints.
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import get_db
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.user import TokenData


# OAuth2 scheme for token authentication
# tokenUrl points to the endpoint where users can get their token
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/login/token")


async def get_current_user(
    token: Annotated[str, Depends(reusable_oauth2)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    This dependency:
    1. Extracts the JWT token from the Authorization header
    2. Decodes and validates the token
    3. Fetches the user from the database
    4. Returns the User object

    Args:
        token: JWT token from Authorization header (automatically extracted)
        db: Database session

    Returns:
        User object for the authenticated user

    Raises:
        HTTPException 401: If token is invalid, expired, or user not found

    Example:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"message": f"Hello {current_user.email}"}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")

        if email is None:
            raise credentials_exception

        token_data = TokenData(email=email)

    except JWTError:
        raise credentials_exception

    # Fetch user from database
    user = await user_crud.get_user_by_email(db, email=token_data.email)  # type: ignore

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to get the current active user.

    This adds an additional check on top of get_current_user to ensure
    the user account is active.

    Args:
        current_user: User object from get_current_user dependency

    Returns:
        User object if account is active

    Raises:
        HTTPException 400: If user account is inactive

    Example:
        @router.get("/users/me")
        async def read_users_me(current_user: User = Depends(get_current_active_user)):
            return current_user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
