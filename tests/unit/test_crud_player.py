"""
Unit tests for Player CRUD operations.

Tests the business logic in app/crud/player.py without involving the API layer.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.player import player as player_crud
from app.schemas.player import PlayerCreate, PlayerUpdate
from app.models.player import Player, PlayerPosition


@pytest.mark.asyncio
class TestPlayerCRUD:
    """Test suite for Player CRUD operations."""

    async def test_create_player(self, test_session: AsyncSession, sample_player_data: dict):
        """Test creating a new player."""
        # Arrange
        player_in = PlayerCreate(**sample_player_data)

        # Act
        created_player = await player_crud.create(test_session, obj_in=player_in)

        # Assert
        assert created_player.id is not None
        assert created_player.first_name == sample_player_data["first_name"]
        assert created_player.last_name == sample_player_data["last_name"]
        assert created_player.position == PlayerPosition(sample_player_data["position"])
        assert created_player.goals == sample_player_data["goals"]

    async def test_create_player_minimal(
        self, test_session: AsyncSession, sample_player_data_minimal: dict
    ):
        """Test creating a player with only required fields."""
        # Arrange
        player_in = PlayerCreate(**sample_player_data_minimal)

        # Act
        created_player = await player_crud.create(test_session, obj_in=player_in)

        # Assert
        assert created_player.id is not None
        assert created_player.first_name == sample_player_data_minimal["first_name"]
        assert created_player.last_name == sample_player_data_minimal["last_name"]
        assert created_player.goals == 0  # Default value
        assert created_player.assists == 0  # Default value

    async def test_get_player_by_id(self, test_session: AsyncSession, sample_player_data: dict):
        """Test retrieving a player by ID."""
        # Arrange
        player_in = PlayerCreate(**sample_player_data)
        created_player = await player_crud.create(test_session, obj_in=player_in)

        # Act
        retrieved_player = await player_crud.get(test_session, player_id=created_player.id)

        # Assert
        assert retrieved_player is not None
        assert retrieved_player.id == created_player.id
        assert retrieved_player.first_name == created_player.first_name

    async def test_get_nonexistent_player(self, test_session: AsyncSession):
        """Test retrieving a player that doesn't exist."""
        # Act
        player = await player_crud.get(test_session, player_id=99999)

        # Assert
        assert player is None

    async def test_get_player_by_name(
        self, test_session: AsyncSession, sample_player_data: dict
    ):
        """Test retrieving a player by first and last name."""
        # Arrange
        player_in = PlayerCreate(**sample_player_data)
        await player_crud.create(test_session, obj_in=player_in)

        # Act
        retrieved_player = await player_crud.get_by_name(
            test_session,
            first_name=sample_player_data["first_name"],
            last_name=sample_player_data["last_name"],
        )

        # Assert
        assert retrieved_player is not None
        assert retrieved_player.first_name == sample_player_data["first_name"]
        assert retrieved_player.last_name == sample_player_data["last_name"]

    async def test_get_multiple_players(
        self, test_session: AsyncSession, sample_players_list: list[dict]
    ):
        """Test retrieving multiple players with pagination."""
        # Arrange
        for player_data in sample_players_list:
            player_in = PlayerCreate(**player_data)
            await player_crud.create(test_session, obj_in=player_in)

        # Act
        players, total = await player_crud.get_multi(test_session, skip=0, limit=10)

        # Assert
        assert total == len(sample_players_list)
        assert len(players) == len(sample_players_list)

    async def test_get_players_with_pagination(
        self, test_session: AsyncSession, sample_players_list: list[dict]
    ):
        """Test pagination of player list."""
        # Arrange
        for player_data in sample_players_list:
            player_in = PlayerCreate(**player_data)
            await player_crud.create(test_session, obj_in=player_in)

        # Act
        players_page1, total = await player_crud.get_multi(test_session, skip=0, limit=2)
        players_page2, _ = await player_crud.get_multi(test_session, skip=2, limit=2)

        # Assert
        assert total == len(sample_players_list)
        assert len(players_page1) == 2
        assert len(players_page2) == 2
        assert players_page1[0].id != players_page2[0].id

    async def test_filter_players_by_position(
        self, test_session: AsyncSession, sample_players_list: list[dict]
    ):
        """Test filtering players by position."""
        # Arrange
        for player_data in sample_players_list:
            player_in = PlayerCreate(**player_data)
            await player_crud.create(test_session, obj_in=player_in)

        # Act
        forwards, total = await player_crud.get_multi(
            test_session, position=PlayerPosition.FORWARD
        )

        # Assert
        assert total == 2  # Messi and Ronaldo are forwards
        assert all(p.position == PlayerPosition.FORWARD for p in forwards)

    async def test_filter_players_by_nationality(
        self, test_session: AsyncSession, sample_players_list: list[dict]
    ):
        """Test filtering players by nationality."""
        # Arrange
        for player_data in sample_players_list:
            player_in = PlayerCreate(**player_data)
            await player_crud.create(test_session, obj_in=player_in)

        # Act
        argentinian_players, total = await player_crud.get_multi(
            test_session, nationality="Argentina"
        )

        # Assert
        assert total == 1  # Only Messi
        assert argentinian_players[0].nationality == "Argentina"

    async def test_filter_players_by_club(
        self, test_session: AsyncSession, sample_players_list: list[dict]
    ):
        """Test filtering players by current club."""
        # Arrange
        for player_data in sample_players_list:
            player_in = PlayerCreate(**player_data)
            await player_crud.create(test_session, obj_in=player_in)

        # Act
        liverpool_players, total = await player_crud.get_by_club(
            test_session, club_name="Liverpool"
        )

        # Assert
        assert total == 2  # Van Dijk and Alisson
        assert all("Liverpool" in p.current_club for p in liverpool_players)

    async def test_search_players(
        self, test_session: AsyncSession, sample_players_list: list[dict]
    ):
        """Test searching players by name or club."""
        # Arrange
        for player_data in sample_players_list:
            player_in = PlayerCreate(**player_data)
            await player_crud.create(test_session, obj_in=player_in)

        # Act
        search_results, total = await player_crud.get_multi(test_session, search="Messi")

        # Assert
        assert total == 1
        assert "Messi" in search_results[0].last_name

    async def test_filter_by_min_rating(
        self, test_session: AsyncSession, sample_players_list: list[dict]
    ):
        """Test filtering players by minimum rating."""
        # Arrange
        for player_data in sample_players_list:
            player_in = PlayerCreate(**player_data)
            await player_crud.create(test_session, obj_in=player_in)

        # Act
        top_players, total = await player_crud.get_multi(test_session, min_rating=9.0)

        # Assert
        assert total == 2  # Messi and Ronaldo have rating >= 9.0
        assert all(p.rating >= 9.0 for p in top_players)

    async def test_update_player(self, test_session: AsyncSession, sample_player_data: dict):
        """Test updating a player's information."""
        # Arrange
        player_in = PlayerCreate(**sample_player_data)
        created_player = await player_crud.create(test_session, obj_in=player_in)

        update_data = PlayerUpdate(
            goals=801, assists=351, matches_played=1001, rating=9.6
        )

        # Act
        updated_player = await player_crud.update(
            test_session, db_obj=created_player, obj_in=update_data
        )

        # Assert
        assert updated_player.id == created_player.id
        assert updated_player.goals == 801
        assert updated_player.assists == 351
        assert updated_player.rating == 9.6

    async def test_update_player_partial(
        self, test_session: AsyncSession, sample_player_data: dict
    ):
        """Test partial update of player."""
        # Arrange
        player_in = PlayerCreate(**sample_player_data)
        created_player = await player_crud.create(test_session, obj_in=player_in)

        update_data = PlayerUpdate(current_club="PSG")

        # Act
        updated_player = await player_crud.update(
            test_session, db_obj=created_player, obj_in=update_data
        )

        # Assert
        assert updated_player.current_club == "PSG"
        # Other fields should remain unchanged
        assert updated_player.goals == created_player.goals
        assert updated_player.first_name == created_player.first_name

    async def test_delete_player(self, test_session: AsyncSession, sample_player_data: dict):
        """Test deleting a player."""
        # Arrange
        player_in = PlayerCreate(**sample_player_data)
        created_player = await player_crud.create(test_session, obj_in=player_in)
        player_id = created_player.id

        # Act
        deleted_player = await player_crud.delete(test_session, player_id=player_id)

        # Assert
        assert deleted_player is not None
        assert deleted_player.id == player_id

        # Verify player is actually deleted
        retrieved_player = await player_crud.get(test_session, player_id=player_id)
        assert retrieved_player is None

    async def test_delete_nonexistent_player(self, test_session: AsyncSession):
        """Test deleting a player that doesn't exist."""
        # Act
        result = await player_crud.delete(test_session, player_id=99999)

        # Assert
        assert result is None

    async def test_get_top_scorers(
        self, test_session: AsyncSession, sample_players_list: list[dict]
    ):
        """Test getting top scorers."""
        # Arrange
        for player_data in sample_players_list:
            player_in = PlayerCreate(**player_data)
            await player_crud.create(test_session, obj_in=player_in)

        # Act
        top_scorers = await player_crud.get_top_scorers(test_session, limit=3)

        # Assert
        assert len(top_scorers) == 3
        # Should be ordered by goals (descending)
        assert top_scorers[0].goals >= top_scorers[1].goals >= top_scorers[2].goals
        # Ronaldo should be first (850 goals)
        assert top_scorers[0].last_name == "Ronaldo"

    async def test_get_top_scorers_by_position(
        self, test_session: AsyncSession, sample_players_list: list[dict]
    ):
        """Test getting top scorers filtered by position."""
        # Arrange
        for player_data in sample_players_list:
            player_in = PlayerCreate(**player_data)
            await player_crud.create(test_session, obj_in=player_in)

        # Act
        top_forwards = await player_crud.get_top_scorers(
            test_session, limit=5, position=PlayerPosition.FORWARD
        )

        # Assert
        assert len(top_forwards) == 2  # Only 2 forwards in sample data
        assert all(p.position == PlayerPosition.FORWARD for p in top_forwards)

    async def test_get_statistics(
        self, test_session: AsyncSession, sample_players_list: list[dict]
    ):
        """Test getting overall player statistics."""
        # Arrange
        for player_data in sample_players_list:
            player_in = PlayerCreate(**player_data)
            await player_crud.create(test_session, obj_in=player_in)

        # Act
        stats = await player_crud.get_statistics(test_session)

        # Assert
        assert stats["total_players"] == len(sample_players_list)
        assert stats["total_goals"] > 0
        assert stats["average_rating"] > 0
        assert "players_by_position" in stats
        assert stats["players_by_position"]["forward"] == 2
        assert stats["players_by_position"]["goalkeeper"] == 1


