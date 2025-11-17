"""
Pytest configuration and shared fixtures.

This module provides fixtures that are shared across all tests including:
- Database session fixtures
- Test client fixtures
- Sample data factories
"""
import asyncio
import os
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient

from app.main import app
from app.db.session import Base, get_db
from app.core.config import settings


# Test database URL - uses environment variable or defaults to localhost
# Override with TEST_DATABASE_URL environment variable when running in Docker
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/soccer_analytics_test"
)

# Alternative: Use SQLite for faster tests (requires aiosqlite)
# TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an event loop for the test session.

    This fixture is session-scoped to allow sharing the same event loop
    across all async tests in the session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """
    Create a test database engine.

    Uses a separate test database to avoid affecting production data.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,  # Use StaticPool for SQLite or testing
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    Each test gets a fresh database session that is rolled back after the test.
    This ensures test isolation.
    """
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client with overridden database dependency.

    This client uses the test database session instead of the production one.
    """
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


# Sample data fixtures

@pytest.fixture
def sample_player_data() -> dict:
    """
    Sample player data for testing.

    Returns a dictionary with valid player attributes.
    """
    return {
        "first_name": "Lionel",
        "last_name": "Messi",
        "date_of_birth": "1987-06-24",
        "nationality": "Argentina",
        "height_cm": 170,
        "weight_kg": 72,
        "preferred_foot": "left",
        "position": "forward",
        "jersey_number": 10,
        "current_club": "Inter Miami",
        "market_value_euros": 35000000.0,
        "goals": 800,
        "assists": 350,
        "matches_played": 1000,
        "yellow_cards": 50,
        "red_cards": 3,
        "minutes_played": 85000,
        "rating": 9.5,
    }


@pytest.fixture
def sample_player_data_minimal() -> dict:
    """
    Minimal player data for testing (only required fields).
    """
    return {
        "first_name": "Cristiano",
        "last_name": "Ronaldo",
        "position": "forward",
    }


@pytest.fixture
def sample_players_list() -> list[dict]:
    """
    List of sample players for bulk testing.
    """
    return [
        {
            "first_name": "Lionel",
            "last_name": "Messi",
            "position": "forward",
            "nationality": "Argentina",
            "current_club": "Inter Miami",
            "goals": 800,
            "assists": 350,
            "matches_played": 1000,
            "rating": 9.5,
        },
        {
            "first_name": "Cristiano",
            "last_name": "Ronaldo",
            "position": "forward",
            "nationality": "Portugal",
            "current_club": "Al Nassr",
            "goals": 850,
            "assists": 250,
            "matches_played": 1100,
            "rating": 9.3,
        },
        {
            "first_name": "Kevin",
            "last_name": "De Bruyne",
            "position": "midfielder",
            "nationality": "Belgium",
            "current_club": "Manchester City",
            "goals": 120,
            "assists": 180,
            "matches_played": 500,
            "rating": 8.8,
        },
        {
            "first_name": "Virgil",
            "last_name": "van Dijk",
            "position": "defender",
            "nationality": "Netherlands",
            "current_club": "Liverpool",
            "goals": 25,
            "assists": 10,
            "matches_played": 400,
            "rating": 8.5,
        },
        {
            "first_name": "Alisson",
            "last_name": "Becker",
            "position": "goalkeeper",
            "nationality": "Brazil",
            "current_club": "Liverpool",
            "goals": 0,
            "assists": 0,
            "matches_played": 300,
            "rating": 8.7,
        },
    ]


@pytest.fixture
def invalid_player_data() -> dict:
    """
    Invalid player data for testing validation errors.
    """
    return {
        "first_name": "",  # Invalid: empty string
        "last_name": "Test",
        "date_of_birth": "2050-01-01",  # Invalid: future date
        "height_cm": 50,  # Invalid: too short
        "position": "invalid_position",  # Invalid: not an enum value
        "jersey_number": 999,  # Invalid: exceeds max
    }
