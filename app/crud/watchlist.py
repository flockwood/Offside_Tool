"""
CRUD operations for user watchlist management.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.player import Player


async def add_player_to_watchlist(
    db: AsyncSession,
    user: User,
    player: Player
) -> User:
    """
    Add a player to a user's watchlist.

    Args:
        db: Database session
        user: User object
        player: Player object to add

    Returns:
        Updated User object with refreshed watchlist

    Note:
        If the player is already in the watchlist, this operation is idempotent
        and will not raise an error.
    """
    # Check if player is already in watchlist
    if player not in user.watchlist_players:
        user.watchlist_players.append(player)
        await db.commit()
        await db.refresh(user)

    return user


async def remove_player_from_watchlist(
    db: AsyncSession,
    user: User,
    player: Player
) -> User:
    """
    Remove a player from a user's watchlist.

    Args:
        db: Database session
        user: User object
        player: Player object to remove

    Returns:
        Updated User object with refreshed watchlist

    Note:
        If the player is not in the watchlist, this operation is idempotent
        and will not raise an error.
    """
    # Check if player is in watchlist
    if player in user.watchlist_players:
        user.watchlist_players.remove(player)
        await db.commit()
        await db.refresh(user)

    return user


async def get_user_watchlist(
    db: AsyncSession,
    user: User
) -> list[Player]:
    """
    Get all players in a user's watchlist.

    Args:
        db: Database session
        user: User object

    Returns:
        List of Player objects in the user's watchlist
    """
    # Refresh user with watchlist_players loaded
    stmt = (
        select(User)
        .where(User.id == user.id)
        .options(selectinload(User.watchlist_players))
    )
    result = await db.execute(stmt)
    refreshed_user = result.scalar_one()

    return refreshed_user.watchlist_players


async def is_player_in_watchlist(
    db: AsyncSession,
    user: User,
    player_id: int
) -> bool:
    """
    Check if a player is in the user's watchlist.

    Args:
        db: Database session
        user: User object
        player_id: ID of the player to check

    Returns:
        True if player is in watchlist, False otherwise
    """
    # Refresh user with watchlist_players loaded
    stmt = (
        select(User)
        .where(User.id == user.id)
        .options(selectinload(User.watchlist_players))
    )
    result = await db.execute(stmt)
    refreshed_user = result.scalar_one()

    return any(player.id == player_id for player in refreshed_user.watchlist_players)
