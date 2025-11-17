# Soccer Analytics Backend

A scalable, production-ready soccer player analytics backend built with modern Python technologies.

## Features

- **FastAPI**: High-performance async web framework
- **PostgreSQL**: Robust relational database with async support
- **SQLAlchemy 2.0**: Modern ORM with full type hints
- **Alembic**: Database migration management
- **Celery**: Distributed task queue for background jobs
- **Redis**: Caching and message broker
- **Docker**: Full containerization with Docker Compose
- **Pydantic**: Data validation and settings management

## Architecture

```
soccer-analytics-backend/
├── app/
│   ├── api/v1/endpoints/    # API endpoints
│   ├── core/                # Core configuration
│   ├── crud/                # Database operations
│   ├── db/                  # Database session management
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── tasks/               # Celery tasks
│   ├── celery_app.py        # Celery configuration
│   └── main.py              # FastAPI application
├── migrations/              # Alembic migrations
├── docker-compose.yml       # Docker services
├── Dockerfile               # Application container
└── pyproject.toml           # Dependencies
```

## Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Poetry (optional, for dependency management)

## Quick Start

### 1. Clone and Setup

```bash
cd soccer-analytics-backend
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Flower (Celery monitoring)**: http://localhost:5555

### 3. Run Migrations

Migrations run automatically on startup, but you can run them manually:

```bash
docker-compose exec api alembic upgrade head
```

## API Endpoints

### Players

- `GET /api/v1/players` - List all players (with pagination & filters)
- `POST /api/v1/players` - Create a new player
- `GET /api/v1/players/{id}` - Get player by ID
- `PUT /api/v1/players/{id}` - Update player
- `DELETE /api/v1/players/{id}` - Delete player
- `GET /api/v1/players/club/{club_name}` - Get players by club
- `GET /api/v1/players/top/scorers` - Get top scorers
- `GET /api/v1/players/stats/overview` - Get statistics overview

### System

- `GET /` - API information
- `GET /health` - Health check
- `GET /info` - Detailed system info

## Development

### Local Development (without Docker)

1. **Install dependencies:**

```bash
pip install poetry
poetry install
```

2. **Set up PostgreSQL and Redis:**

Make sure PostgreSQL and Redis are running locally or update `.env` with remote connections.

3. **Run migrations:**

```bash
alembic upgrade head
```

4. **Start the API:**

```bash
uvicorn app.main:app --reload
```

5. **Start Celery worker:**

```bash
celery -A app.celery_app worker --loglevel=info
```

6. **Start Celery beat (scheduler):**

```bash
celery -A app.celery_app beat --loglevel=info
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

### Running Tests

```bash
# Install test dependencies
poetry install --with dev

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Environment Variables

Key environment variables (see `.env.example` for all options):

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_SERVER` | PostgreSQL host | localhost |
| `POSTGRES_USER` | PostgreSQL user | postgres |
| `POSTGRES_PASSWORD` | PostgreSQL password | postgres |
| `POSTGRES_DB` | Database name | soccer_analytics |
| `REDIS_HOST` | Redis host | localhost |
| `DEBUG` | Enable debug mode | False |
| `ENVIRONMENT` | Environment (development/production) | development |

## Celery Tasks

Background tasks available:

- **scrape_player_statistics**: Scrape player stats (daily at 2:00 AM)
- **update_player_ratings**: Update player ratings (weekly on Monday at 3:00 AM)
- **cleanup_old_data**: Clean up old data (monthly on 1st at 4:00 AM)
- **import_players_bulk**: Import players in bulk
- **generate_analytics_report**: Generate analytics reports

### Running Tasks Manually

```python
from app.tasks.scraping_tasks import scrape_player_statistics

# Sync execution
result = scrape_player_statistics.delay()
print(result.get())

# Check task status
result.status
result.result
```

## Docker Services

The `docker-compose.yml` includes:

- **postgres**: PostgreSQL 16 database
- **redis**: Redis 7 for caching and message broker
- **api**: FastAPI application
- **celery_worker**: Celery worker for background tasks
- **celery_beat**: Celery beat scheduler
- **flower**: Celery monitoring dashboard

## Production Deployment

1. **Set production environment variables:**

```bash
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<strong-random-key>
```

2. **Use production-grade database:**

Update `DATABASE_URL` with production PostgreSQL credentials.

3. **Enable HTTPS:**

Configure a reverse proxy (Nginx/Traefik) with SSL certificates.

4. **Scale workers:**

```bash
docker-compose up -d --scale celery_worker=4
```

5. **Set up monitoring:**

- Use Flower for Celery monitoring
- Add application monitoring (Sentry, DataDog, etc.)
- Set up logging aggregation

## Code Quality

The project uses:

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **mypy**: Type checking

```bash
# Format code
black app/

# Sort imports
isort app/

# Run linter
flake8 app/

# Type checking
mypy app/
```

## API Documentation

Interactive API documentation is automatically generated:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/api/v1/openapi.json

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Run tests and linting
5. Commit: `git commit -am 'Add new feature'`
6. Push: `git push origin feature/new-feature`
7. Submit a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Contact the development team

## Roadmap

- [ ] Authentication & Authorization (JWT)
- [ ] Rate limiting
- [ ] Advanced analytics endpoints
- [ ] Real-time match statistics
- [ ] GraphQL API support
- [ ] Websocket support for live updates
- [ ] Machine learning player performance predictions
- [ ] Export data to CSV/Excel
- [ ] Multi-language support
- [ ] Admin dashboard

---

Built with ❤️ using Python, FastAPI, and modern backend technologies.
