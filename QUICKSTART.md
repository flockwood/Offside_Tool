# Quick Start Guide

Get your Soccer Analytics Backend up and running in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- 8GB RAM minimum
- Ports available: 8000, 5432, 6379, 5555

## Step 1: Setup Environment

```bash
# Navigate to project directory
cd soccer-analytics-backend

# Copy environment file
cp .env.example .env

# (Optional) Edit .env with your preferred settings
# Default settings work out of the box!
```

## Step 2: Start Services

### Option A: Using the Setup Script (Linux/Mac)

```bash
chmod +x setup.sh
./setup.sh
```

### Option B: Using Makefile

```bash
make up
```

### Option C: Using Docker Compose Directly

```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head
```

## Step 3: Verify Installation

Open your browser and visit:

- **API Docs**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health
- **Flower (Celery Monitoring)**: http://localhost:5555

## Step 4: Create Your First Player

### Using API Docs (Swagger UI)

1. Go to http://localhost:8000/docs
2. Click on `POST /api/v1/players`
3. Click "Try it out"
4. Use this sample data:

```json
{
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
  "market_value_euros": 35000000,
  "goals": 800,
  "assists": 350,
  "matches_played": 1000,
  "rating": 9.5
}
```

5. Click "Execute"

### Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/players" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Lionel",
    "last_name": "Messi",
    "date_of_birth": "1987-06-24",
    "nationality": "Argentina",
    "position": "forward",
    "jersey_number": 10,
    "current_club": "Inter Miami",
    "goals": 800,
    "assists": 350,
    "matches_played": 1000,
    "rating": 9.5
  }'
```

### Using Python

```python
import requests

player_data = {
    "first_name": "Lionel",
    "last_name": "Messi",
    "date_of_birth": "1987-06-24",
    "nationality": "Argentina",
    "position": "forward",
    "jersey_number": 10,
    "current_club": "Inter Miami",
    "goals": 800,
    "assists": 350,
    "matches_played": 1000,
    "rating": 9.5
}

response = requests.post(
    "http://localhost:8000/api/v1/players",
    json=player_data
)

print(response.json())
```

## Step 5: Explore API Endpoints

### Get All Players

```bash
curl http://localhost:8000/api/v1/players
```

### Get Player by ID

```bash
curl http://localhost:8000/api/v1/players/1
```

### Filter Players

```bash
# By position
curl "http://localhost:8000/api/v1/players?position=forward"

# By nationality
curl "http://localhost:8000/api/v1/players?nationality=Argentina"

# By minimum rating
curl "http://localhost:8000/api/v1/players?min_rating=8.0"

# Search by name or club
curl "http://localhost:8000/api/v1/players?search=Messi"
```

### Get Top Scorers

```bash
curl http://localhost:8000/api/v1/players/top/scorers?limit=10
```

### Get Statistics

```bash
curl http://localhost:8000/api/v1/players/stats/overview
```

## Common Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View service status
docker-compose ps

# Run migrations
docker-compose exec api alembic upgrade head

# Access database
docker-compose exec postgres psql -U postgres -d soccer_analytics

# Access API shell
docker-compose exec api /bin/sh
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use, edit `.env`:

```env
# Change API port
API_PORT=8001
```

Then update `docker-compose.yml`:

```yaml
api:
  ports:
    - "${API_PORT:-8001}:8000"
```

### Services Won't Start

```bash
# Clean everything and restart
docker-compose down -v
docker-compose up -d --build
```

### Database Connection Error

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Celery Tasks Not Running

```bash
# Check Celery worker status
docker-compose logs celery_worker

# Restart Celery worker
docker-compose restart celery_worker

# Monitor tasks in Flower
# Open http://localhost:5555
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore API documentation at http://localhost:8000/docs
- Check out [migrations/README](migrations/README) for database migration guide
- Customize Celery tasks in `app/tasks/scraping_tasks.py`
- Add authentication and authorization
- Set up production deployment

## Sample Data

Want to populate the database with sample players? Here's a script:

```python
import requests

sample_players = [
    {
        "first_name": "Cristiano",
        "last_name": "Ronaldo",
        "nationality": "Portugal",
        "position": "forward",
        "jersey_number": 7,
        "goals": 850,
        "assists": 250
    },
    {
        "first_name": "Neymar",
        "last_name": "Jr",
        "nationality": "Brazil",
        "position": "forward",
        "jersey_number": 10,
        "goals": 400,
        "assists": 220
    },
    {
        "first_name": "Kevin",
        "last_name": "De Bruyne",
        "nationality": "Belgium",
        "position": "midfielder",
        "jersey_number": 17,
        "goals": 120,
        "assists": 180
    }
]

for player in sample_players:
    response = requests.post(
        "http://localhost:8000/api/v1/players",
        json=player
    )
    print(f"Created: {player['first_name']} {player['last_name']}")
```

## Support

Need help? Check:

- API Documentation: http://localhost:8000/docs
- README.md for detailed information
- Docker logs: `docker-compose logs -f`

Happy coding! ⚽🚀
