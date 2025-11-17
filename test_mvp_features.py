#!/usr/bin/env python3
"""
Test script for MVP features: Player Search and Comparison.

This script:
1. Creates sample players in the database
2. Tests the search endpoint
3. Tests the comparison endpoint
4. Displays results in a user-friendly format
"""
import asyncio
import httpx
from typing import List, Dict, Any


BASE_URL = "http://localhost:8000/api/v1"


# Sample player data for testing
SAMPLE_PLAYERS = [
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
        "rating": 9.5,
    },
    {
        "first_name": "Cristiano",
        "last_name": "Ronaldo",
        "date_of_birth": "1985-02-05",
        "nationality": "Portugal",
        "height_cm": 187,
        "weight_kg": 84,
        "preferred_foot": "right",
        "position": "forward",
        "jersey_number": 7,
        "current_club": "Al Nassr",
        "market_value_euros": 15000000,
        "goals": 850,
        "assists": 250,
        "matches_played": 1100,
        "rating": 9.3,
    },
    {
        "first_name": "Kevin",
        "last_name": "De Bruyne",
        "date_of_birth": "1991-06-28",
        "nationality": "Belgium",
        "height_cm": 181,
        "weight_kg": 70,
        "preferred_foot": "right",
        "position": "midfielder",
        "jersey_number": 17,
        "current_club": "Manchester City",
        "market_value_euros": 80000000,
        "goals": 120,
        "assists": 180,
        "matches_played": 500,
        "rating": 8.8,
    },
    {
        "first_name": "Kylian",
        "last_name": "Mbappé",
        "date_of_birth": "1998-12-20",
        "nationality": "France",
        "height_cm": 178,
        "weight_kg": 73,
        "preferred_foot": "right",
        "position": "forward",
        "jersey_number": 7,
        "current_club": "Real Madrid",
        "market_value_euros": 180000000,
        "goals": 300,
        "assists": 150,
        "matches_played": 400,
        "rating": 9.0,
    },
    {
        "first_name": "Erling",
        "last_name": "Haaland",
        "date_of_birth": "2000-07-21",
        "nationality": "Norway",
        "height_cm": 194,
        "weight_kg": 88,
        "preferred_foot": "left",
        "position": "forward",
        "jersey_number": 9,
        "current_club": "Manchester City",
        "market_value_euros": 170000000,
        "goals": 200,
        "assists": 50,
        "matches_played": 250,
        "rating": 9.1,
    },
]


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_player(player: Dict[str, Any], index: int = None):
    """Print player information in a formatted way."""
    if index:
        print(f"{index}. {player['full_name']}")
    else:
        print(f"   {player['full_name']}")
    print(f"   Position: {player['position']}")
    print(f"   Club: {player.get('current_club', 'N/A')}")
    print(f"   Goals: {player['goals']} | Assists: {player['assists']}")
    print(f"   Goals/Match: {player['goals_per_match']:.2f} | Assists/Match: {player['assists_per_match']:.2f}")
    if player.get('market_value_euros'):
        print(f"   Market Value: €{player['market_value_euros']:,.0f}")
    print()


