"""
Integration tests for advanced player search endpoint (MVP v2).

Tests comprehensive search functionality with multiple filter parameters.
All endpoints require authentication.
"""
import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestAdvancedPlayerSearch:
    """Test suite for advanced player search functionality."""

    async def test_search_by_club_only(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test searching by club name only."""
        # Arrange - Create user and players
        user_data = {"email": "search1@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        # Create players with different clubs
        for player_data in sample_players_list[:3]:
            await client.post("/api/v1/players/", json=player_data)

        # Act - Search for Inter Miami players
        response = await client.post(
            "/api/v1/players/search/advanced",
            json={"club": "Inter Miami"},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["current_club"] == "Inter Miami"
        assert data[0]["last_name"] == "Messi"

    async def test_search_by_nationality_only(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test searching by nationality only."""
        # Arrange
        user_data = {"email": "search2@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        for player_data in sample_players_list:
            await client.post("/api/v1/players/", json=player_data)

        # Act - Search for Portuguese players
        response = await client.post(
            "/api/v1/players/search/advanced",
            json={"nationality": "Portugal"},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["nationality"] == "Portugal"
        assert data[0]["last_name"] == "Ronaldo"

    async def test_search_by_position_only(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test searching by position only."""
        # Arrange
        user_data = {"email": "search3@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        for player_data in sample_players_list:
            await client.post("/api/v1/players/", json=player_data)

        # Act - Search for goalkeepers
        response = await client.post(
            "/api/v1/players/search/advanced",
            json={"position": "goalkeeper"},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["position"] == "goalkeeper"
        assert data[0]["last_name"] == "Becker"

    async def test_search_with_multiple_parameters(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test searching with multiple filters simultaneously."""
        # Arrange
        user_data = {"email": "search4@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        for player_data in sample_players_list:
            await client.post("/api/v1/players/", json=player_data)

        # Act - Search for Liverpool midfielders
        response = await client.post(
            "/api/v1/players/search/advanced",
            json={
                "club": "Liverpool",
                "position": "goalkeeper"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["current_club"] == "Liverpool"
        assert data[0]["position"] == "goalkeeper"

    async def test_search_no_results(self, client: AsyncClient, sample_players_list: list[dict]):
        """Test search that yields no results."""
        # Arrange
        user_data = {"email": "search5@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        for player_data in sample_players_list:
            await client.post("/api/v1/players/", json=player_data)

        # Act - Search for non-existent combination
        response = await client.post(
            "/api/v1/players/search/advanced",
            json={
                "club": "Real Madrid",  # None of our test players are from Real Madrid
                "position": "forward"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    async def test_search_by_min_age(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test searching by minimum age."""
        # Arrange
        user_data = {"email": "search6@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        for player_data in sample_players_list:
            await client.post("/api/v1/players/", json=player_data)

        # Act - Search for players 38+ years old
        response = await client.post(
            "/api/v1/players/search/advanced",
            json={"min_age": 38},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Messi and Ronaldo should be 38+ based on sample data
        assert len(data) >= 1
        for player in data:
            assert player["age"] is None or player["age"] >= 38

    async def test_search_by_max_age(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test searching by maximum age."""
        # Arrange
        user_data = {"email": "search7@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        for player_data in sample_players_list:
            await client.post("/api/v1/players/", json=player_data)

        # Act - Search for players 35 and younger
        response = await client.post(
            "/api/v1/players/search/advanced",
            json={"max_age": 35},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for player in data:
            if player["age"] is not None:
                assert player["age"] <= 35

    async def test_search_by_age_range(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test searching by age range (min and max together)."""
        # Arrange
        user_data = {"email": "search8@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        for player_data in sample_players_list:
            await client.post("/api/v1/players/", json=player_data)

        # Act - Search for players between 25 and 35 years old
        response = await client.post(
            "/api/v1/players/search/advanced",
            json={"min_age": 25, "max_age": 35},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for player in data:
            if player["age"] is not None:
                assert 25 <= player["age"] <= 35

    async def test_search_age_range_validation(self, client: AsyncClient):
        """Test that max_age must be >= min_age."""
        # Arrange
        user_data = {"email": "search9@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        # Act - Try invalid age range
        response = await client.post(
            "/api/v1/players/search/advanced",
            json={"min_age": 35, "max_age": 25},  # Invalid: max < min
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_search_case_insensitive_club(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test that club search is case-insensitive."""
        # Arrange
        user_data = {"email": "search10@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        for player_data in sample_players_list:
            await client.post("/api/v1/players/", json=player_data)

        # Act - Search with different cases
        response_lower = await client.post(
            "/api/v1/players/search/advanced",
            json={"club": "inter miami"},
            headers={"Authorization": f"Bearer {token}"}
        )

        response_upper = await client.post(
            "/api/v1/players/search/advanced",
            json={"club": "INTER MIAMI"},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert - Both should return same results
        assert response_lower.status_code == status.HTTP_200_OK
        assert response_upper.status_code == status.HTTP_200_OK
        assert len(response_lower.json()) == len(response_upper.json())

    async def test_search_case_insensitive_nationality(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test that nationality search is case-insensitive."""
        # Arrange
        user_data = {"email": "search11@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        for player_data in sample_players_list:
            await client.post("/api/v1/players/", json=player_data)

        # Act
        response_lower = await client.post(
            "/api/v1/players/search/advanced",
            json={"nationality": "argentina"},
            headers={"Authorization": f"Bearer {token}"}
        )

        response_upper = await client.post(
            "/api/v1/players/search/advanced",
            json={"nationality": "ARGENTINA"},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response_lower.status_code == status.HTTP_200_OK
        assert response_upper.status_code == status.HTTP_200_OK
        assert len(response_lower.json()) == len(response_upper.json())

    async def test_search_empty_parameters(self, client: AsyncClient):
        """Test search with empty request body returns all players."""
        # Arrange
        user_data = {"email": "search12@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        # Act - Search with no filters
        response = await client.post(
            "/api/v1/players/search/advanced",
            json={},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        # Should return all players (or empty if none exist)


@pytest.mark.asyncio
class TestAdvancedSearchAuthentication:
    """Test suite for advanced search authentication requirements."""

    async def test_search_without_token(self, client: AsyncClient):
        """Test that advanced search requires authentication."""
        # Act
        response = await client.post(
            "/api/v1/players/search/advanced",
            json={"club": "Manchester City"}
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_search_with_invalid_token(self, client: AsyncClient):
        """Test that search rejects invalid tokens."""
        # Act
        response = await client.post(
            "/api/v1/players/search/advanced",
            json={"club": "Manchester City"},
            headers={"Authorization": "Bearer invalid_token_here"}
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
