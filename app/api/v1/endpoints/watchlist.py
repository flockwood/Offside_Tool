"""
Watchlist API endpoints for managing user's followed players.

All endpoints require authentication.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.crud import player as player_crud
from app.crud import watchlist as watchlist_crud
from app.schemas.player import Player

router = APIRouter()


@router.post(
    "/{player_id}",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Add player to watchlist"
)
async def add_to_watchlist(
    player_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_active_user)],
) -> dict:
    """
    Add a player to the current user's watchlist.

    Parameters:
    - **player_id**: ID of the player to add to watchlist

    Returns:
    - Success message with player details

    Requires:
    - Valid JWT token in Authorization header

    Raises:
    - 401: If not authenticated
    - 404: If player not found
    """
    # Check if player exists
    player = await player_crud.get(db, player_id=player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with ID {player_id} not found"
        )

    # Add to watchlist
    await watchlist_crud.add_player_to_watchlist(db, current_user, player)

    return {
        "message": f"Player '{player.full_name}' added to watchlist",
        "player_id": player.id,
        "player_name": player.full_name
    }


@router.delete(
    "/{player_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove player from watchlist"
)
async def remove_from_watchlist(
    player_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_active_user)],
) -> dict:
    """
    Remove a player from the current user's watchlist.

    Parameters:
    - **player_id**: ID of the player to remove from watchlist

    Returns:
    - Success message

    Requires:
    - Valid JWT token in Authorization header

    Raises:
    - 401: If not authenticated
    - 404: If player not found
    """
    # Check if player exists
    player = await player_crud.get(db, player_id=player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with ID {player_id} not found"
        )

    # Remove from watchlist
    await watchlist_crud.remove_player_from_watchlist(db, current_user, player)

    return {
        "message": f"Player '{player.full_name}' removed from watchlist",
        "player_id": player.id,
        "player_name": player.full_name
    }


@router.get(
    "/",
    response_model=list[Player],
    summary="Get user's watchlist"
)
async def get_watchlist(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_active_user)],
) -> list[Player]:
    """
    Retrieve all players in the current user's watchlist.

    Returns:
    - List of players in the watchlist (empty list if no players)

    Requires:
    - Valid JWT token in Authorization header

    Raises:
    - 401: If not authenticated
    """
    players = await watchlist_crud.get_user_watchlist(db, current_user)

    # Convert to Pydantic schemas
    return [Player.from_orm_model(p) for p in players]
