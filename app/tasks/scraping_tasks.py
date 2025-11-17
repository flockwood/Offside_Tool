"""
Celery tasks for scraping and data processing.

These tasks run asynchronously to scrape player data, update statistics,
and perform maintenance operations.
"""
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime, timedelta
from celery import Task
from sqlalchemy import select

from app.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.player import Player
from app.crud.player import player as player_crud
from app.scrapers.transfermarkt import TransfermarktScraper
from app.schemas.player import PlayerCreate, PlayerUpdate


logger = logging.getLogger(__name__)


class AsyncTask(Task):
    """
    Base task class that handles async operations.

    Provides a run method that executes async functions in the Celery worker.
    """

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the task.

        This method should be overridden in subclasses.
        """
        raise NotImplementedError("Subclasses must implement the run method")


@celery_app.task(name="app.tasks.scraping_tasks.scrape_transfermarkt_player", bind=True)
def scrape_transfermarkt_player(self, player_name: str, update_existing: bool = True) -> Dict[str, Any]:
    """
    Scrape a specific player from Transfermarkt and save to database.

    Args:
        player_name: Name of the player to scrape
        update_existing: If True, update existing player; if False, skip if exists

    Returns:
        Dict with task results
    """
    task_id = self.request.id

    logger.info(f"Task {task_id}: Scraping player '{player_name}' from Transfermarkt")

    result = asyncio.run(_scrape_and_save_player(player_name, update_existing))

    return {
        "task_id": task_id,
        "task_name": "scrape_transfermarkt_player",
        "player_name": player_name,
        "status": result["status"],
        "timestamp": datetime.utcnow().isoformat(),
        "player_data": result.get("player_data"),
        "error": result.get("error"),
    }


async def _scrape_and_save_player(player_name: str, update_existing: bool) -> Dict[str, Any]:
    """
    Async helper to scrape and save player data.

    Args:
        player_name: Name of player to scrape
        update_existing: Whether to update if player exists

    Returns:
        Dict with status and player data
    """
    try:
        # Scrape player data
        async with TransfermarktScraper() as scraper:
            player_data = await scraper.scrape(player_name)

        if not player_data:
            return {
                "status": "not_found",
                "error": f"Player '{player_name}' not found on Transfermarkt",
            }

        # Ensure required fields
        if not player_data.get("first_name") or not player_data.get("position"):
            return {
                "status": "error",
                "error": "Missing required fields in scraped data",
                "player_data": player_data,
            }

        async with AsyncSessionLocal() as db:
            try:
                # Check if player already exists
                existing_player = await player_crud.get_by_name(
                    db,
                    first_name=player_data["first_name"],
                    last_name=player_data.get("last_name", ""),
                )

                if existing_player:
                    if not update_existing:
                        logger.info(f"Player {player_name} already exists, skipping")
                        return {
                            "status": "skipped",
                            "player_data": {
                                "id": existing_player.id,
                                "name": existing_player.full_name,
                            },
                        }

                    # Update existing player
                    update_data = PlayerUpdate(**player_data)
                    updated_player = await player_crud.update(
                        db, db_obj=existing_player, obj_in=update_data
                    )
                    await db.commit()

                    logger.info(f"Updated player: {updated_player.full_name}")
                    return {
                        "status": "updated",
                        "player_data": {
                            "id": updated_player.id,
                            "name": updated_player.full_name,
                            "position": updated_player.position.value,
                            "club": updated_player.current_club,
                        },
                    }

                else:
                    # Create new player
                    player_in = PlayerCreate(**player_data)
                    new_player = await player_crud.create(db, obj_in=player_in)
                    await db.commit()

                    logger.info(f"Created new player: {new_player.full_name}")
                    return {
                        "status": "created",
                        "player_data": {
                            "id": new_player.id,
                            "name": new_player.full_name,
                            "position": new_player.position.value,
                            "club": new_player.current_club,
                        },
                    }

            except Exception as e:
                await db.rollback()
                logger.error(f"Database error: {e}")
                raise

    except Exception as e:
        logger.error(f"Error scraping player {player_name}: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@celery_app.task(name="app.tasks.scraping_tasks.scrape_player_list", bind=True)
def scrape_player_list(self, player_names: List[str], update_existing: bool = True) -> Dict[str, Any]:
    """
    Scrape multiple players from Transfermarkt.

    Args:
        player_names: List of player names to scrape
        update_existing: If True, update existing players

    Returns:
        Dict with task results
    """
    task_id = self.request.id

    logger.info(f"Task {task_id}: Scraping {len(player_names)} players from Transfermarkt")

    results = asyncio.run(_scrape_multiple_players(player_names, update_existing))

    summary = {
        "created": sum(1 for r in results if r["status"] == "created"),
        "updated": sum(1 for r in results if r["status"] == "updated"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "errors": sum(1 for r in results if r["status"] == "error"),
        "not_found": sum(1 for r in results if r["status"] == "not_found"),
    }

    return {
        "task_id": task_id,
        "task_name": "scrape_player_list",
        "timestamp": datetime.utcnow().isoformat(),
        "total_players": len(player_names),
        "summary": summary,
        "results": results,
    }


async def _scrape_multiple_players(player_names: List[str], update_existing: bool) -> List[Dict[str, Any]]:
    """
    Async helper to scrape multiple players.

    Args:
        player_names: List of player names
        update_existing: Whether to update existing players

    Returns:
        List of results for each player
    """
    results = []

    async with TransfermarktScraper() as scraper:
        for player_name in player_names:
            try:
                logger.info(f"Scraping player: {player_name}")
                result = await _scrape_and_save_player_with_scraper(
                    scraper, player_name, update_existing
                )
                results.append({
                    "player_name": player_name,
                    **result
                })

                # Rate limiting: wait between players
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error scraping {player_name}: {e}")
                results.append({
                    "player_name": player_name,
                    "status": "error",
                    "error": str(e),
                })

    return results


async def _scrape_and_save_player_with_scraper(
    scraper: TransfermarktScraper,
    player_name: str,
    update_existing: bool
) -> Dict[str, Any]:
    """
    Scrape and save player using existing scraper instance.

    Args:
        scraper: TransfermarktScraper instance
        player_name: Player name
        update_existing: Whether to update existing

    Returns:
        Result dictionary
    """
    try:
        player_data = await scraper.scrape(player_name)

        if not player_data:
            return {
                "status": "not_found",
                "error": f"Player '{player_name}' not found",
            }

        if not player_data.get("first_name") or not player_data.get("position"):
            return {
                "status": "error",
                "error": "Missing required fields",
            }

        async with AsyncSessionLocal() as db:
            existing_player = await player_crud.get_by_name(
                db,
                first_name=player_data["first_name"],
                last_name=player_data.get("last_name", ""),
            )

            if existing_player:
                if not update_existing:
                    return {
                        "status": "skipped",
                        "player_id": existing_player.id,
                    }

                update_data = PlayerUpdate(**player_data)
                updated_player = await player_crud.update(
                    db, db_obj=existing_player, obj_in=update_data
                )
                await db.commit()

                return {
                    "status": "updated",
                    "player_id": updated_player.id,
                    "name": updated_player.full_name,
                }

            else:
                player_in = PlayerCreate(**player_data)
                new_player = await player_crud.create(db, obj_in=player_in)
                await db.commit()

                return {
                    "status": "created",
                    "player_id": new_player.id,
                    "name": new_player.full_name,
                }

    except Exception as e:
        logger.error(f"Error processing {player_name}: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@celery_app.task(name="app.tasks.scraping_tasks.scrape_player_statistics", bind=True)
def scrape_player_statistics(self) -> Dict[str, Any]:
    """
    Scrape and update player statistics from external sources.

    This task updates statistics for all existing players in the database.

    Returns:
        Dict with task results and statistics
    """
    task_id = self.request.id

    logger.info(f"Task {task_id}: Updating player statistics from Transfermarkt")

    result = asyncio.run(_update_all_player_stats())

    return {
        "task_id": task_id,
        "task_name": "scrape_player_statistics",
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        **result,
    }


async def _update_all_player_stats() -> Dict[str, Any]:
    """
    Update statistics for all players in database.

    Returns:
        Summary of updates
    """
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Player))
            players = result.scalars().all()

            updated_count = 0
            error_count = 0

            async with TransfermarktScraper() as scraper:
                for player in players:
                    try:
                        full_name = player.full_name
                        player_data = await scraper.scrape(full_name)

                        if player_data:
                            update_data = PlayerUpdate(**player_data)
                            await player_crud.update(db, db_obj=player, obj_in=update_data)
                            updated_count += 1

                        await asyncio.sleep(2)  # Rate limiting

                    except Exception as e:
                        logger.error(f"Error updating {player.full_name}: {e}")
                        error_count += 1

            await db.commit()

            return {
                "total_players": len(players),
                "updated": updated_count,
                "errors": error_count,
            }

        except Exception as e:
            await db.rollback()
            raise e


@celery_app.task(name="app.tasks.scraping_tasks.update_player_ratings", bind=True)
def update_player_ratings(self) -> Dict[str, Any]:
    """
    Update player ratings based on recent performance.

    This task recalculates player ratings using a weighted algorithm
    based on recent matches, goals, assists, and other metrics.

    Returns:
        Dict with task results
    """
    task_id = self.request.id

    # Run the async update function
    updated_count = asyncio.run(_update_ratings_async())

    return {
        "task_id": task_id,
        "task_name": "update_player_ratings",
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "players_updated": updated_count,
    }


async def _update_ratings_async() -> int:
    """
    Async helper to update player ratings.

    Returns:
        Number of players updated
    """
    async with AsyncSessionLocal() as db:
        try:
            # Get all players
            result = await db.execute(select(Player))
            players = result.scalars().all()

            updated_count = 0

            for player in players:
                # Calculate new rating based on performance metrics
                # This is a simple example - you would use a more sophisticated algorithm
                if player.matches_played > 0:
                    base_rating = 5.0

                    # Goals contribution
                    goals_contribution = min((player.goals / player.matches_played) * 2, 3.0)

                    # Assists contribution
                    assists_contribution = min((player.assists / player.matches_played) * 1.5, 2.0)

                    # Calculate final rating (0-10 scale)
                    new_rating = min(base_rating + goals_contribution + assists_contribution, 10.0)

                    player.rating = round(new_rating, 2)
                    updated_count += 1

            await db.commit()
            return updated_count

        except Exception as e:
            await db.rollback()
            raise e


@celery_app.task(name="app.tasks.scraping_tasks.cleanup_old_data", bind=True)
def cleanup_old_data(self) -> Dict[str, Any]:
    """
    Clean up old or stale data from the database.

    This task removes outdated records and performs database maintenance.

    Returns:
        Dict with cleanup results
    """
    task_id = self.request.id

    # Run the async cleanup function
    deleted_count = asyncio.run(_cleanup_async())

    return {
        "task_id": task_id,
        "task_name": "cleanup_old_data",
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "records_deleted": deleted_count,
    }


async def _cleanup_async() -> int:
    """
    Async helper to clean up old data.

    Returns:
        Number of records deleted
    """
    async with AsyncSessionLocal() as db:
        try:
            # Example: Delete players with no matches played and created over a year ago
            one_year_ago = datetime.utcnow() - timedelta(days=365)

            result = await db.execute(
                select(Player).where(
                    Player.matches_played == 0,
                    Player.created_at < one_year_ago
                )
            )
            old_players = result.scalars().all()

            deleted_count = len(old_players)

            for player in old_players:
                await db.delete(player)

            await db.commit()
            return deleted_count

        except Exception as e:
            await db.rollback()
            raise e


@celery_app.task(name="app.tasks.scraping_tasks.import_players_bulk", bind=True)
def import_players_bulk(self, players_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Import multiple players from external data source.

    Args:
        players_data: List of player dictionaries

    Returns:
        Dict with import results
    """
    task_id = self.request.id

    imported_count = asyncio.run(_import_players_async(players_data))

    return {
        "task_id": task_id,
        "task_name": "import_players_bulk",
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "players_imported": imported_count,
        "total_received": len(players_data),
    }


