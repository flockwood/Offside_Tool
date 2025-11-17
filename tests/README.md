# Testing Documentation

This directory contains the comprehensive test suite for the Soccer Analytics Backend.

## Test Structure

```
tests/
├── conftest.py              # Shared pytest fixtures
├── unit/                    # Unit tests
│   └── test_crud_player.py  # CRUD operations tests
├── integration/             # Integration tests
│   └── test_api_players.py  # API endpoint tests
└── fixtures/                # Test data fixtures (future)
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)

Unit tests focus on individual components in isolation:

- **CRUD Operations**: Testing database operations without API layer
- **Model Logic**: Testing computed properties and model methods
- **Business Logic**: Testing core functionality

**Run unit tests only:**
```bash
pytest tests/unit -v
```

### 2. Integration Tests (`tests/integration/`)

Integration tests verify the interaction between components:

- **API Endpoints**: Full request/response cycle
- **Database Integration**: Real database operations
- **Validation**: Request/response validation

**Run integration tests only:**
```bash
pytest tests/integration -v
```

## Running Tests

### Prerequisites

1. **Install dependencies:**
   ```bash
   poetry install --with dev
   ```

2. **Set up test database:**
   ```bash
   # Using Docker
   docker-compose up -d postgres redis

   # Or install PostgreSQL and Redis locally
   ```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run tests in parallel (faster)
pytest -n auto
```

### Run Specific Tests

```bash
# Run specific test file
pytest tests/unit/test_crud_player.py

# Run specific test class
pytest tests/unit/test_crud_player.py::TestPlayerCRUD

# Run specific test method
pytest tests/unit/test_crud_player.py::TestPlayerCRUD::test_create_player

# Run by marker
pytest -m unit
pytest -m integration
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Generate terminal report
pytest --cov=app --cov-report=term-missing

# Generate XML report (for CI/CD)
pytest --cov=app --cov-report=xml
```

## Test Database

### Configuration

Tests use a separate test database configured in `conftest.py`:

```python
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/soccer_analytics_test"
```

### Database Isolation

- Each test gets a fresh database session
- Transactions are rolled back after each test
- Database state doesn't leak between tests

### Using SQLite for Faster Tests (Optional)

For faster local testing, you can use SQLite:

```python
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

Note: Some PostgreSQL-specific features may not work with SQLite.

## Fixtures

### Available Fixtures

All fixtures are defined in `conftest.py`:

#### Database Fixtures

- `test_engine`: Async database engine for tests
- `test_session`: Async database session with automatic rollback
- `client`: HTTP test client with database override

#### Data Fixtures

- `sample_player_data`: Complete player data
- `sample_player_data_minimal`: Minimal player data (required fields only)
- `sample_players_list`: List of 5 diverse players
- `invalid_player_data`: Invalid data for testing validation

### Using Fixtures

```python
async def test_example(test_session, sample_player_data):
    """Example test using fixtures."""
    player_in = PlayerCreate(**sample_player_data)
    player = await player_crud.create(test_session, obj_in=player_in)
    assert player.id is not None
```

## Test Coverage Goals

Our target coverage metrics:

- **Overall Coverage**: > 90%
- **CRUD Operations**: 100%
- **API Endpoints**: > 95%
- **Models**: > 90%

### Current Coverage

Run this command to see current coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

## Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test Structure

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestPlayerFeature:
    """Test suite for player feature."""

    async def test_feature_success(self, client: AsyncClient):
        """Test successful feature execution."""
        # Arrange
        data = {"key": "value"}

        # Act
        response = await client.post("/api/v1/endpoint", json=data)

        # Assert
        assert response.status_code == 200
        assert response.json()["key"] == "value"

    async def test_feature_validation_error(self, client: AsyncClient):
        """Test feature with invalid data."""
        # Arrange
        invalid_data = {}

        # Act
        response = await client.post("/api/v1/endpoint", json=invalid_data)

        # Assert
        assert response.status_code == 422
```

### Testing Best Practices

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **One assertion per test**: Test one thing at a time
3. **Clear test names**: Describe what is being tested
4. **Use fixtures**: Reuse common setup code
5. **Test edge cases**: Not just the happy path
6. **Keep tests fast**: Use mocks when appropriate
7. **Independent tests**: Tests should not depend on each other

## Continuous Integration

Tests automatically run on every push/PR via GitHub Actions:

1. **Code Quality**: Black, isort, Ruff, Flake8, MyPy
2. **Unit Tests**: All unit tests with coverage
3. **Integration Tests**: All integration tests with real database
4. **Security Scan**: Safety, Bandit
5. **Docker Build**: Verify Docker image builds

See `.github/workflows/ci.yml` for full CI configuration.

## Debugging Tests

### Run with pytest debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at start of test
pytest --trace

# Show print statements
pytest -s

# Show local variables on failure
pytest -l
```

### VS Code Debugging

1. Install Python extension
2. Set breakpoint in test file
3. Run "Python: Debug Tests" from command palette

### Pytest Debugging Tips

```python
# Add breakpoint in test
def test_something():
    import pdb; pdb.set_trace()
    # Your test code
```

## Performance Testing

### Benchmarking Tests

```bash
# Install pytest-benchmark
poetry add --group dev pytest-benchmark

# Run benchmark tests
pytest tests/ --benchmark-only
```

### Load Testing (Future)

Consider adding:
- Locust for load testing
- pytest-benchmark for performance regression testing

## Test Data Management

### Factory Pattern (Future Enhancement)

Consider implementing factory patterns using `factory_boy`:

```python
from factory import Factory
from app.models.player import Player

class PlayerFactory(Factory):
    class Meta:
        model = Player

    first_name = "Test"
    last_name = "Player"
    position = "forward"
```

## Common Issues

### Database Connection Errors

```bash
# Ensure PostgreSQL is running
docker-compose up -d postgres

# Check connection
psql -h localhost -U postgres -d soccer_analytics_test
```

### Import Errors

```bash
# Ensure app is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Or use poetry
poetry run pytest
```

### Async Test Errors

Ensure tests are marked with `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

## Future Enhancements

- [ ] Add mutation testing (mutmut)
- [ ] Add property-based testing (Hypothesis)
- [ ] Add contract testing for API
- [ ] Add performance benchmarks
- [ ] Add E2E tests with Playwright
- [ ] Add test data factories
- [ ] Add fixtures for common scenarios
- [ ] Add visual regression testing
