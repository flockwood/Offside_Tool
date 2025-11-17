"""
Transfermarkt scraper for player data.

Scrapes player information from Transfermarkt.com including:
- Personal information
- Career statistics
- Market value
- Contract details
"""
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup, Tag

from app.scrapers.base import BaseScraper, ParsingError
from app.models.player import PlayerPosition, PreferredFoot


logger = logging.getLogger(__name__)


class TransfermarktScraper(BaseScraper):
    """
    Scraper for Transfermarkt.com player data.

    Example URLs:
    - Player profile: https://www.transfermarkt.com/lionel-messi/profil/spieler/28003
    - Search: https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche
    """

    def __init__(self):
        """Initialize Transfermarkt scraper."""
        super().__init__(
            base_url="https://www.transfermarkt.com",
            rate_limit_delay=2.0,  # Be respectful to Transfermarkt servers
            timeout=30,
        )

    async def search_player(self, player_name: str) -> List[Dict[str, Any]]:
        """
        Search for a player by name.

        Args:
            player_name: Player name to search for

        Returns:
            List of player search results with basic info
        """
        search_url = f"{self.base_url}/schnellsuche/ergebnis/schnellsuche"
        params = {"query": player_name}

        soup = await self.fetch_soup(search_url, params)

        results = []
        # Find all player result rows
        player_rows = soup.select("table.items tbody tr")

        for row in player_rows:
            try:
                player_link = row.select_one("td.hauptlink a")
                if not player_link:
                    continue

                player_url = player_link.get("href", "")
                player_id = self._extract_player_id(player_url)

                result = {
                    "name": self.clean_text(player_link.text),
                    "player_id": player_id,
                    "url": f"{self.base_url}{player_url}" if player_url else None,
                }

                # Extract position if available
                position_cell = row.select_one("td.inline-table tr td")
                if position_cell:
                    result["position"] = self.clean_text(position_cell.text)

                # Extract club if available
                club_cell = row.select_one("td.zentriert img")
                if club_cell:
                    result["club"] = club_cell.get("alt", "")

                results.append(result)

            except Exception as e:
                logger.warning(f"Error parsing search result row: {e}")
                continue

        return results

    async def scrape_player(self, player_id: str) -> Dict[str, Any]:
        """
        Scrape detailed player information.

        Args:
            player_id: Transfermarkt player ID

        Returns:
            Dictionary with player data

        Raises:
            ParsingError: If parsing fails
        """
        url = f"{self.base_url}/player/profil/spieler/{player_id}"

        try:
            soup = await self.fetch_soup(url)
            return await self._parse_player_page(soup)

        except Exception as e:
            logger.error(f"Error scraping player {player_id}: {e}")
            raise ParsingError(f"Failed to scrape player {player_id}: {e}")

    async def _parse_player_page(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Parse player profile page.

        Args:
            soup: BeautifulSoup object of player page

        Returns:
            Parsed player data
        """
        data: Dict[str, Any] = {}

        # Extract name
        name_header = soup.select_one("h1.data-header__headline-wrapper")
        if name_header:
            full_name = self.clean_text(name_header.text)
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                data["first_name"] = " ".join(name_parts[:-1])
                data["last_name"] = name_parts[-1]
            else:
                data["first_name"] = full_name
                data["last_name"] = ""

        # Extract personal information from info table
        info_table = soup.select_one("div.info-table")
        if info_table:
            data.update(self._parse_info_table(info_table))

        # Extract market value
        market_value_div = soup.select_one("a.data-header__market-value-wrapper")
        if market_value_div:
            market_value_text = self.clean_text(market_value_div.text)
            data["market_value_euros"] = self.parse_currency(market_value_text)

        # Extract statistics
        stats_section = soup.select_one("div.box stats-box")
        if stats_section:
            data.update(self._parse_statistics(stats_section))

        # Extract position
        position_span = soup.select_one("span.info-table__content--bold")
        if position_span:
            position_text = self.clean_text(position_span.text)
            data["position"] = self._map_position(position_text)

        # Extract current club
        club_link = soup.select_one("span.data-header__club a")
        if club_link:
            data["current_club"] = self.clean_text(club_link.text)

        # Extract jersey number
        jersey_span = soup.select_one("span.data-header__shirt-number")
        if jersey_span:
            jersey_text = self.clean_text(jersey_span.text).replace("#", "")
            data["jersey_number"] = self.parse_number(jersey_text)

        return data

    def _parse_info_table(self, info_table: Tag) -> Dict[str, Any]:
        """
        Parse the player information table.

        Args:
            info_table: BeautifulSoup Tag for info table

        Returns:
            Dictionary with parsed info
        """
        info = {}

        info_rows = info_table.select("span.info-table__content")

        for i in range(0, len(info_rows), 2):
            if i + 1 >= len(info_rows):
                break

            label = self.clean_text(info_rows[i].text).lower()
            value = self.clean_text(info_rows[i + 1].text)

            # Date of birth
            if "date of birth" in label or "born" in label:
                date_match = re.search(r"(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})", value)
                if date_match:
                    try:
                        # Try multiple date formats
                        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]:
                            try:
                                date_obj = datetime.strptime(date_match.group(1), fmt)
                                info["date_of_birth"] = date_obj.strftime("%Y-%m-%d")
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {value} - {e}")

                # Extract age
                age_match = re.search(r"\((\d+)\)", value)
                if age_match:
                    info["age"] = int(age_match.group(1))

            # Height
            elif "height" in label:
                height_match = re.search(r"(\d+),?(\d+)", value)
                if height_match:
                    meters = float(f"{height_match.group(1)}.{height_match.group(2)}")
                    info["height_cm"] = int(meters * 100)

            # Nationality
            elif "citizenship" in label or "nationality" in label:
                info["nationality"] = value

            # Preferred foot
            elif "foot" in label:
                foot_text = value.lower()
                if "left" in foot_text:
                    info["preferred_foot"] = PreferredFoot.LEFT.value
                elif "right" in foot_text:
                    info["preferred_foot"] = PreferredFoot.RIGHT.value
                elif "both" in foot_text:
                    info["preferred_foot"] = PreferredFoot.BOTH.value

            # Contract expires
            elif "contract" in label:
                date_match = re.search(r"(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})", value)
                if date_match:
                    try:
                        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]:
                            try:
                                date_obj = datetime.strptime(date_match.group(1), fmt)
                                info["contract_expiry"] = date_obj.strftime("%Y-%m-% d")
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        logger.warning(f"Failed to parse contract date: {value} - {e}")

        return info

    def _parse_statistics(self, stats_section: Tag) -> Dict[str, Any]:
        """
        Parse player statistics section.

        Args:
            stats_section: BeautifulSoup Tag for statistics

        Returns:
            Dictionary with statistics
        """
        stats = {}

        # Find all stat boxes
        stat_boxes = stats_section.select("div.box-content")

        for box in stat_boxes:
            # Extract stat name and value
            stat_name_elem = box.select_one("div.box-heading")
            stat_value_elem = box.select_one("div.box-value")

            if not stat_name_elem or not stat_value_elem:
                continue

            stat_name = self.clean_text(stat_name_elem.text).lower()
            stat_value = self.clean_text(stat_value_elem.text)

            # Map statistics
            if "goals" in stat_name:
                stats["goals"] = self.parse_number(stat_value) or 0

            elif "assists" in stat_name:
                stats["assists"] = self.parse_number(stat_value) or 0

            elif "matches" in stat_name or "appearances" in stat_name:
                stats["matches_played"] = self.parse_number(stat_value) or 0

            elif "yellow cards" in stat_name:
                stats["yellow_cards"] = self.parse_number(stat_value) or 0

            elif "red cards" in stat_name:
                stats["red_cards"] = self.parse_number(stat_value) or 0

            elif "minutes" in stat_name:
                stats["minutes_played"] = self.parse_number(stat_value) or 0

        return stats

    def _map_position(self, position_text: str) -> str:
        """
        Map Transfermarkt position to our PlayerPosition enum.

        Args:
            position_text: Position text from Transfermarkt

        Returns:
            Mapped position value
        """
        position_lower = position_text.lower()

        if "goalkeeper" in position_lower or "gk" in position_lower:
            return PlayerPosition.GOALKEEPER.value

        elif any(
            word in position_lower
            for word in ["defender", "defence", "back", "cb", "lb", "rb"]
        ):
            return PlayerPosition.DEFENDER.value

        elif any(
            word in position_lower
            for word in ["midfielder", "midfield", "cm", "dm", "am"]
        ):
            return PlayerPosition.MIDFIELDER.value

        elif any(
            word in position_lower
            for word in ["forward", "striker", "winger", "attacker", "cf", "lw", "rw"]
        ):
            return PlayerPosition.FORWARD.value

        # Default to midfielder if unknown
        logger.warning(f"Unknown position: {position_text}, defaulting to midfielder")
        return PlayerPosition.MIDFIELDER.value

    @staticmethod
    def _extract_player_id(url: str) -> Optional[str]:
        """
        Extract player ID from Transfermarkt URL.

        Args:
            url: Transfermarkt player URL

        Returns:
            Player ID or None
        """
        match = re.search(r"/spieler/(\d+)", url)
        return match.group(1) if match else None

    async def scrape(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for and scrape a player by name.

        Args:
            player_name: Name of player to scrape

        Returns:
            Player data dictionary or None if not found
        """
        # First, search for the player
        search_results = await self.search_player(player_name)

        if not search_results:
            logger.warning(f"No results found for player: {player_name}")
            return None

        # Take the first result
        first_result = search_results[0]
        player_id = first_result.get("player_id")

        if not player_id:
            logger.error(f"No player ID found for: {player_name}")
            return None

        # Scrape detailed player data
        logger.info(f"Scraping player {player_name} (ID: {player_id})")
        return await self.scrape_player(player_id)