@pytest.mark.asyncio
class TestPlayerModelProperties:
    """Test computed properties of the Player model."""

    async def test_player_full_name(
        self, test_session: AsyncSession, sample_player_data: dict
    ):
        """Test full_name computed property."""
        # Arrange
        player_in = PlayerCreate(**sample_player_data)
        player = await player_crud.create(test_session, obj_in=player_in)

        # Act
        full_name = player.full_name

        # Assert
        assert full_name == f"{sample_player_data['first_name']} {sample_player_data['last_name']}"

    async def test_player_age_calculation(
        self, test_session: AsyncSession, sample_player_data: dict
    ):
        """Test age calculation from date_of_birth."""
        # Arrange
        player_in = PlayerCreate(**sample_player_data)
        player = await player_crud.create(test_session, obj_in=player_in)

        # Act
        age = player.age

        # Assert
        assert age is not None
        assert age > 0
        assert age < 100  # Sanity check

    async def test_goals_per_match_calculation(
        self, test_session: AsyncSession, sample_player_data: dict
    ):
        """Test goals_per_match calculation."""
        # Arrange
        player_in = PlayerCreate(**sample_player_data)
        player = await player_crud.create(test_session, obj_in=player_in)

        # Act
        goals_per_match = player.goals_per_match

        # Assert
        expected = round(sample_player_data["goals"] / sample_player_data["matches_played"], 2)
        assert goals_per_match == expected

    async def test_assists_per_match_calculation(
        self, test_session: AsyncSession, sample_player_data: dict
    ):
        """Test assists_per_match calculation."""
        # Arrange
        player_in = PlayerCreate(**sample_player_data)
        player = await player_crud.create(test_session, obj_in=player_in)

        # Act
        assists_per_match = player.assists_per_match

        # Assert
        expected = round(sample_player_data["assists"] / sample_player_data["matches_played"], 2)
        assert assists_per_match == expected

    async def test_zero_matches_played(self, test_session: AsyncSession):
        """Test computed properties when matches_played is 0."""
        # Arrange
        player_in = PlayerCreate(
            first_name="New",
            last_name="Player",
            position="forward",
            matches_played=0,
            goals=0,
            assists=0,
        )
        player = await player_crud.create(test_session, obj_in=player_in)

        # Act
        goals_per_match = player.goals_per_match
        assists_per_match = player.assists_per_match

        # Assert
        assert goals_per_match == 0.0
        assert assists_per_match == 0.0
