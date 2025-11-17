"""
CRUD operations for Player model using SQLAlchemy 2.0 async patterns.
"""
from typing import Optional, List, Any
from datetime import date, timedelta
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player import Player, PlayerPosition
from app.schemas.player import PlayerCreate, PlayerUpdate, PlayerSearch


class CRUDPlayer:
    """
    CRUD operations for Player model.

    Provides async methods for Create, Read, Update, and Delete operations.
    """

    async def get(self, db: AsyncSession, player_id: int) -> Optional[Player]:
        """
        Get a player by ID.

        Args:
            db: Database session
            player_id: Player ID

        Returns:
            Player object or None if not found
        """
        result = await db.execute(select(Player).where(Player.id == player_id))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 20,
        position: Optional[PlayerPosition] = None,
        nationality: Optional[str] = None,
        current_club: Optional[str] = None,
        min_rating: Optional[float] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Player], int]:
        """
        Get multiple players with filtering and pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            position: Filter by player position
            nationality: Filter by nationality
            current_club: Filter by current club
            min_rating: Filter by minimum rating
            search: Search in first_name, last_name, or current_club

        Returns:
            Tuple of (list of players, total count)
        """
        # Build base query
        query = select(Player)
        count_query = select(func.count()).select_from(Player)

        # Apply filters
        filters = []

        if position:
            filters.append(Player.position == position)

        if nationality:
            filters.append(Player.nationality.ilike(f"%{nationality}%"))

        if current_club:
            filters.append(Player.current_club.ilike(f"%{current_club}%"))

        if min_rating is not None:
            filters.append(Player.rating >= min_rating)

        if search:
            search_filter = or_(
                Player.first_name.ilike(f"%{search}%"),
                Player.last_name.ilike(f"%{search}%"),
                Player.current_club.ilike(f"%{search}%"),
            )
            filters.append(search_filter)

        # Apply all filters
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        query = query.order_by(Player.id).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        players = result.scalars().all()

        return list(players), total

    async def create(self, db: AsyncSession, *, obj_in: PlayerCreate) -> Player:
        """
        Create a new player.

        Args:
            db: Database session
            obj_in: Player creation schema

        Returns:
            Created player object
        """
        db_obj = Player(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Player,
        obj_in: PlayerUpdate | dict[str, Any],
    ) -> Player:
        """
        Update a player.

        Args:
            db: Database session
            db_obj: Existing player object
            obj_in: Player update schema or dictionary

        Returns:
            Updated player object
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, player_id: int) -> Optional[Player]:
        """
        Delete a player.

        Args:
            db: Database session
            player_id: Player ID to delete

        Returns:
            Deleted player object or None if not found
        """
        player = await self.get(db, player_id)
        if player:
            await db.delete(player)
            await db.commit()
        return player

    async def get_by_name(
        self,
        db: AsyncSession,
        *,
        first_name: str,
        last_name: str,
    ) -> Optional[Player]:
        """
        Get a player by first and last name.

        Args:
            db: Database session
            first_name: Player's first name
            last_name: Player's last name

        Returns:
            Player object or None if not found
        """
        result = await db.execute(
            select(Player).where(
                and_(
                    Player.first_name.ilike(first_name),
                    Player.last_name.ilike(last_name),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_club(
        self,
        db: AsyncSession,
        *,
        club_name: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Player], int]:
        """
        Get all players from a specific club.

        Args:
            db: Database session
            club_name: Club name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of players, total count)
        """
        query = select(Player).where(Player.current_club.ilike(f"%{club_name}%"))
        count_query = select(func.count()).select_from(Player).where(
            Player.current_club.ilike(f"%{club_name}%")
        )

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        query = query.order_by(Player.jersey_number).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        players = result.scalars().all()

        return list(players), total

    async def get_top_scorers(
        self,
        db: AsyncSession,
        *,
        limit: int = 10,
        position: Optional[PlayerPosition] = None,
    ) -> List[Player]:
        """
        Get top scorers.

        Args:
            db: Database session
            limit: Maximum number of players to return
            position: Filter by position (optional)

        Returns:
            List of top scoring players
        """
        query = select(Player).order_by(Player.goals.desc())

        if position:
            query = query.where(Player.position == position)

        query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def search_players_by_name(
        self,
        db: AsyncSession,
        *,
        name_query: str,
    ) -> List[Player]:
        """
        Search for players by name (case-insensitive).

        Searches in both first_name and last_name fields.

        Args:
            db: Database session
            name_query: Name search query

        Returns:
            List of matching players
        """
        # Search in both first and last names
        query = select(Player).where(
            or_(
                Player.first_name.ilike(f"%{name_query}%"),
                Player.last_name.ilike(f"%{name_query}%"),
            )
        ).order_by(Player.last_name, Player.first_name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_statistics(self, db: AsyncSession) -> dict[str, Any]:
        """
        Get overall player statistics.

        Args:
            db: Database session

        Returns:
            Dictionary with various statistics
        """
        # Total players
        total_players_result = await db.execute(select(func.count()).select_from(Player))
        total_players = total_players_result.scalar_one()

        # Total goals
        total_goals_result = await db.execute(select(func.sum(Player.goals)))
        total_goals = total_goals_result.scalar_one() or 0

        # Average rating
        avg_rating_result = await db.execute(select(func.avg(Player.rating)))
        avg_rating = avg_rating_result.scalar_one()

        # Players by position
        position_counts = {}
        for position in PlayerPosition:
            count_result = await db.execute(
                select(func.count()).select_from(Player).where(Player.position == position)
            )
            position_counts[position.value] = count_result.scalar_one()

        return {
            "total_players": total_players,
            "total_goals": int(total_goals),
            "average_rating": round(float(avg_rating), 2) if avg_rating else 0,
            "players_by_position": position_counts,
        }

    async def advanced_search_players(
        self,
        db: AsyncSession,
        search_params: PlayerSearch
    ) -> List[Player]:
        """
        Advanced search for players with multiple optional filters.

        Dynamically builds a query based on provided search parameters.
        For age filtering, calculates date of birth range from min_age and max_age.

        Args:
            db: Database session
            search_params: PlayerSearch schema with optional filter parameters

        Returns:
            List of players matching all provided criteria
        """
        # Start with base query
        query = select(Player)

        # Build dynamic filters
        filters = []

        # Filter by club (case-insensitive)
        if search_params.club is not None:
            filters.append(func.lower(Player.current_club) == search_params.club.lower())

        # Filter by nationality (case-insensitive)
        if search_params.nationality is not None:
            filters.append(func.lower(Player.nationality) == search_params.nationality.lower())

        # Filter by position
        if search_params.position is not None:
            filters.append(Player.position == search_params.position)

        # Filter by age range
        # Calculate date of birth range from age constraints
        today = date.today()

        if search_params.min_age is not None:
            # min_age means player must be AT LEAST this old
            # So date_of_birth must be ON OR BEFORE this date
            max_dob = date(today.year - search_params.min_age, today.month, today.day)
            filters.append(Player.date_of_birth <= max_dob)

        if search_params.max_age is not None:
            # max_age means player must be AT MOST this old
            # So date_of_birth must be ON OR AFTER this date
            # Add 1 year because we want the player to be exactly max_age or younger
            min_dob = date(today.year - search_params.max_age - 1, today.month, today.day) + timedelta(days=1)
            filters.append(Player.date_of_birth >= min_dob)

        # Apply all filters
        if filters:
            query = query.where(and_(*filters))

        # Execute query
        result = await db.execute(query.order_by(Player.last_name, Player.first_name))
        players = result.scalars().all()

        return list(players)


# Create a singleton instance
player = CRUDPlayer()