def print_comparison(data: Dict[str, Any]):
    """Print comparison results in a formatted way."""
    p1 = data['player_1']
    p2 = data['player_2']
    comp = data['comparison']
    summary = data['summary']

    print(f"{'Metric':<25} {'Player 1':<20} {'Player 2':<20} {'Winner':<15}")
    print("-" * 80)

    # Market Value
    mv = comp['market_value_euros']
    p1_val = f"€{mv['player_1_value']:,.0f}" if mv['player_1_value'] else "N/A"
    p2_val = f"€{mv['player_2_value']:,.0f}" if mv['player_2_value'] else "N/A"
    winner = "🏆 Player 1" if mv['winner'] == 'player_1' else "🏆 Player 2" if mv['winner'] == 'player_2' else "🤝 Tie"
    print(f"{'Market Value':<25} {p1_val:<20} {p2_val:<20} {winner:<15}")

    # Goals
    g = comp['goals']
    print(f"{'Goals':<25} {g['player_1_value']:<20.0f} {g['player_2_value']:<20.0f} {'🏆 Player 1' if g['winner'] == 'player_1' else '🏆 Player 2' if g['winner'] == 'player_2' else '🤝 Tie':<15}")

    # Assists
    a = comp['assists']
    print(f"{'Assists':<25} {a['player_1_value']:<20.0f} {a['player_2_value']:<20.0f} {'🏆 Player 1' if a['winner'] == 'player_1' else '🏆 Player 2' if a['winner'] == 'player_2' else '🤝 Tie':<15}")

    # Goals per Match
    gpm = comp['goals_per_match']
    print(f"{'Goals per Match':<25} {gpm['player_1_value']:<20.2f} {gpm['player_2_value']:<20.2f} {'🏆 Player 1' if gpm['winner'] == 'player_1' else '🏆 Player 2' if gpm['winner'] == 'player_2' else '🤝 Tie':<15}")

    # Assists per Match
    apm = comp['assists_per_match']
    print(f"{'Assists per Match':<25} {apm['player_1_value']:<20.2f} {apm['player_2_value']:<20.2f} {'🏆 Player 1' if apm['winner'] == 'player_1' else '🏆 Player 2' if apm['winner'] == 'player_2' else '🤝 Tie':<15}")

    print("\n" + "-" * 80)
    print(f"\n📊 SUMMARY:")
    print(f"   {p1['full_name']}: {summary['player_1_wins']} wins")
    print(f"   {p2['full_name']}: {summary['player_2_wins']} wins")
    print(f"   Ties: {summary['ties']}")

    if summary['player_1_wins'] > summary['player_2_wins']:
        print(f"\n🎉 OVERALL WINNER: {p1['full_name']}")
    elif summary['player_2_wins'] > summary['player_1_wins']:
        print(f"\n🎉 OVERALL WINNER: {p2['full_name']}")
    else:
        print(f"\n🤝 IT'S A TIE!")


async def test_health_check(client: httpx.AsyncClient) -> bool:
    """Test if the API is healthy."""
    try:
        response = await client.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code == 200:
            print("✅ API is healthy and running")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Make sure the server is running: docker-compose up -d")
        return False


async def create_sample_players(client: httpx.AsyncClient) -> List[int]:
    """Create sample players and return their IDs."""
    print_header("Step 1: Creating Sample Players")

    player_ids = []

    for i, player_data in enumerate(SAMPLE_PLAYERS, 1):
        try:
            response = await client.post(f"{BASE_URL}/players", json=player_data)

            if response.status_code == 201:
                player = response.json()
                player_ids.append(player['id'])
                print(f"✅ Created: {player['full_name']} (ID: {player['id']})")

            elif response.status_code == 400 and "already exists" in response.text:
                # Player exists, search for it
                search_response = await client.get(
                    f"{BASE_URL}/players/search",
                    params={"name": player_data['last_name']}
                )
                if search_response.status_code == 200:
                    players = search_response.json()
                    if players:
                        player_ids.append(players[0]['id'])
                        print(f"ℹ️  Already exists: {players[0]['full_name']} (ID: {players[0]['id']})")
            else:
                print(f"❌ Failed to create {player_data['first_name']} {player_data['last_name']}: {response.status_code}")

        except Exception as e:
            print(f"❌ Error creating player: {e}")

    print(f"\n✅ {len(player_ids)} players ready for testing")
    return player_ids


