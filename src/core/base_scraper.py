"""
Base scraper abstract class for all price scrapers.
Provides common functionality and interface for all scrapers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
import time
import random
from loguru import logger
from fake_useragent import UserAgent


class ScraperType(Enum):
    """Types of scrapers available."""
    ECOMMERCE = "ecommerce"
    REGIONAL = "regional"
    API = "api"
    SPECIALIZED = "specialized"


@dataclass
class ProductResult:
    """Standardized product result structure."""
    link: str
    price: str
    currency: str
    product_name: str
    availability: str = "In Stock"
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    seller: Optional[str] = None
    shipping_cost: Optional[str] = None
    delivery_time: Optional[str] = None
    image_url: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    confidence_score: float = 1.0
    source: str = ""
    scraped_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "link": self.link,
            "price": self.price,
            "currency": self.currency,
            "productName": self.product_name,
            "availability": self.availability,
            "rating": self.rating,
            "reviewsCount": self.reviews_count,
            "seller": self.seller,
            "shippingCost": self.shipping_cost,
            "deliveryTime": self.delivery_time,
            "imageUrl": self.image_url,
            "specifications": self.specifications,
            "confidenceScore": self.confidence_score,
            "source": self.source,
            "scrapedAt": self.scraped_at
        }


class BaseScraper(ABC):
    """Abstract base class for all price scrapers."""

    def __init__(self,
                 name: str,
                 scraper_type: ScraperType,
                 base_url: str,
                 supported_countries: List[str],
                 rate_limit: float = 2.0,
                 timeout: int = 30):
        """
        Initialize the base scraper.

        Args:
            name: Name of the scraper
            scraper_type: Type of scraper
            base_url: Base URL for the website
            supported_countries: List of supported country codes
            rate_limit: Delay between requests in seconds
            timeout: Request timeout in seconds
        """
        self.name = name
        self.scraper_type = scraper_type
        self.base_url = base_url
        self.supported_countries = supported_countries
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_agent = UserAgent()
        self.last_request_time = 0

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def initialize(self):
        """Initialize the scraper session."""
        if not self.session:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self._get_headers()
            )
            logger.info(f"Initialized {self.name} scraper")

    async def cleanup(self):
        """Cleanup the scraper session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info(f"Cleaned up {self.name} scraper")

    def _get_headers(self) -> Dict[str, str]:
        """Get randomized headers for requests."""
        return {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    async def _rate_limit_delay(self):
        """Apply rate limiting delay."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit:
            delay = self.rate_limit - time_since_last + random.uniform(0.1, 0.5)
            await asyncio.sleep(delay)
        self.last_request_time = time.time()

    @abstractmethod
    async def search(self, query: str, country: str, **kwargs) -> List[ProductResult]:
        """
        Search for products and return results.

        Args:
            query: Search query
            country: Country code (e.g., 'US', 'IN')
            **kwargs: Additional search parameters

        Returns:
            List of ProductResult objects
        """
        pass

    @abstractmethod
    def is_supported_country(self, country: str) -> bool:
        """Check if the country is supported by this scraper."""
        pass

    @abstractmethod
    def build_search_url(self, query: str, country: str, **kwargs) -> str:
        """Build the search URL for the given query and country."""
        pass

    def get_priority(self, country: str) -> int:
        """
        Get the priority of this scraper for the given country.
        Lower numbers = higher priority.
        """
        if country in self.supported_countries:
            return 1
        return 999  # Very low priority for unsupported countries