# 🚀 Run and Test Guide

Complete guide to running and testing the Soccer Analytics Backend with MVP features.

---

## Prerequisites

✅ Docker Desktop installed and running
✅ Docker Compose available
✅ Ports available: 8000, 5432, 6379, 5555

---

## Quick Start (3 Steps)

### Step 1: Start All Services

```bash
cd soccer-analytics-backend

# Start all services (PostgreSQL, Redis, API, Celery, Flower)
docker-compose up -d

# Check if services are running
docker-compose ps
```

Expected output:
```
NAME                              STATUS
soccer_analytics_api              Up (healthy)
soccer_analytics_celery_beat      Up
soccer_analytics_celery_worker    Up
soccer_analytics_db               Up (healthy)
soccer_analytics_flower           Up
soccer_analytics_redis            Up (healthy)
```

### Step 2: Run Database Migrations

Migrations should run automatically on startup, but you can verify:

```bash
# Check migration status
docker-compose exec api alembic current

# If needed, run migrations manually
docker-compose exec api alembic upgrade head
```

### Step 3: Test MVP Features

```bash
# Option 1: Run the interactive test script
docker-compose exec api python test_mvp_features.py

# Option 2: Run automated tests
docker-compose exec api pytest tests/integration/test_api_players_mvp.py -v
```

---

## Detailed Testing Guide

### 1. Health Check

First, verify the API is running:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Soccer Analytics API",
  "version": "0.1.0",
  "environment": "development"
}
```

### 2. Interactive API Testing

Visit the Swagger UI:
```
http://localhost:8000/docs
```

You'll see all endpoints including our new MVP features:
- `GET /api/v1/players/search` - Search players by name
- `GET /api/v1/players/compare` - Compare two players

### 3. Create Sample Players

You can use the test script or create manually via API:

#### Using Test Script (Recommended)

```bash
# This creates 5 sample players and tests all features
docker-compose exec api python test_mvp_features.py
```

#### Manual Creation via cURL

```bash
# Create Lionel Messi
curl -X POST "http://localhost:8000/api/v1/players" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Lionel",
    "last_name": "Messi",
    "position": "forward",
    "nationality": "Argentina",
    "current_club": "Inter Miami",
    "jersey_number": 10,
    "goals": 800,
    "assists": 350,
    "matches_played": 1000,
    "market_value_euros": 35000000,
    "rating": 9.5
  }'

# Create Cristiano Ronaldo
curl -X POST "http://localhost:8000/api/v1/players" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Cristiano",
    "last_name": "Ronaldo",
    "position": "forward",
    "nationality": "Portugal",
    "current_club": "Al Nassr",
    "jersey_number": 7,
    "goals": 850,
    "assists": 250,
    "matches_played": 1100,
    "market_value_euros": 15000000,
    "rating": 9.3
  }'
```

### 4. Test Search Feature

```bash
# Search for "Messi"
curl "http://localhost:8000/api/v1/players/search?name=Messi"

# Case-insensitive search
curl "http://localhost:8000/api/v1/players/search?name=RONALDO"

# Partial match
curl "http://localhost:8000/api/v1/players/search?name=Ron"

# Search by first name
curl "http://localhost:8000/api/v1/players/search?name=Cristiano"
```

### 5. Test Comparison Feature

```bash
# Compare player 1 vs player 2
curl "http://localhost:8000/api/v1/players/compare?player_id_1=1&player_id_2=2"

# Pretty print with jq (if installed)
curl "http://localhost:8000/api/v1/players/compare?player_id_1=1&player_id_2=2" | jq
```

Expected response structure:
```json
{
  "player_1": { /* Full player object */ },
  "player_2": { /* Full player object */ },
  "comparison": {
    "market_value_euros": {
      "player_1_value": 35000000,
      "player_2_value": 15000000,
      "winner": "player_1"
    },
    "goals": {
      "player_1_value": 800,
      "player_2_value": 850,
      "winner": "player_2"
    },
    "assists": { /* ... */ },
    "goals_per_match": { /* ... */ },
    "assists_per_match": { /* ... */ }
  },
  "summary": {
    "player_1_wins": 4,
    "player_2_wins": 1,
    "ties": 0
  }
}
```

---

## Running Automated Tests

### All Tests

```bash
# Run entire test suite
docker-compose exec api pytest -v

