# Frontend Integration Guide - Soccer Analytics API v2.0

## Overview

This document provides everything a frontend team needs to integrate with the Soccer Analytics API Staging Candidate v2.0. The API is a fully asynchronous, JWT-authenticated REST API built with FastAPI.

---

## API Environment Details

### Staging Environment
- **Base URL**: `http://localhost:8000` (Update with actual staging URL when deployed)
- **Interactive Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Documentation**: `http://localhost:8000/redoc` (ReDoc)
- **API Version**: v2.0
- **API Prefix**: `/api/v1`

### Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Soccer Analytics API",
  "version": "0.1.0",
  "environment": "development"
}
```

---

## Authentication Flow

The API uses **OAuth2 with JWT Bearer tokens**. All protected endpoints require a valid token in the Authorization header.

### Step 1: User Registration

**Endpoint:** `POST /api/v1/users/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Success Response (201 Created):**
```json
{
  "email": "user@example.com",
  "id": 1,
  "is_active": true,
  "created_at": "2025-01-17T20:30:00",
  "updated_at": "2025-01-17T20:30:00"
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "User with email 'user@example.com' already exists"
}
```

---

### Step 2: Login to Get JWT Token

**Endpoint:** `POST /api/v1/login/token`

**Request Headers:**
```
Content-Type: application/x-www-form-urlencoded
```

**Request Body (Form Data):**
```
username=user@example.com&password=securepassword123
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Incorrect email or password"
}
```

**Token Details:**
- Algorithm: HS256
- Expiration: 30 minutes from issue
- Include in all protected requests as: `Authorization: Bearer {access_token}`

---

### Step 3: Make Authenticated Requests

Include the token in the Authorization header for all protected endpoints:

```http
GET /api/v1/watchlist/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**JavaScript/TypeScript Example:**
```typescript
const token = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/v1/watchlist/', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
```

**Python Example:**
```python
import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    "http://localhost:8000/api/v1/watchlist/",
    headers=headers
)
data = response.json()
```

---

## Core API Endpoints

### Player Management

#### Get All Players (with pagination)
```http
GET /api/v1/players/?skip=0&limit=20
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Max records to return (default: 20, max: 100)
- `position` (optional): Filter by position
- `nationality` (optional): Filter by nationality
- `current_club` (optional): Filter by club
- `min_rating` (optional): Minimum rating filter
- `search` (optional): Search by name or club

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "first_name": "Lionel",
      "last_name": "Messi",
      "full_name": "Lionel Messi",
      "date_of_birth": "1987-06-24",
      "age": 38,
      "nationality": "Argentina",
      "position": "forward",
      "current_club": "Inter Miami",
      "goals": 800,
      "assists": 350,
      "matches_played": 1000,
      "goals_per_match": 0.8,
      "assists_per_match": 0.35
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### Get Single Player
```http
GET /api/v1/players/{player_id}
```

**Response:** Single player object with all attributes and computed properties.

---

## MVP v2 Features

### 🆕 Feature 1: Advanced Player Search

**Endpoint:** `POST /api/v1/players/search/advanced`

**Authentication:** Required (JWT token)

**Request Body (all fields optional):**
```json
{
  "club": "Manchester City",
  "nationality": "Brazil",
  "position": "midfielder",
  "min_age": 20,
  "max_age": 30
}
```

**Search Parameters:**
- `club` (string, optional): Filter by current club (case-insensitive)
- `nationality` (string, optional): Filter by nationality (case-insensitive)
- `position` (enum, optional): `"goalkeeper"`, `"defender"`, `"midfielder"`, `"forward"`
- `min_age` (integer, optional): Minimum age in years (10-60)
- `max_age` (integer, optional): Maximum age in years (10-60)

**Search Behavior:**
- All filters use AND logic (all conditions must match)
- Case-insensitive for text fields (club, nationality)
- Age calculated from date of birth
- Empty body `{}` returns all players
- No results returns empty array `[]`

**Success Response (200 OK):**
```json
[
  {
    "id": 5,
    "first_name": "Kevin",
    "last_name": "De Bruyne",
    "full_name": "Kevin De Bruyne",
    "age": 32,
    "nationality": "Belgium",
    "position": "midfielder",
    "current_club": "Manchester City",
    "goals": 120,
    "assists": 180
  }
]
```

