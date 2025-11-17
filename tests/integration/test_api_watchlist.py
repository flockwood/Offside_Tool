"""
Integration tests for watchlist API endpoints.

Tests the complete watchlist lifecycle including adding, retrieving, and removing players.
All endpoints require authentication.
"""
import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestWatchlistLifecycle:
    """Test suite for watchlist lifecycle operations."""

    async def test_add_player_to_watchlist_success(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test successfully adding a player to watchlist."""
        # Arrange - Create user and player
        user_data = {"email": "watchlist@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        player_response = await client.post("/api/v1/players/", json=sample_player_data)
        player_id = player_response.json()["id"]

        # Act - Add player to watchlist
        response = await client.post(
            f"/api/v1/watchlist/{player_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "message" in data
        assert data["player_id"] == player_id
        assert "Messi" in data["player_name"]

    async def test_add_player_to_watchlist_player_not_found(self, client: AsyncClient):
        """Test adding a non-existent player to watchlist."""
        # Arrange - Create user
        user_data = {"email": "watchlist2@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        # Act - Try to add non-existent player
        response = await client.post(
            "/api/v1/watchlist/99999",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    async def test_add_same_player_twice(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test adding the same player twice is idempotent."""
        # Arrange
        user_data = {"email": "watchlist3@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        player_response = await client.post("/api/v1/players/", json=sample_player_data)
        player_id = player_response.json()["id"]

        # Act - Add player twice
        response1 = await client.post(
            f"/api/v1/watchlist/{player_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        response2 = await client.post(
            f"/api/v1/watchlist/{player_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert - Both should succeed
        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_201_CREATED

        # Verify watchlist only has one copy
        watchlist_response = await client.get(
            "/api/v1/watchlist/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert len(watchlist_response.json()) == 1

    async def test_get_empty_watchlist(self, client: AsyncClient):
        """Test getting an empty watchlist."""
        # Arrange
        user_data = {"email": "watchlist4@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        # Act
        response = await client.get(
            "/api/v1/watchlist/",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    async def test_get_watchlist_with_one_player(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test getting watchlist with one player."""
        # Arrange
        user_data = {"email": "watchlist5@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        player_response = await client.post("/api/v1/players/", json=sample_player_data)
        player_id = player_response.json()["id"]

        await client.post(
            f"/api/v1/watchlist/{player_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Act
        response = await client.get(
            "/api/v1/watchlist/",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == player_id
        assert data[0]["last_name"] == "Messi"

    async def test_get_watchlist_with_multiple_players(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test getting watchlist with multiple players."""
        # Arrange
        user_data = {"email": "watchlist6@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        # Add 3 players to watchlist
        player_ids = []
        for player_data in sample_players_list[:3]:
            player_response = await client.post("/api/v1/players/", json=player_data)
            player_id = player_response.json()["id"]
            player_ids.append(player_id)

            await client.post(
                f"/api/v1/watchlist/{player_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

        # Act
        response = await client.get(
            "/api/v1/watchlist/",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        returned_ids = [p["id"] for p in data]
        for player_id in player_ids:
            assert player_id in returned_ids

    async def test_remove_player_from_watchlist(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test removing a player from watchlist."""
        # Arrange
        user_data = {"email": "watchlist7@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        player_response = await client.post("/api/v1/players/", json=sample_player_data)
        player_id = player_response.json()["id"]

        await client.post(
            f"/api/v1/watchlist/{player_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Act - Remove player
        response = await client.delete(
            f"/api/v1/watchlist/{player_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "removed" in data["message"].lower()

        # Verify watchlist is empty
        watchlist_response = await client.get(
            "/api/v1/watchlist/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert len(watchlist_response.json()) == 0

    async def test_remove_player_not_in_watchlist(
        self, client: AsyncClient, sample_player_data: dict
    ):
        """Test removing a player that's not in watchlist."""
        # Arrange
        user_data = {"email": "watchlist8@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        player_response = await client.post("/api/v1/players/", json=sample_player_data)
        player_id = player_response.json()["id"]

        # Act - Remove player that was never added
        response = await client.delete(
            f"/api/v1/watchlist/{player_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert - Should succeed (idempotent)
        assert response.status_code == status.HTTP_200_OK

    async def test_remove_nonexistent_player(self, client: AsyncClient):
        """Test removing a player that doesn't exist."""
        # Arrange
        user_data = {"email": "watchlist9@example.com", "password": "secure123"}
        await client.post("/api/v1/users/", json=user_data)

        login_response = await client.post(
            "/api/v1/login/token",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        # Act
        response = await client.delete(
            "/api/v1/watchlist/99999",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
class TestWatchlistAuthentication:
    """Test suite for watchlist authentication requirements."""

    async def test_add_to_watchlist_without_token(self, client: AsyncClient):
        """Test that add endpoint requires authentication."""
        # Act
        response = await client.post("/api/v1/watchlist/1")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_watchlist_without_token(self, client: AsyncClient):
        """Test that get watchlist endpoint requires authentication."""
        # Act
        response = await client.get("/api/v1/watchlist/")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_remove_from_watchlist_without_token(self, client: AsyncClient):
        """Test that remove endpoint requires authentication."""
        # Act
        response = await client.delete("/api/v1/watchlist/1")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_watchlist_isolation_between_users(
        self, client: AsyncClient, sample_players_list: list[dict]
    ):
        """Test that watchlists are properly isolated between users."""
        # Arrange - Create two users
        user1_data = {"email": "user1@example.com", "password": "secure123"}
        user2_data = {"email": "user2@example.com", "password": "secure123"}

        await client.post("/api/v1/users/", json=user1_data)
        await client.post("/api/v1/users/", json=user2_data)

        # Get tokens
        login1 = await client.post(
            "/api/v1/login/token",
            data={"username": user1_data["email"], "password": user1_data["password"]}
        )
        token1 = login1.json()["access_token"]

        login2 = await client.post(
            "/api/v1/login/token",
            data={"username": user2_data["email"], "password": user2_data["password"]}
        )
        token2 = login2.json()["access_token"]

        # Create two players
        player1_response = await client.post("/api/v1/players/", json=sample_players_list[0])
        player2_response = await client.post("/api/v1/players/", json=sample_players_list[1])

        player1_id = player1_response.json()["id"]
        player2_id = player2_response.json()["id"]

        # User 1 adds player 1
        await client.post(
            f"/api/v1/watchlist/{player1_id}",
            headers={"Authorization": f"Bearer {token1}"}
        )

        # User 2 adds player 2
        await client.post(
            f"/api/v1/watchlist/{player2_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )

        # Act - Get both watchlists
        watchlist1 = await client.get(
            "/api/v1/watchlist/",
            headers={"Authorization": f"Bearer {token1}"}
        )
        watchlist2 = await client.get(
            "/api/v1/watchlist/",
            headers={"Authorization": f"Bearer {token2}"}
        )

        # Assert - Each user only sees their own watchlist
        assert len(watchlist1.json()) == 1
        assert watchlist1.json()[0]["id"] == player1_id

        assert len(watchlist2.json()) == 1
        assert watchlist2.json()[0]["id"] == player2_id