async def _import_players_async(players_data: List[Dict[str, Any]]) -> int:
    """
    Async helper to import players in bulk.

    Args:
        players_data: List of player dictionaries

    Returns:
        Number of players imported
    """
    async with AsyncSessionLocal() as db:
        try:
            imported_count = 0

            for player_data in players_data:
                # Check if player already exists
                existing_player = await player_crud.get_by_name(
                    db,
                    first_name=player_data.get("first_name", ""),
                    last_name=player_data.get("last_name", ""),
                )

                if not existing_player:
                    # Create new player
                    new_player = Player(**player_data)
                    db.add(new_player)
                    imported_count += 1

            await db.commit()
            return imported_count

        except Exception as e:
            await db.rollback()
            raise e


@celery_app.task(name="app.tasks.scraping_tasks.generate_analytics_report", bind=True)
def generate_analytics_report(self) -> Dict[str, Any]:
    """
    Generate comprehensive analytics report.

    This task generates various statistics and insights about players.

    Returns:
        Dict with analytics data
    """
    task_id = self.request.id

    analytics = asyncio.run(_generate_analytics_async())

    return {
        "task_id": task_id,
        "task_name": "generate_analytics_report",
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "analytics": analytics,
    }


async def _generate_analytics_async() -> Dict[str, Any]:
    """
    Async helper to generate analytics.

    Returns:
        Dict with analytics data
    """
    async with AsyncSessionLocal() as db:
        try:
            # Get overall statistics
            stats = await player_crud.get_statistics(db)

            # Get top scorers
            top_scorers = await player_crud.get_top_scorers(db, limit=10)

            # Build analytics report
            analytics = {
                "overview": stats,
                "top_scorers": [
                    {
                        "name": f"{player.first_name} {player.last_name}",
                        "goals": player.goals,
                        "club": player.current_club,
                    }
                    for player in top_scorers
                ],
            }

            return analytics

        except Exception as e:
            raise e
