"""
Player API endpoints.
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from math import ceil

from app.db.session import get_db
from app.crud.player import player as player_crud
from app.schemas.player import (
    Player,
    PlayerCreate,
    PlayerUpdate,
    PlayerList,
    ComparisonMetric,
    PlayerComparisonSummary,
    PlayerComparisonResponse,
    PlayerSearch,
)
from app.models.player import PlayerPosition
from app.api import deps
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=PlayerList, summary="Get all players")
async def get_players(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    position: Optional[PlayerPosition] = Query(None, description="Filter by position"),
    nationality: Optional[str] = Query(None, description="Filter by nationality"),
    current_club: Optional[str] = Query(None, description="Filter by current club"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Minimum rating"),
    search: Optional[str] = Query(None, description="Search by name or club"),
) -> Any:
    """
    Retrieve players with pagination and filtering.

    Parameters:
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (max 100)
    - **position**: Filter by player position
    - **nationality**: Filter by nationality (case-insensitive)
    - **current_club**: Filter by current club (case-insensitive)
    - **min_rating**: Filter players with rating >= this value
    - **search**: Search in player names and club names
    """
    players, total = await player_crud.get_multi(
        db,
        skip=skip,
        limit=limit,
        position=position,
        nationality=nationality,
        current_club=current_club,
        min_rating=min_rating,
        search=search,
    )

    # Convert ORM models to Pydantic schemas with computed properties
    player_schemas = [Player.from_orm_model(p) for p in players]

    return PlayerList(
        items=player_schemas,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=ceil(total / limit) if total > 0 else 0,
    )


@router.post(
    "/",
    response_model=Player,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new player",
)
async def create_player(
    *,
    db: AsyncSession = Depends(get_db),
    player_in: PlayerCreate,
) -> Any:
    """
    Create a new player.

    Required fields:
    - **first_name**: Player's first name
    - **last_name**: Player's last name
    - **position**: Player's primary position

    Optional fields include nationality, physical attributes, statistics, etc.
    """
    # Check if player with same name already exists
    existing_player = await player_crud.get_by_name(
        db,
        first_name=player_in.first_name,
        last_name=player_in.last_name,
    )

    if existing_player:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Player with name '{player_in.first_name} {player_in.last_name}' already exists",
        )

    player = await player_crud.create(db, obj_in=player_in)
    return Player.from_orm_model(player)


@router.get("/search", response_model=list[Player], summary="Search players by name")
async def search_players(
    name: str = Query(..., min_length=1, description="Name to search for (case-insensitive)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Search for players by name (Protected endpoint - requires authentication).

    Performs a case-insensitive search across both first and last names.

    Parameters:
    - **name**: Search query (minimum 1 character)

    Returns:
    - List of players matching the search query
    - Empty list if no matches found

    Requires:
    - Valid JWT token in Authorization header
    """
    players = await player_crud.search_players_by_name(db, name_query=name)
    return [Player.from_orm_model(p) for p in players]