**Use Cases:**
1. Find all midfielders under 25
2. Search for Brazilian forwards
3. Filter players by specific club and position
4. Age-based talent scouting (e.g., players 18-21)

**Frontend Implementation Example:**
```typescript
interface PlayerSearch {
  club?: string;
  nationality?: string;
  position?: 'goalkeeper' | 'defender' | 'midfielder' | 'forward';
  min_age?: number;
  max_age?: number;
}

async function advancedSearch(filters: PlayerSearch, token: string) {
  const response = await fetch('http://localhost:8000/api/v1/players/search/advanced', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(filters)
  });

  if (response.status === 401) {
    // Token expired or invalid - redirect to login
    return;
  }

  return await response.json();
}
```

---

### 🆕 Feature 2: User Watchlist System

A personalized watchlist allows users to follow/track specific players.

#### Add Player to Watchlist

**Endpoint:** `POST /api/v1/watchlist/{player_id}`

**Authentication:** Required

**Path Parameter:**
- `player_id` (integer): ID of player to add

**Success Response (201 Created):**
```json
{
  "message": "Player 'Lionel Messi' added to watchlist",
  "player_id": 1,
  "player_name": "Lionel Messi"
}
```

**Error Responses:**
- `404 Not Found`: Player doesn't exist
- `401 Unauthorized`: Invalid/missing token

