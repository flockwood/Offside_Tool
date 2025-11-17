"""
Integration tests for Player API endpoints.

Tests the full API layer including routing, validation, error handling,
and database interaction.
"""
import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestPlayerEndpoints:
    """Test suite for Player API endpoints."""

    async def test_create_player_success(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test successful player creation via API."""
        # Act
        response = await client.post("/api/v1/players", json=sample_player_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["first_name"] == sample_player_data["first_name"]
        assert data["last_name"] == sample_player_data["last_name"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["full_name"] == f"{sample_player_data['first_name']} {sample_player_data['last_name']}"

    async def test_create_player_minimal_fields(
        self, client: AsyncClient, sample_player_data_minimal: dict
    ):
        """Test creating player with only required fields."""
        # Act
        response = await client.post("/api/v1/players", json=sample_player_data_minimal)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["goals"] == 0  # Default value
        assert data["assists"] == 0  # Default value

    async def test_create_player_duplicate_name(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test creating a player with duplicate name fails."""
        # Arrange - Create first player
        await client.post("/api/v1/players", json=sample_player_data)

        # Act - Try to create duplicate
        response = await client.post("/api/v1/players", json=sample_player_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

    async def test_create_player_invalid_data(self, client: AsyncClient):
        """Test creating player with invalid data."""
        invalid_data = {
            "first_name": "",  # Empty
            "last_name": "Test",
            "position": "invalid_position",  # Invalid enum
        }

        # Act
        response = await client.post("/api/v1/players", json=invalid_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_player_missing_required_fields(self, client: AsyncClient):
        """Test creating player without required fields."""
        incomplete_data = {"first_name": "Test"}  # Missing last_name and position

        # Act
        response = await client.post("/api/v1/players", json=incomplete_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_get_player_by_id(self, client: AsyncClient, sample_player_data: dict):
        """Test retrieving a player by ID."""
        # Arrange
        create_response = await client.post("/api/v1/players", json=sample_player_data)
        player_id = create_response.json()["id"]

        # Act
        response = await client.get(f"/api/v1/players/{player_id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == player_id
        assert data["first_name"] == sample_player_data["first_name"]

    async def test_get_nonexistent_player(self, client: AsyncClient):
        """Test retrieving a player that doesn't exist."""
        # Act
        response = await client.get("/api/v1/players/99999")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    async def test_list_players_empty(self, client: AsyncClient):
        """Test listing players when database is empty."""
        # Act
        response = await client.get("/api/v1/players")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1
        assert data["total_pages"] == 0

    async def test_list_players(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test listing multiple players."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act
        response = await client.get("/api/v1/players")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == len(sample_players_list)
        assert len(data["items"]) == len(sample_players_list)

    async def test_list_players_pagination(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test pagination of player list."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act
        response_page1 = await client.get("/api/v1/players?skip=0&limit=2")
        response_page2 = await client.get("/api/v1/players?skip=2&limit=2")

        # Assert
        assert response_page1.status_code == status.HTTP_200_OK
        assert response_page2.status_code == status.HTTP_200_OK

        data_page1 = response_page1.json()
        data_page2 = response_page2.json()

        assert len(data_page1["items"]) == 2
        assert len(data_page2["items"]) == 2
        assert data_page1["total"] == len(sample_players_list)
        assert data_page1["page"] == 1
        assert data_page2["page"] == 2

    async def test_filter_players_by_position(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test filtering players by position."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act
        response = await client.get("/api/v1/players?position=forward")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2  # Messi and Ronaldo
        assert all(item["position"] == "forward" for item in data["items"])

    async def test_filter_players_by_nationality(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test filtering players by nationality."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act
        response = await client.get("/api/v1/players?nationality=Argentina")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1  # Only Messi
        assert data["items"][0]["nationality"] == "Argentina"

    async def test_filter_players_by_club(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test filtering players by current club."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act
        response = await client.get("/api/v1/players?current_club=Liverpool")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2  # Van Dijk and Alisson
        assert all("Liverpool" in item["current_club"] for item in data["items"])

    async def test_filter_players_by_min_rating(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test filtering players by minimum rating."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act
        response = await client.get("/api/v1/players?min_rating=9.0")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2  # Messi and Ronaldo
        assert all(item["rating"] >= 9.0 for item in data["items"])

    async def test_search_players(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test searching players by name."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act
        response = await client.get("/api/v1/players?search=Messi")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert "Messi" in data["items"][0]["last_name"]

    async def test_update_player(self, client: AsyncClient, sample_player_data: dict):
        """Test updating a player's information."""
        # Arrange
        create_response = await client.post("/api/v1/players", json=sample_player_data)
        player_id = create_response.json()["id"]

        update_data = {
            "goals": 801,
            "assists": 351,
            "current_club": "PSG",
            "rating": 9.6,
        }

        # Act
        response = await client.put(f"/api/v1/players/{player_id}", json=update_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["goals"] == 801
        assert data["assists"] == 351
        assert data["current_club"] == "PSG"
        assert data["rating"] == 9.6
        # Original data should be preserved
        assert data["first_name"] == sample_player_data["first_name"]

    async def test_update_nonexistent_player(self, client: AsyncClient):
        """Test updating a player that doesn't exist."""
        update_data = {"goals": 100}

        # Act
        response = await client.put("/api/v1/players/99999", json=update_data)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_player_duplicate_name(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test updating player name to duplicate another player's name."""
        # Arrange
        player1_response = await client.post(
            "/api/v1/players", json=sample_players_list[0]
        )
        player2_response = await client.post(
            "/api/v1/players", json=sample_players_list[1]
        )

        player2_id = player2_response.json()["id"]

        # Try to update player2 with player1's name
        update_data = {
            "first_name": sample_players_list[0]["first_name"],
            "last_name": sample_players_list[0]["last_name"],
        }

        # Act
        response = await client.put(f"/api/v1/players/{player2_id}", json=update_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

    async def test_delete_player(self, client: AsyncClient, sample_player_data: dict):
        """Test deleting a player."""
        # Arrange
        create_response = await client.post("/api/v1/players", json=sample_player_data)
        player_id = create_response.json()["id"]

        # Act
        delete_response = await client.delete(f"/api/v1/players/{player_id}")

        # Assert
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify player is deleted
        get_response = await client.get(f"/api/v1/players/{player_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_nonexistent_player(self, client: AsyncClient):
        """Test deleting a player that doesn't exist."""
        # Act
        response = await client.delete("/api/v1/players/99999")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_players_by_club_endpoint(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test the get players by club endpoint."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act
        response = await client.get("/api/v1/players/club/Liverpool")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2  # Van Dijk and Alisson
        assert all("Liverpool" in item["current_club"] for item in data["items"])

    async def test_get_top_scorers(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test getting top scorers."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act
        response = await client.get("/api/v1/players/top/scorers?limit=3")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        # Should be sorted by goals descending
        assert data[0]["goals"] >= data[1]["goals"] >= data[2]["goals"]
        # Ronaldo should be first
        assert data[0]["last_name"] == "Ronaldo"

    async def test_get_top_scorers_by_position(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test getting top scorers filtered by position."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act
        response = await client.get("/api/v1/players/top/scorers?position=midfielder")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1  # Only De Bruyne
        assert all(item["position"] == "midfielder" for item in data)

    async def test_get_statistics_overview(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test getting statistics overview."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act
        response = await client.get("/api/v1/players/stats/overview")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_players"] == len(sample_players_list)
        assert data["total_goals"] > 0
        assert data["average_rating"] > 0
        assert "players_by_position" in data
        assert data["players_by_position"]["forward"] == 2
        assert data["players_by_position"]["goalkeeper"] == 1

    async def test_pagination_boundary_conditions(self, client: AsyncClient):
        """Test pagination with boundary conditions."""
        # Create just 1 player
        sample_data = {
            "first_name": "Test",
            "last_name": "Player",
            "position": "forward",
        }
        await client.post("/api/v1/players", json=sample_data)

        # Test with limit larger than available records
        response = await client.get("/api/v1/players?skip=0&limit=100")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

        # Test with skip beyond available records
        response = await client.get("/api/v1/players?skip=100&limit=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 0

    async def test_invalid_pagination_parameters(self, client: AsyncClient):
        """Test API with invalid pagination parameters."""
        # Negative skip
        response = await client.get("/api/v1/players?skip=-1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Limit exceeding maximum
        response = await client.get("/api/v1/players?limit=1000")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_computed_fields_in_response(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test that computed fields are included in API response."""
        # Arrange
        response = await client.post("/api/v1/players", json=sample_player_data)

        # Assert
        data = response.json()
        assert "full_name" in data
        assert "age" in data
        assert "goals_per_match" in data
        assert "assists_per_match" in data

        expected_goals_per_match = round(
            sample_player_data["goals"] / sample_player_data["matches_played"], 2
        )
        assert data["goals_per_match"] == expected_goals_per_match


@pytest.mark.asyncio
class TestSystemEndpoints:
    """Test system health and info endpoints."""

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns API information."""
        # Act
        response = await client.get("/")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "api" in data

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        # Act
        response = await client.get("/health")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    async def test_info_endpoint(self, client: AsyncClient):
        """Test info endpoint returns system information."""
        # Act
        response = await client.get("/info")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "project_name" in data
        assert "version" in data
        assert "environment" in data
        assert "database" in data
        assert "redis" in data
        assert "features" in data
