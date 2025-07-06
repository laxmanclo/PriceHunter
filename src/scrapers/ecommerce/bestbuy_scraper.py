"""
Best Buy scraper for price comparison.
"""

from typing import List
from ...core.base_scraper import BaseScraper, ProductResult, ScraperType


class BestBuyScraper(BaseScraper):
    """Best Buy scraper."""

    def __init__(self):
        super().__init__(
            name="BestBuy",
            scraper_type=ScraperType.ECOMMERCE,
            base_url="https://bestbuy.com",
            supported_countries=['US'],
            rate_limit=2.0
        )

    def is_supported_country(self, country: str) -> bool:
        return country.upper() == 'US'

    def build_search_url(self, query: str, country: str, **kwargs) -> str:
        return f"https://www.bestbuy.com/site/searchpage.jsp?st={query}"

    async def search(self, query: str, country: str, **kwargs) -> List[ProductResult]:
        # Placeholder implementation
        return []