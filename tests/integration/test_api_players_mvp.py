"""
Integration tests for MVP features: Player Search and Comparison endpoints.

Tests the /search and /compare endpoints with comprehensive scenarios.
"""
import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestPlayerSearchEndpoint:
    """Test suite for the player search endpoint."""

    async def test_search_returns_multiple_players(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test searching returns multiple matching players."""
        # Arrange - Create test players
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act - Search for common name pattern
        response = await client.get("/api/v1/players/search?name=a")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 1  # Multiple players have 'a' in their names
        # Verify all results contain 'a' in first or last name
        for player in data:
            name_lower = (player["first_name"] + player["last_name"]).lower()
            assert "a" in name_lower

    async def test_search_returns_single_player(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test searching returns a single player when query is specific."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act - Search for specific unique name
        response = await client.get("/api/v1/players/search?name=Messi")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["last_name"] == "Messi"
        assert data[0]["first_name"] == "Lionel"

    async def test_search_returns_empty_list_no_matches(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test searching returns empty list when no players match."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act - Search for non-existent name
        response = await client.get("/api/v1/players/search?name=Zlatan")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_search_with_partial_name(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test searching with partial name returns correct matches."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act - Search for partial name "Ron" (should match Ronaldo)
        response = await client.get("/api/v1/players/search?name=Ron")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert "Ron" in data[0]["last_name"]

    async def test_search_case_insensitive(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test that search is case-insensitive."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act - Search with different cases
        response_lower = await client.get("/api/v1/players/search?name=messi")
        response_upper = await client.get("/api/v1/players/search?name=MESSI")
        response_mixed = await client.get("/api/v1/players/search?name=MeSsI")

        # Assert - All should return same results
        assert response_lower.status_code == status.HTTP_200_OK
        assert response_upper.status_code == status.HTTP_200_OK
        assert response_mixed.status_code == status.HTTP_200_OK

        data_lower = response_lower.json()
        data_upper = response_upper.json()
        data_mixed = response_mixed.json()

        assert len(data_lower) == len(data_upper) == len(data_mixed) == 1
        assert data_lower[0]["id"] == data_upper[0]["id"] == data_mixed[0]["id"]

    async def test_search_first_and_last_names(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test that search works on both first and last names."""
        # Arrange
        for player_data in sample_players_list:
            await client.post("/api/v1/players", json=player_data)

        # Act - Search by first name
        response_first = await client.get("/api/v1/players/search?name=Kevin")
        # Search by last name
        response_last = await client.get("/api/v1/players/search?name=Bruyne")

        # Assert - Both should find Kevin De Bruyne
        assert response_first.status_code == status.HTTP_200_OK
        assert response_last.status_code == status.HTTP_200_OK

        data_first = response_first.json()
        data_last = response_last.json()

        assert len(data_first) == 1
        assert len(data_last) == 1
        assert data_first[0]["first_name"] == "Kevin"
        assert data_last[0]["last_name"] == "De Bruyne"

    async def test_search_missing_name_parameter(self, client: AsyncClient):
        """Test that search without name parameter returns validation error."""
        # Act
        response = await client.get("/api/v1/players/search")

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_search_empty_database(self, client: AsyncClient):
        """Test searching when database is empty returns empty list."""
        # Act
        response = await client.get("/api/v1/players/search?name=anyone")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    async def test_search_with_special_characters(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test searching handles special characters gracefully."""
        # Arrange
        await client.post("/api/v1/players", json=sample_player_data)

        # Act - Search with special characters
        response = await client.get("/api/v1/players/search?name=M@ss!")

        # Assert - Should not crash, just return no results
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_search_without_token_returns_401(self, client: AsyncClient):
        """Test that accessing search endpoint without authentication returns 401."""
        # Act - Try to search without providing authentication token
        response = await client.get("/api/v1/players/search?name=Messi")

        # Assert - Should return 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    async def test_search_with_valid_token_returns_200(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test that accessing search endpoint with valid token returns 200."""
        # Arrange - Create a user and get authentication token
        user_data = {
            "email": "testuser@example.com",
            "password": "securepassword123"
        }
        await client.post("/api/v1/users/", json=user_data)

        # Login to get token
        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        # Create a player to search for
        await client.post("/api/v1/players", json=sample_player_data)

        # Act - Search with valid token
        response = await client.get(
            "/api/v1/players/search?name=Messi",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert - Should return 200 OK with results
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
class TestPlayerComparisonEndpoint:
    """Test suite for the player comparison endpoint."""

    async def test_compare_player1_clear_winner(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test comparison where player 1 dominates most metrics."""
        # Arrange - Create two players where Messi is clearly better
        messi_data = sample_players_list[0]  # Messi: 800 goals, 350 assists
        van_dijk_data = sample_players_list[3]  # Van Dijk: 25 goals, 10 assists (defender)

        messi_response = await client.post("/api/v1/players", json=messi_data)
        van_dijk_response = await client.post("/api/v1/players", json=van_dijk_data)

        messi_id = messi_response.json()["id"]
        van_dijk_id = van_dijk_response.json()["id"]

        # Act
        response = await client.get(
            f"/api/v1/players/compare?player_id_1={messi_id}&player_id_2={van_dijk_id}"
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify structure
        assert "player_1" in data
        assert "player_2" in data
        assert "comparison" in data
        assert "summary" in data

        # Verify players
        assert data["player_1"]["id"] == messi_id
        assert data["player_2"]["id"] == van_dijk_id

        # Verify comparison metrics
        comparison = data["comparison"]
        assert "goals" in comparison
        assert "assists" in comparison
        assert "goals_per_match" in comparison
        assert "assists_per_match" in comparison

        # Messi should win goals and assists
        assert comparison["goals"]["winner"] == "player_1"
        assert comparison["assists"]["winner"] == "player_1"

        # Verify summary - player 1 should have more wins
        summary = data["summary"]
        assert summary["player_1_wins"] > summary["player_2_wins"]

    async def test_compare_player2_clear_winner(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test comparison where player 2 wins most metrics."""
        # Arrange - Create players where Ronaldo (player 2) has more goals
        messi_data = sample_players_list[0].copy()  # 800 goals
        ronaldo_data = sample_players_list[1].copy()  # 850 goals

        messi_response = await client.post("/api/v1/players", json=messi_data)
        ronaldo_response = await client.post("/api/v1/players", json=ronaldo_data)

        messi_id = messi_response.json()["id"]
        ronaldo_id = ronaldo_response.json()["id"]

        # Act - Compare with Ronaldo as player_2
        response = await client.get(
            f"/api/v1/players/compare?player_id_1={messi_id}&player_id_2={ronaldo_id}"
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Ronaldo should win goals
        assert data["comparison"]["goals"]["winner"] == "player_2"

        # Verify summary exists
        assert "player_1_wins" in data["summary"]
        assert "player_2_wins" in data["summary"]
        assert "ties" in data["summary"]

    async def test_compare_with_tied_stats(
        self, client: AsyncClient
    ):
        """Test comparison where some stats are tied."""
        # Arrange - Create two identical players except for names
        player1_data = {
            "first_name": "Player",
            "last_name": "One",
            "position": "forward",
            "goals": 100,
            "assists": 50,
            "matches_played": 100,
            "market_value_euros": 50000000,
        }

        player2_data = {
            "first_name": "Player",
            "last_name": "Two",
            "position": "forward",
            "goals": 100,  # Same
            "assists": 50,  # Same
            "matches_played": 100,  # Same
            "market_value_euros": 50000000,  # Same
        }

        response1 = await client.post("/api/v1/players", json=player1_data)
        response2 = await client.post("/api/v1/players", json=player2_data)

        player1_id = response1.json()["id"]
        player2_id = response2.json()["id"]

        # Act
        response = await client.get(
            f"/api/v1/players/compare?player_id_1={player1_id}&player_id_2={player2_id}"
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        comparison = data["comparison"]

        # All metrics should be tied
        assert comparison["goals"]["winner"] == "tie"
        assert comparison["assists"]["winner"] == "tie"
        assert comparison["goals_per_match"]["winner"] == "tie"
        assert comparison["assists_per_match"]["winner"] == "tie"
        assert comparison["market_value_euros"]["winner"] == "tie"

        # Summary should show all ties
        assert data["summary"]["ties"] == 5
        assert data["summary"]["player_1_wins"] == 0
        assert data["summary"]["player_2_wins"] == 0

    async def test_compare_player1_not_found(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test comparison when player 1 doesn't exist."""
        # Arrange - Create only player 2
        response2 = await client.post("/api/v1/players", json=sample_player_data)
        player2_id = response2.json()["id"]

        # Act - Try to compare with non-existent player 1
        response = await client.get(
            f"/api/v1/players/compare?player_id_1=99999&player_id_2={player2_id}"
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "99999" in response.json()["detail"]
        assert "not found" in response.json()["detail"].lower()

    async def test_compare_player2_not_found(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test comparison when player 2 doesn't exist."""
        # Arrange - Create only player 1
        response1 = await client.post("/api/v1/players", json=sample_player_data)
        player1_id = response1.json()["id"]

        # Act - Try to compare with non-existent player 2
        response = await client.get(
            f"/api/v1/players/compare?player_id_1={player1_id}&player_id_2=99999"
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "99999" in response.json()["detail"]
        assert "not found" in response.json()["detail"].lower()

    async def test_compare_both_players_not_found(self, client: AsyncClient):
        """Test comparison when both players don't exist."""
        # Act
        response = await client.get(
            "/api/v1/players/compare?player_id_1=99998&player_id_2=99999"
        )

        # Assert - Should fail on first player check
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "99998" in response.json()["detail"]

    async def test_compare_same_player(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test that comparing a player with itself returns error."""
        # Arrange
        response = await client.post("/api/v1/players", json=sample_player_data)
        player_id = response.json()["id"]

        # Act - Try to compare player with itself
        response = await client.get(
            f"/api/v1/players/compare?player_id_1={player_id}&player_id_2={player_id}"
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot compare a player with itself" in response.json()["detail"].lower()

    async def test_compare_missing_parameters(self, client: AsyncClient):
        """Test comparison without required parameters."""
        # Act - Missing both parameters
        response1 = await client.get("/api/v1/players/compare")

        # Act - Missing player_id_2
        response2 = await client.get("/api/v1/players/compare?player_id_1=1")

        # Act - Missing player_id_1
        response3 = await client.get("/api/v1/players/compare?player_id_2=1")

        # Assert - All should fail validation
        assert response1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response3.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_compare_invalid_player_ids(self, client: AsyncClient):
        """Test comparison with invalid player ID formats."""
        # Act - Negative IDs
        response1 = await client.get(
            "/api/v1/players/compare?player_id_1=-1&player_id_2=1"
        )

        # Act - Zero ID
        response2 = await client.get(
            "/api/v1/players/compare?player_id_1=0&player_id_2=1"
        )

        # Assert
        assert response1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_compare_with_null_market_values(
        self, client: AsyncClient
    ):
        """Test comparison when one or both players have null market values."""
        # Arrange - Create players without market values
        player1_data = {
            "first_name": "Player",
            "last_name": "One",
            "position": "forward",
            "goals": 100,
            "assists": 50,
            "matches_played": 100,
        }

        player2_data = {
            "first_name": "Player",
            "last_name": "Two",
            "position": "forward",
            "goals": 120,
            "assists": 40,
            "matches_played": 100,
            "market_value_euros": 25000000,
        }

        response1 = await client.post("/api/v1/players", json=player1_data)
        response2 = await client.post("/api/v1/players", json=player2_data)

        player1_id = response1.json()["id"]
        player2_id = response2.json()["id"]

        # Act
        response = await client.get(
            f"/api/v1/players/compare?player_id_1={player1_id}&player_id_2={player2_id}"
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Player 2 should win market value (player 1 has None)
        market_comparison = data["comparison"]["market_value_euros"]
        assert market_comparison["player_1_value"] is None
        assert market_comparison["player_2_value"] == 25000000
        assert market_comparison["winner"] == "player_2"

    async def test_compare_response_includes_computed_fields(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test that comparison response includes computed fields like goals_per_match."""
        # Arrange
        messi_response = await client.post("/api/v1/players", json=sample_players_list[0])
        ronaldo_response = await client.post("/api/v1/players", json=sample_players_list[1])

        messi_id = messi_response.json()["id"]
        ronaldo_id = ronaldo_response.json()["id"]

        # Act
        response = await client.get(
            f"/api/v1/players/compare?player_id_1={messi_id}&player_id_2={ronaldo_id}"
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify computed fields are present in player objects
        assert "goals_per_match" in data["player_1"]
        assert "assists_per_match" in data["player_1"]
        assert "full_name" in data["player_1"]
        assert "age" in data["player_1"]

        assert "goals_per_match" in data["player_2"]
        assert "assists_per_match" in data["player_2"]
        assert "full_name" in data["player_2"]
        assert "age" in data["player_2"]

        # Verify computed fields are compared
        assert "goals_per_match" in data["comparison"]
        assert "assists_per_match" in data["comparison"]

    async def test_compare_different_positions(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test comparing players from different positions."""
        # Arrange - Compare forward with goalkeeper
        messi_response = await client.post("/api/v1/players", json=sample_players_list[0])  # Forward
        alisson_response = await client.post("/api/v1/players", json=sample_players_list[4])  # Goalkeeper

        messi_id = messi_response.json()["id"]
        alisson_id = alisson_response.json()["id"]

        # Act
        response = await client.get(
            f"/api/v1/players/compare?player_id_1={messi_id}&player_id_2={alisson_id}"
        )

        # Assert - Should work fine, goalkeepers just have fewer goals
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Forward should dominate offensive stats
        assert data["comparison"]["goals"]["winner"] == "player_1"
        assert data["comparison"]["assists"]["winner"] == "player_1"

    async def test_compare_without_token_returns_401(self, client: AsyncClient):
        """Test that accessing compare endpoint without authentication returns 401."""
        # Act - Try to compare players without providing authentication token
        response = await client.get("/api/v1/players/compare?player_id_1=1&player_id_2=2")

        # Assert - Should return 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    async def test_compare_with_valid_token_returns_200(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test that accessing compare endpoint with valid token returns 200."""
        # Arrange - Create two players first (player creation doesn't require auth)
        messi_response = await client.post("/api/v1/players/", json=sample_players_list[0])
        ronaldo_response = await client.post("/api/v1/players/", json=sample_players_list[1])

        assert messi_response.status_code == status.HTTP_201_CREATED
        assert ronaldo_response.status_code == status.HTTP_201_CREATED

        messi_id = messi_response.json()["id"]
        ronaldo_id = ronaldo_response.json()["id"]

        # Create a user and get authentication token
        user_data = {
            "email": "compareuser@example.com",
            "password": "securepassword123"
        }
        await client.post("/api/v1/users/", json=user_data)

        # Login to get token
        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        # Act - Compare with valid token
        response = await client.get(
            f"/api/v1/players/compare?player_id_1={messi_id}&player_id_2={ronaldo_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert - Should return 200 OK with comparison data
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "player_1" in data
        assert "player_2" in data
        assert "comparison" in data
        assert "summary" in data