**Note:** Adding the same player twice is idempotent (won't create duplicates)

---

#### Get User's Watchlist

**Endpoint:** `GET /api/v1/watchlist/`

**Authentication:** Required

**Success Response (200 OK):**
```json
[
  {
    "id": 1,
    "first_name": "Lionel",
    "last_name": "Messi",
    "full_name": "Lionel Messi",
    "position": "forward",
    "current_club": "Inter Miami",
    "age": 38,
    "goals": 800,
    "assists": 350
  },
  {
    "id": 2,
    "first_name": "Cristiano",
    "last_name": "Ronaldo",
    "full_name": "Cristiano Ronaldo",
    "position": "forward",
    "current_club": "Al Nassr",
    "age": 40,
    "goals": 850,
    "assists": 250
  }
]
```

**Empty Watchlist:**
```json
[]
```

---

#### Remove Player from Watchlist

**Endpoint:** `DELETE /api/v1/watchlist/{player_id}`

**Authentication:** Required

**Path Parameter:**
- `player_id` (integer): ID of player to remove

**Success Response (200 OK):**
```json
{
  "message": "Player 'Lionel Messi' removed from watchlist",
  "player_id": 1,
  "player_name": "Lionel Messi"
}
```

**Error Responses:**
- `404 Not Found`: Player doesn't exist
- `401 Unauthorized`: Invalid/missing token

**Note:** Removing a player not in the watchlist is idempotent (won't error)

---

#### Frontend Watchlist Component Example

```typescript
class WatchlistService {
  private baseUrl = 'http://localhost:8000/api/v1';

  async getWatchlist(token: string) {
    const response = await fetch(`${this.baseUrl}/watchlist/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  }

  async addToWatchlist(playerId: number, token: string) {
    const response = await fetch(`${this.baseUrl}/watchlist/${playerId}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  }

  async removeFromWatchlist(playerId: number, token: string) {
    const response = await fetch(`${this.baseUrl}/watchlist/${playerId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  }

  async toggleWatchlist(playerId: number, isInWatchlist: boolean, token: string) {
    return isInWatchlist
      ? this.removeFromWatchlist(playerId, token)
      : this.addToWatchlist(playerId, token);
  }
}
```

---

## Existing MVP v1 Features

### Simple Name Search

**Endpoint:** `GET /api/v1/players/search?name={query}`

**Authentication:** Required

**Query Parameter:**
- `name` (string, required): Search query (minimum 1 character)

**Response:** Array of players with matching first or last names

---

### Player Comparison

**Endpoint:** `GET /api/v1/players/compare?player_id_1={id1}&player_id_2={id2}`

**Authentication:** Required

**Query Parameters:**
- `player_id_1` (integer, required): First player ID
- `player_id_2` (integer, required): Second player ID

**Response:**
```json
{
  "player_1": { /* full player object */ },
  "player_2": { /* full player object */ },
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
    "player_1_wins": 3,
    "player_2_wins": 1,
    "ties": 1
  }
}
```

---

## Error Handling

### Standard HTTP Status Codes

- `200 OK`: Successful GET/DELETE request
- `201 Created`: Successful POST request
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Resource doesn't exist
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server-side error

### Error Response Format

All errors follow this structure:
```json
{
  "detail": "Detailed error message here"
}
```

### Validation Errors (422)
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "max_age"],
      "msg": "max_age must be greater than or equal to min_age"
    }
  ]
}
```

---

## Rate Limiting & Best Practices

### Token Management
- Store tokens securely (httpOnly cookies or secure storage)
- Implement token refresh before expiration (30 min lifetime)
- Handle 401 responses by redirecting to login
- Clear tokens on logout

### Performance Tips
- Use pagination for large lists (`skip` and `limit` parameters)
- Cache player data when appropriate
- Debounce search inputs to reduce API calls
- Use watchlist for frequently accessed players

### CORS
The API is configured to accept requests from allowed origins. Ensure your frontend domain is whitelisted.

---

## Complete Frontend Flow Example

### React TypeScript Example

```typescript
import { useState, useEffect } from 'react';

interface Player {
  id: number;
  full_name: string;
  position: string;
  current_club: string;
  age: number;
}

function PlayerSearch() {
  const [token, setToken] = useState<string>('');
  const [watchlist, setWatchlist] = useState<Player[]>([]);
  const [searchResults, setSearchResults] = useState<Player[]>([]);

  // 1. Authentication
  async function login(email: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch('http://localhost:8000/api/v1/login/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });

    const data = await response.json();
    setToken(data.access_token);
    localStorage.setItem('token', data.access_token);
  }

  // 2. Advanced Search
  async function searchPlayers(club?: string, position?: string, minAge?: number) {
    const response = await fetch('http://localhost:8000/api/v1/players/search/advanced', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ club, position, min_age: minAge })
    });

    const results = await response.json();
    setSearchResults(results);
  }

  // 3. Watchlist Management
  async function loadWatchlist() {
    const response = await fetch('http://localhost:8000/api/v1/watchlist/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const data = await response.json();
    setWatchlist(data);
  }

  async function addToWatchlist(playerId: number) {
    await fetch(`http://localhost:8000/api/v1/watchlist/${playerId}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });

    loadWatchlist(); // Refresh watchlist
  }

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
      loadWatchlist();
    }
  }, []);

  return (
    <div>
      <h2>Advanced Player Search</h2>
      {/* Search form and results display */}

      <h2>My Watchlist ({watchlist.length})</h2>
      {watchlist.map(player => (
        <div key={player.id}>
          {player.full_name} - {player.position} - {player.current_club}
        </div>
      ))}
    </div>
  );
}
```

---

## Testing with Swagger UI

The easiest way to test and understand the API:

1. **Navigate to**: `http://localhost:8000/docs`
2. **Create a user**: Use `POST /api/v1/users/` endpoint
3. **Login**: Use `POST /api/v1/login/token` to get a token
4. **Authorize**: Click the "Authorize" button (top right) and paste your token
5. **Test endpoints**: All protected endpoints will now work with your token

---

## API Schema

Full OpenAPI schema available at:
- `http://localhost:8000/api/v1/openapi.json`

This can be imported into Postman, Insomnia, or used to generate TypeScript types.

---

## Support & Issues

- **API Documentation**: `/docs` (Swagger UI)
- **Health Check**: `/health`
- **Version Info**: `/info`

For backend issues or questions, contact the backend development team.

---

## Summary Checklist for Frontend Team

- [ ] Set up authentication flow (register → login → store token)
- [ ] Implement token refresh logic (before 30-min expiration)
- [ ] Build advanced search UI with filter controls
- [ ] Implement watchlist management (add/remove/display)
- [ ] Handle all error cases (401, 404, 422, 500)
- [ ] Test with Swagger UI first to understand responses
- [ ] Implement loading states for async operations
- [ ] Add error messaging for failed requests
- [ ] Cache frequently accessed data
- [ ] Implement proper logout (clear tokens)

---

**Version**: 2.0
**Last Updated**: 2025-01-17
**API Status**: Staging Candidate - Awaiting Green Build
**Deployment**: Pending CI/CD Pipeline Success