# With coverage
docker-compose exec api pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### MVP Tests Only

```bash
# Run all MVP tests
docker-compose exec api pytest tests/integration/test_api_players_mvp.py -v

# Run only search tests
docker-compose exec api pytest tests/integration/test_api_players_mvp.py::TestPlayerSearchEndpoint -v

# Run only comparison tests
docker-compose exec api pytest tests/integration/test_api_players_mvp.py::TestPlayerComparisonEndpoint -v

# Run specific test
docker-compose exec api pytest tests/integration/test_api_players_mvp.py::TestPlayerSearchEndpoint::test_search_returns_multiple_players -v
```

### Unit Tests

```bash
# Run CRUD unit tests
docker-compose exec api pytest tests/unit/test_crud_player.py -v

# Run all unit tests
docker-compose exec api pytest tests/unit/ -v
```

### Integration Tests

```bash
# Run all integration tests
docker-compose exec api pytest tests/integration/ -v
```

---

## Using the Test Script

The `test_mvp_features.py` script provides an interactive way to test:

```bash
# Run the test script
docker-compose exec api python test_mvp_features.py
```

This script will:
1. ✅ Check API health
2. ✅ Create 5 sample players (Messi, Ronaldo, De Bruyne, Mbappé, Haaland)
3. ✅ Test search with various queries
4. ✅ Test player comparisons
5. ✅ Test error cases
6. ✅ Display formatted results

Sample output:
```
================================================================================
  🚀 Soccer Analytics MVP Features - Live Testing
================================================================================

✅ API is healthy and running

================================================================================
  Step 1: Creating Sample Players
================================================================================

✅ Created: Lionel Messi (ID: 1)
✅ Created: Cristiano Ronaldo (ID: 2)
✅ Created: Kevin De Bruyne (ID: 3)
...

================================================================================
  Step 2: Testing Player Search Feature
================================================================================

🔍 Searching for 'Messi'...
   Found 1 player(s):
   1. Lionel Messi (forward - Inter Miami)

🔍 Searching for 'ronaldo' (case-insensitive)...
   Found 1 player(s):
   1. Cristiano Ronaldo (forward - Al Nassr)

================================================================================
  Step 3: Testing Player Comparison Feature
================================================================================

⚔️  Comparison 1: Player 1 vs Player 2
--------------------------------------------------------------------------------

Lionel Messi vs Cristiano Ronaldo

Metric                    Player 1             Player 2             Winner
--------------------------------------------------------------------------------
Market Value              €35,000,000          €15,000,000          🏆 Player 1
Goals                     800                  850                  🏆 Player 2
Assists                   350                  250                  🏆 Player 1
Goals per Match           0.80                 0.77                 🏆 Player 1
Assists per Match         0.35                 0.23                 🏆 Player 1

--------------------------------------------------------------------------------

📊 SUMMARY:
   Lionel Messi: 4 wins
   Cristiano Ronaldo: 1 wins
   Ties: 0

🎉 OVERALL WINNER: Lionel Messi
```

---

## Monitoring & Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery_worker
docker-compose logs -f postgres
```

### Celery Monitoring (Flower)

Visit: http://localhost:5555

See:
- Active workers
- Task history
- Task details
- Scheduled tasks

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d soccer_analytics

# Run SQL queries
SELECT id, first_name, last_name, position, goals FROM players;
```

### API Logs

```bash
# Follow API logs
docker-compose logs -f api

# Search for specific requests
docker-compose logs api | grep "GET /api/v1/players/search"
```

