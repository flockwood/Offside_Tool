"""
Integration tests for authentication API endpoints.

Tests the complete authentication flow including:
- User registration
- Login/token generation
- Protected endpoint access
- Token validation
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.core.security import create_access_token
from app.crud import user as user_crud
from app.schemas.user import UserCreate


@pytest.mark.integration
class TestUserRegistration:
    """Tests for user registration endpoint."""

    async def test_create_user_success(self, client: AsyncClient):
        """Test successful user creation."""
        response = await client.post(
            "/api/v1/users/",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        # Ensure password is never returned
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_create_user_duplicate_email(self, client: AsyncClient):
        """Test user creation with duplicate email fails."""
        # Create first user
        await client.post(
            "/api/v1/users/",
            json={
                "email": "duplicate@example.com",
                "password": "Password123!"
            }
        )

        # Try to create second user with same email
        response = await client.post(
            "/api/v1/users/",
            json={
                "email": "duplicate@example.com",
                "password": "DifferentPassword123!"
            }
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    async def test_create_user_invalid_email(self, client: AsyncClient):
        """Test user creation with invalid email format."""
        response = await client.post(
            "/api/v1/users/",
            json={
                "email": "not-an-email",
                "password": "Password123!"
            }
        )

        assert response.status_code == 422  # Validation error

    async def test_create_user_missing_password(self, client: AsyncClient):
        """Test user creation without password fails."""
        response = await client.post(
            "/api/v1/users/",
            json={
                "email": "user@example.com"
            }
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestLogin:
    """Tests for login/token generation endpoint."""

    async def test_login_success(self, client: AsyncClient, test_session: AsyncSession):
        """Test successful login with valid credentials."""
        # Create a test user first
        user_in = UserCreate(email="testuser@example.com", password="TestPassword123!")
        await user_crud.create_user(test_session, user_in)

        # Attempt login
        response = await client.post(
            "/api/v1/login/token",
            data={  # OAuth2 uses form data
                "username": "testuser@example.com",
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20  # JWT should be reasonably long

    async def test_login_wrong_password(self, client: AsyncClient, test_session: AsyncSession):
        """Test login with incorrect password fails."""
        # Create a test user first
        user_in = UserCreate(email="testuser2@example.com", password="CorrectPassword123!")
        await user_crud.create_user(test_session, user_in)

        # Attempt login with wrong password
        response = await client.post(
            "/api/v1/login/token",
            data={
                "username": "testuser2@example.com",
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent email fails."""
        response = await client.post(
            "/api/v1/login/token",
            data={
                "username": "nonexistent@example.com",
                "password": "SomePassword123!"
            }
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_missing_credentials(self, client: AsyncClient):
        """Test login without credentials fails."""
        response = await client.post("/api/v1/login/token", data={})

        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestProtectedEndpoints:
    """Tests for accessing protected endpoints."""

    async def test_access_protected_endpoint_with_valid_token(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test accessing /users/me with valid token succeeds."""
        # Create user and get token
        user_in = UserCreate(email="protecteduser@example.com", password="Password123!")
        user = await user_crud.create_user(test_session, user_in)

        token = create_access_token({"sub": user.email})

        # Access protected endpoint
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "protecteduser@example.com"
        assert data["id"] == user.id
        assert data["is_active"] is True

    async def test_access_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token fails."""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    async def test_access_protected_endpoint_with_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token fails."""
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )

        assert response.status_code == 401
        assert "validate credentials" in response.json()["detail"].lower()

    async def test_access_protected_endpoint_with_expired_token(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test accessing protected endpoint with expired token fails."""
        # Create user
        user_in = UserCreate(email="expireduser@example.com", password="Password123!")
        user = await user_crud.create_user(test_session, user_in)

        # Create expired token (negative expiration time)
        expired_token = create_access_token(
            {"sub": user.email},
            expires_delta=timedelta(minutes=-30)
        )

        # Try to access protected endpoint
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401
        assert "validate credentials" in response.json()["detail"].lower()

    async def test_access_protected_endpoint_with_nonexistent_user_token(
        self, client: AsyncClient
    ):
        """Test that token for deleted/nonexistent user is rejected."""
        # Create token for user that doesn't exist in DB
        token = create_access_token({"sub": "nonexistent@example.com"})

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401
        assert "validate credentials" in response.json()["detail"].lower()


@pytest.mark.integration
class TestInactiveUser:
    """Tests for inactive user scenarios."""

    async def test_inactive_user_cannot_login(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test that inactive users cannot log in."""
        # Create user
        user_in = UserCreate(email="inactive@example.com", password="Password123!")
        user = await user_crud.create_user(test_session, user_in)

        # Manually deactivate user
        user.is_active = False
        test_session.add(user)
        await test_session.commit()

        # Attempt login
        response = await client.post(
            "/api/v1/login/token",
            data={
                "username": "inactive@example.com",
                "password": "Password123!"
            }
        )

        assert response.status_code == 400
        assert "inactive" in response.json()["detail"].lower()

    async def test_inactive_user_cannot_access_protected_endpoints(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test that inactive users cannot access protected endpoints."""
        # Create user
        user_in = UserCreate(email="inactive2@example.com", password="Password123!")
        user = await user_crud.create_user(test_session, user_in)

        # Get token while user is active
        token = create_access_token({"sub": user.email})

        # Deactivate user
        user.is_active = False
        test_session.add(user)
        await test_session.commit()

        # Try to access protected endpoint
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        assert "inactive" in response.json()["detail"].lower()


@pytest.mark.integration
class TestCompleteAuthFlow:
    """End-to-end authentication flow tests."""

    async def test_complete_signup_login_access_flow(self, client: AsyncClient):
        """Test complete flow: signup -> login -> access protected resource."""
        # 1. Sign up
        signup_response = await client.post(
            "/api/v1/users/",
            json={
                "email": "flowuser@example.com",
                "password": "FlowPassword123!"
            }
        )
        assert signup_response.status_code == 201
        user_data = signup_response.json()

        # 2. Login
        login_response = await client.post(
            "/api/v1/login/token",
            data={
                "username": "flowuser@example.com",
                "password": "FlowPassword123!"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # 3. Access protected resource
        me_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["id"] == user_data["id"]
        assert me_data["email"] == "flowuser@example.com"


@pytest.mark.integration
class TestPasswordSecurity:
    """Tests to ensure password security."""

    async def test_password_is_hashed_in_database(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Ensure passwords are hashed, not stored in plain text."""
        # Create user
        plain_password = "MySecretPassword123!"
        user_in = UserCreate(email="hashtest@example.com", password=plain_password)
        user = await user_crud.create_user(test_session, user_in)

        # Verify password is hashed (bcrypt hashes start with $2b$)
        assert user.hashed_password.startswith("$2b$")
        assert user.hashed_password != plain_password
        assert len(user.hashed_password) > 50  # Bcrypt hashes are 60 chars

    async def test_password_never_returned_in_api(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Ensure password/hashed_password never appear in API responses."""
        # Create user and get token
        user_in = UserCreate(email="nopassword@example.com", password="Password123!")
        user = await user_crud.create_user(test_session, user_in)
        token = create_access_token({"sub": user.email})

        # Check /users/me endpoint
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data

        # Check user creation endpoint
        signup_response = await client.post(
            "/api/v1/users/",
            json={
                "email": "another@example.com",
                "password": "AnotherPassword123!"
            }
        )

        signup_data = signup_response.json()
        assert "password" not in signup_data
        assert "hashed_password" not in signup_data