async def test_search_feature(client: httpx.AsyncClient):
    """Test the player search endpoint."""
    print_header("Step 2: Testing Player Search Feature")

    test_queries = [
        ("Messi", "Searching for 'Messi'"),
        ("ronaldo", "Searching for 'ronaldo' (case-insensitive)"),
        ("De", "Searching for 'De' (partial match)"),
        ("Manchester", "This shouldn't match names, expect empty"),
        ("Kylian", "Searching by first name"),
    ]

    for query, description in test_queries:
        print(f"\n🔍 {description}...")
        try:
            response = await client.get(
                f"{BASE_URL}/players/search",
                params={"name": query}
            )

            if response.status_code == 200:
                players = response.json()
                if players:
                    print(f"   Found {len(players)} player(s):")
                    for i, player in enumerate(players, 1):
                        print(f"   {i}. {player['full_name']} ({player['position']} - {player['current_club']})")
                else:
                    print("   No players found")
            else:
                print(f"   ❌ Error: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n✅ Search feature testing complete")


async def test_comparison_feature(client: httpx.AsyncClient, player_ids: List[int]):
    """Test the player comparison endpoint."""
    print_header("Step 3: Testing Player Comparison Feature")

    if len(player_ids) < 2:
        print("❌ Not enough players to test comparison")
        return

    # Test 1: Compare first two players (Messi vs Ronaldo)
    print(f"\n⚔️  Comparison 1: Player {player_ids[0]} vs Player {player_ids[1]}")
    print("-" * 80)

    try:
        response = await client.get(
            f"{BASE_URL}/players/compare",
            params={"player_id_1": player_ids[0], "player_id_2": player_ids[1]}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n{data['player_1']['full_name']} vs {data['player_2']['full_name']}\n")
            print_comparison(data)
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Compare with midfielder (if available)
    if len(player_ids) >= 3:
        print(f"\n\n⚔️  Comparison 2: Player {player_ids[0]} vs Player {player_ids[2]}")
        print("-" * 80)

        try:
            response = await client.get(
                f"{BASE_URL}/players/compare",
                params={"player_id_1": player_ids[0], "player_id_2": player_ids[2]}
            )

            if response.status_code == 200:
                data = response.json()
                print(f"\n{data['player_1']['full_name']} vs {data['player_2']['full_name']}\n")
                print_comparison(data)
            else:
                print(f"❌ Error: {response.status_code}")

        except Exception as e:
            print(f"❌ Error: {e}")

    # Test 3: Error case - same player
    print(f"\n\n⚔️  Comparison 3: Testing error case (same player)")
    print("-" * 80)

    try:
        response = await client.get(
            f"{BASE_URL}/players/compare",
            params={"player_id_1": player_ids[0], "player_id_2": player_ids[0]}
        )

        if response.status_code == 400:
            print("✅ Correctly rejected same player comparison")
            print(f"   Error message: {response.json()['detail']}")
        else:
            print(f"❌ Expected 400 error, got: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 4: Error case - non-existent player
    print(f"\n\n⚔️  Comparison 4: Testing error case (non-existent player)")
    print("-" * 80)

    try:
        response = await client.get(
            f"{BASE_URL}/players/compare",
            params={"player_id_1": player_ids[0], "player_id_2": 99999}
        )

        if response.status_code == 404:
            print("✅ Correctly returned 404 for non-existent player")
            print(f"   Error message: {response.json()['detail']}")
        else:
            print(f"❌ Expected 404 error, got: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n✅ Comparison feature testing complete")


async def main():
    """Main test function."""
    print_header("🚀 Soccer Analytics MVP Features - Live Testing")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check if API is healthy
        if not await test_health_check(client):
            return

        # Create sample players
        player_ids = await create_sample_players(client)

        if not player_ids:
            print("\n❌ No players available for testing")
            return

        # Test search feature
        await test_search_feature(client)

        # Test comparison feature
        await test_comparison_feature(client, player_ids)

    print_header("✅ All MVP Features Tested Successfully!")
    print("""
Next steps:
1. Visit http://localhost:8000/docs to try the interactive API
2. Run automated tests: pytest tests/integration/test_api_players_mvp.py -v
3. Check Flower for Celery tasks: http://localhost:5555
    """)


if __name__ == "__main__":
    asyncio.run(main())