---

## Common Issues & Solutions

### Issue: Port already in use

**Error**: `Port 8000 is already allocated`

**Solution**:
```bash
# Stop conflicting service or change port in docker-compose.yml
docker-compose down
# Edit docker-compose.yml and change port mapping
docker-compose up -d
```

### Issue: Database connection error

**Error**: `could not connect to server: Connection refused`

**Solution**:
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Wait for health check
docker-compose ps

# Check logs
docker-compose logs postgres
```

### Issue: Tests fail with "connection refused"

**Solution**:
```bash
# Make sure services are running
docker-compose ps

# Restart all services
docker-compose restart

# Wait 10 seconds for services to be ready
sleep 10

# Run tests again
docker-compose exec api pytest
```

### Issue: Migration errors

**Solution**:
```bash
# Check current migration status
docker-compose exec api alembic current

# Reset migrations (WARNING: destroys data)
docker-compose exec api alembic downgrade base
docker-compose exec api alembic upgrade head
```

---

## Clean Restart

If you want to start fresh:

```bash
# Stop all services and remove volumes
docker-compose down -v

# Remove all containers
docker-compose rm -f

# Start fresh
docker-compose up -d

# Wait for services to be healthy
sleep 15

# Run migrations
docker-compose exec api alembic upgrade head

# Run test script
docker-compose exec api python test_mvp_features.py
```

---

## Performance Testing

### Load Testing with Apache Bench

```bash
# Install Apache Bench (ab)
# Ubuntu: sudo apt-get install apache2-utils
# macOS: brew install apache-bench

# Test search endpoint
ab -n 1000 -c 10 "http://localhost:8000/api/v1/players/search?name=Messi"

# Test comparison endpoint
ab -n 1000 -c 10 "http://localhost:8000/api/v1/players/compare?player_id_1=1&player_id_2=2"
```

### Response Time Testing

```bash
# Measure response time
time curl "http://localhost:8000/api/v1/players/search?name=Messi"

# Multiple iterations
for i in {1..10}; do
  time curl -s "http://localhost:8000/api/v1/players/compare?player_id_1=1&player_id_2=2" > /dev/null
done
```

---

## Integration with Frontend

### CORS Configuration

CORS is configured in `.env`:
```env
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://localhost:5173"]
```

Add your frontend URL if different.

### JavaScript/TypeScript Example

```typescript
// Search players
const searchPlayers = async (query: string) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/players/search?name=${encodeURIComponent(query)}`
  );
  return await response.json();
};

// Compare players
const comparePlayers = async (id1: number, id2: number) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/players/compare?player_id_1=${id1}&player_id_2=${id2}`
  );
  return await response.json();
};

// Usage
const players = await searchPlayers("Messi");
const comparison = await comparePlayers(1, 2);
console.log(comparison.summary);
```

---

## Next Steps

After successful testing:

1. ✅ **Explore API Docs**: http://localhost:8000/docs
2. ✅ **Check Flower**: http://localhost:5555
3. ✅ **Run Full Test Suite**: `docker-compose exec api pytest -v`
4. ✅ **Review Coverage**: `docker-compose exec api pytest --cov=app --cov-report=html`
5. ✅ **Read MVP Docs**: See [MVP_FEATURES.md](MVP_FEATURES.md)

---

## Stopping Services

```bash
# Stop all services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (clean slate)
docker-compose down -v
```

---

## Summary

You now have a fully functional Soccer Analytics Backend with:

✅ Player Search by name (case-insensitive, partial matching)
✅ Player-to-Player Comparison (5 metrics, winner determination)
✅ Comprehensive test suite (26 MVP tests + 70 existing tests)
✅ Interactive API documentation
✅ Celery background tasks
✅ Real-time monitoring with Flower
✅ Production-ready architecture

**Happy testing! ⚽🚀**
