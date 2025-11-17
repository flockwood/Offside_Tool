"""
Base scraper class with common functionality.

Provides rate limiting, error handling, and retry logic for all scrapers.
"""
import asyncio
import logging
from typing import Optional, Any, Dict
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import httpx
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class RateLimitError(ScraperError):
    """Raised when rate limit is exceeded."""
    pass


class ParsingError(ScraperError):
    """Raised when data parsing fails."""
    pass


class BaseScraper(ABC):
    """
    Base class for all web scrapers.

    Provides common functionality for HTTP requests, rate limiting,
    and error handling.
    """

    def __init__(
        self,
        base_url: str,
        rate_limit_delay: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize the scraper.

        Args:
            base_url: Base URL for the website
            rate_limit_delay: Delay between requests in seconds
            timeout: HTTP timeout in seconds
            max_retries: Maximum number of retries for failed requests
            user_agent: Custom user agent string
        """
        self.base_url = base_url.rstrip("/")
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.last_request_time: Optional[datetime] = None

        # Default user agent
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # HTTP client
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def _rate_limit(self) -> None:
        """
        Enforce rate limiting between requests.

        Ensures minimum delay between consecutive requests.
        """
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)

        self.last_request_time = datetime.now()

    async def fetch(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        retries: int = 0,
    ) -> httpx.Response:
        """
        Fetch a URL with rate limiting and retry logic.

        Args:
            url: URL to fetch
            params: Query parameters
            retries: Current retry attempt

        Returns:
            HTTP response

        Raises:
            ScraperError: If fetching fails after all retries
        """
        if not self.client:
            raise ScraperError("Scraper not initialized. Use async context manager.")

        # Enforce rate limiting
        await self._rate_limit()

        try:
            logger.info(f"Fetching URL: {url}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit
                if retries < self.max_retries:
                    wait_time = 2 ** retries  # Exponential backoff
                    logger.warning(
                        f"Rate limited. Waiting {wait_time}s before retry {retries + 1}/{self.max_retries}"
                    )
                    await asyncio.sleep(wait_time)
                    return await self.fetch(url, params, retries + 1)
                raise RateLimitError("Rate limit exceeded after all retries")

            elif e.response.status_code >= 500:  # Server error
                if retries < self.max_retries:
                    wait_time = 2 ** retries
                    logger.warning(
                        f"Server error. Retrying in {wait_time}s ({retries + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    return await self.fetch(url, params, retries + 1)

            logger.error(f"HTTP error fetching {url}: {e}")
            raise ScraperError(f"HTTP error: {e}")

        except httpx.RequestError as e:
            if retries < self.max_retries:
                wait_time = 2 ** retries
                logger.warning(
                    f"Request error. Retrying in {wait_time}s ({retries + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)
                return await self.fetch(url, params, retries + 1)

            logger.error(f"Request error fetching {url}: {e}")
            raise ScraperError(f"Request error: {e}")

    async def fetch_soup(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> BeautifulSoup:
        """
        Fetch a URL and return parsed BeautifulSoup object.

        Args:
            url: URL to fetch
            params: Query parameters

        Returns:
            Parsed HTML as BeautifulSoup object
        """
        response = await self.fetch(url, params)
        return BeautifulSoup(response.text, "html.parser")

    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ""
        return " ".join(text.strip().split())

    @staticmethod
    def parse_number(text: Optional[str]) -> Optional[int]:
        """
        Parse a number from text.

        Args:
            text: Text containing a number

        Returns:
            Parsed number or None
        """
        if not text:
            return None

        # Remove common formatting
        cleaned = text.replace(",", "").replace(".", "").strip()

        try:
            return int(cleaned)
        except ValueError:
            logger.warning(f"Failed to parse number: {text}")
            return None

    @staticmethod
    def parse_currency(text: Optional[str]) -> Optional[float]:
        """
        Parse currency value from text.

        Args:
            text: Text containing currency (e.g., "€35.00m", "$50M")

        Returns:
            Parsed value in base currency or None
        """
        if not text:
            return None

        # Remove currency symbols and whitespace
        cleaned = text.replace("€", "").replace("$", "").replace("£", "").strip()

        try:
            # Handle millions (m, M)
            if "m" in cleaned.lower():
                return float(cleaned.lower().replace("m", "")) * 1_000_000

            # Handle thousands (k, K)
            if "k" in cleaned.lower():
                return float(cleaned.lower().replace("k", "")) * 1_000

            # Handle billions (bn, B)
            if "bn" in cleaned.lower() or "b" in cleaned.lower():
                return float(cleaned.lower().replace("bn", "").replace("b", "")) * 1_000_000_000

            # Direct number
            return float(cleaned)

        except ValueError:
            logger.warning(f"Failed to parse currency: {text}")
            return None

    @abstractmethod
    async def scrape(self, *args, **kwargs) -> Any:
        """
        Abstract method for scraping logic.

        Must be implemented by subclasses.
        """
        pass
