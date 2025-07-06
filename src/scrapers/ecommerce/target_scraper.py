from typing import List
from ...core.base_scraper import BaseScraper, ProductResult, ScraperType

class TargetScraper(BaseScraper):
    def __init__(self):
        super().__init__(name="Target", scraper_type=ScraperType.ECOMMERCE, base_url="https://target.com", supported_countries=['US'], rate_limit=2.0)
    def is_supported_country(self, country: str) -> bool:
        return country.upper() == 'US'
    def build_search_url(self, query: str, country: str, **kwargs) -> str:
        return f"https://www.target.com/s?searchTerm={query}"
    async def search(self, query: str, country: str, **kwargs) -> List[ProductResult]:
        return []