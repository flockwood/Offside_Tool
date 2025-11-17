"""API v1 module."""
from fastapi import APIRouter
from app.api.v1.endpoints import players, auth, users, watchlist

api_router = APIRouter()

# Include authentication endpoints
api_router.include_router(
    auth.router,
    tags=["authentication"],
)

# Include user endpoints
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
)

# Include player endpoints
api_router.include_router(
    players.router,
    prefix="/players",
    tags=["players"],
)

# Include watchlist endpoints
api_router.include_router(
    watchlist.router,
    prefix="/watchlist",
    tags=["watchlist"],
)