@router.post(
    "/search/advanced",
    response_model=list[Player],
    summary="Advanced multi-parameter player search"
)
async def advanced_search_players(
    search_params: PlayerSearch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Advanced player search with multiple optional filters (Protected endpoint - requires authentication).

    Filter players by club, nationality, position, and age range.
    All parameters are optional - only provided filters will be applied.

    Parameters (all optional):
    - **club**: Filter by current club (case-insensitive)
    - **nationality**: Filter by nationality (case-insensitive)
    - **position**: Filter by position (goalkeeper, defender, midfielder, forward)
    - **min_age**: Minimum age (inclusive)
    - **max_age**: Maximum age (inclusive)

    Returns:
    - List of players matching ALL provided criteria
    - Empty list if no matches found

    Requires:
    - Valid JWT token in Authorization header

    Example request body:
    ```json
    {
        "club": "Manchester City",
        "position": "midfielder",
        "min_age": 20,
        "max_age": 30
    }
    ```
    """
    players = await player_crud.advanced_search_players(db, search_params)
    return [Player.from_orm_model(p) for p in players]


@router.get("/compare", response_model=PlayerComparisonResponse, summary="Compare two players")
async def compare_players(
    player_id_1: int = Query(..., ge=1, description="ID of first player"),
    player_id_2: int = Query(..., ge=1, description="ID of second player"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Compare two players across key performance metrics (Protected endpoint - requires authentication).

    Compares players on:
    - Market value
    - Goals
    - Assists
    - Goals per match
    - Assists per match

    Parameters:
    - **player_id_1**: ID of the first player to compare
    - **player_id_2**: ID of the second player to compare

    Returns:
    - Detailed comparison showing which player is better in each metric
    - Summary of total wins for each player

    Requires:
    - Valid JWT token in Authorization header

    Raises:
    - 401: If not authenticated
    - 404: If either player is not found
    - 400: If trying to compare a player with itself
    """
    # Validate players are different
    if player_id_1 == player_id_2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare a player with itself. Please provide two different player IDs.",
        )

    # Fetch both players
    player1 = await player_crud.get(db, player_id=player_id_1)
    if not player1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with ID {player_id_1} not found",
        )

    player2 = await player_crud.get(db, player_id=player_id_2)
    if not player2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with ID {player_id_2} not found",
        )

    # Helper function to compare two values
    def compare_metric(value1: Optional[float], value2: Optional[float]) -> ComparisonMetric:
        """Compare two metric values and determine winner."""
        # Handle None values
        if value1 is None and value2 is None:
            return ComparisonMetric(
                player_1_value=None,
                player_2_value=None,
                winner="tie"
            )
        elif value1 is None:
            return ComparisonMetric(
                player_1_value=None,
                player_2_value=value2,
                winner="player_2"
            )
        elif value2 is None:
            return ComparisonMetric(
                player_1_value=value1,
                player_2_value=None,
                winner="player_1"
            )

        # Compare actual values
        if value1 > value2:
            winner = "player_1"
        elif value2 > value1:
            winner = "player_2"
        else:
            winner = "tie"

        return ComparisonMetric(
            player_1_value=value1,
            player_2_value=value2,
            winner=winner
        )

    # Perform comparisons
    market_value_comparison = compare_metric(
        player1.market_value_euros,
        player2.market_value_euros
    )

    goals_comparison = compare_metric(
        float(player1.goals),
        float(player2.goals)
    )

    assists_comparison = compare_metric(
        float(player1.assists),
        float(player2.assists)
    )

    goals_per_match_comparison = compare_metric(
        player1.goals_per_match,
        player2.goals_per_match
    )

    assists_per_match_comparison = compare_metric(
        player1.assists_per_match,
        player2.assists_per_match
    )

    # Create comparison summary
    comparison = PlayerComparisonSummary(
        market_value_euros=market_value_comparison,
        goals=goals_comparison,
        assists=assists_comparison,
        goals_per_match=goals_per_match_comparison,
        assists_per_match=assists_per_match_comparison,
    )

    # Calculate summary statistics
    metrics = [
        market_value_comparison,
        goals_comparison,
        assists_comparison,
        goals_per_match_comparison,
        assists_per_match_comparison,
    ]

    player_1_wins = sum(1 for m in metrics if m.winner == "player_1")
    player_2_wins = sum(1 for m in metrics if m.winner == "player_2")
    ties = sum(1 for m in metrics if m.winner == "tie")

    summary = {
        "player_1_wins": player_1_wins,
        "player_2_wins": player_2_wins,
        "ties": ties,
    }

    # Convert players to schema
    player1_schema = Player.from_orm_model(player1)
    player2_schema = Player.from_orm_model(player2)

    return PlayerComparisonResponse(
        player_1=player1_schema,
        player_2=player2_schema,
        comparison=comparison,
        summary=summary,
    )


@router.get("/{player_id}", response_model=Player, summary="Get a specific player")
async def get_player(
    player_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a specific player by ID.

    Returns player details including computed properties like age and goals per match.
    """
    player = await player_crud.get(db, player_id=player_id)

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with ID {player_id} not found",
        )

    return Player.from_orm_model(player)


@router.put("/{player_id}", response_model=Player, summary="Update a player")
async def update_player(
    player_id: int,
    player_in: PlayerUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a player's information.

    All fields are optional. Only provided fields will be updated.
    """
    player = await player_crud.get(db, player_id=player_id)

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with ID {player_id} not found",
        )

    # Check if updating name would conflict with existing player
    update_data = player_in.model_dump(exclude_unset=True)
    if "first_name" in update_data or "last_name" in update_data:
        new_first_name = update_data.get("first_name", player.first_name)
        new_last_name = update_data.get("last_name", player.last_name)

        existing_player = await player_crud.get_by_name(
            db,
            first_name=new_first_name,
            last_name=new_last_name,
        )

        if existing_player and existing_player.id != player_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Player with name '{new_first_name} {new_last_name}' already exists",
            )

    updated_player = await player_crud.update(db, db_obj=player, obj_in=player_in)
    return Player.from_orm_model(updated_player)


@router.delete(
    "/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a player",
)
async def delete_player(
    player_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a player by ID.

    Returns 204 No Content on success.
    """
    player = await player_crud.delete(db, player_id=player_id)

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with ID {player_id} not found",
        )


@router.get("/club/{club_name}", response_model=PlayerList, summary="Get players by club")
async def get_players_by_club(
    club_name: str,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
) -> Any:
    """
    Get all players from a specific club.

    Returns players ordered by jersey number.
    """
    players, total = await player_crud.get_by_club(
        db,
        club_name=club_name,
        skip=skip,
        limit=limit,
    )

    player_schemas = [Player.from_orm_model(p) for p in players]

    return PlayerList(
        items=player_schemas,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=ceil(total / limit) if total > 0 else 0,
    )


@router.get("/top/scorers", response_model=list[Player], summary="Get top scorers")
async def get_top_scorers(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50, description="Number of top scorers to return"),
    position: Optional[PlayerPosition] = Query(None, description="Filter by position"),
) -> Any:
    """
    Get top scorers across all players.

    Optionally filter by position.
    """
    players = await player_crud.get_top_scorers(db, limit=limit, position=position)
    return [Player.from_orm_model(p) for p in players]


@router.get("/stats/overview", summary="Get player statistics overview")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get overall player statistics.

    Returns:
    - Total number of players
    - Total goals scored
    - Average player rating
    - Players count by position
    """
    stats = await player_crud.get_statistics(db)
    return stats
