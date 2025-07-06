"""
Apple Store scraper for official Apple pricing.
High priority for Apple products across multiple regions.
"""

import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
from datetime import datetime
from bs4 import BeautifulSoup
from loguru import logger

from ...core.base_scraper import BaseScraper, ProductResult, ScraperType


class AppleStoreScraper(BaseScraper):
    """Apple Store scraper for official Apple pricing."""

    APPLE_DOMAINS = {
        'US': 'apple.com',
        'CA': 'apple.com/ca',
        'UK': 'apple.com/uk',
        'DE': 'apple.com/de',
        'FR': 'apple.com/fr',
        'IT': 'apple.com/it',
        'ES': 'apple.com/es',
        'JP': 'apple.com/jp',
        'IN': 'apple.com/in',
        'AU': 'apple.com/au',
        'SG': 'apple.com/sg',
        'HK': 'apple.com/hk'
    }

    CURRENCY_MAP = {
        'US': 'USD', 'CA': 'CAD', 'UK': 'GBP', 'DE': 'EUR', 'FR': 'EUR',
        'IT': 'EUR', 'ES': 'EUR', 'JP': 'JPY', 'IN': 'INR', 'AU': 'AUD',
        'SG': 'SGD', 'HK': 'HKD'
    }

    def __init__(self):
        """Initialize Apple Store scraper."""
        super().__init__(
            name="Apple Store",
            scraper_type=ScraperType.REGIONAL,
            base_url="https://apple.com",
            supported_countries=list(self.APPLE_DOMAINS.keys()),
            rate_limit=3.0,  # Be respectful to Apple
            timeout=30
        )

    def is_supported_country(self, country: str) -> bool:
        """Check if country is supported."""
        return country.upper() in self.APPLE_DOMAINS

    def build_search_url(self, query: str, country: str, **kwargs) -> str:
        """Build Apple Store search URL."""
        country = country.upper()
        if not self.is_supported_country(country):
            country = 'US'

        domain = self.APPLE_DOMAINS[country]

        # Apple doesn't have a traditional search, so we'll try to match products
        # For iPhone searches, go directly to iPhone page
        if 'iphone' in query.lower():
            if '16 pro' in query.lower():
                return f"https://{domain}/iphone-16-pro/"
            elif '16' in query.lower():
                return f"https://{domain}/iphone-16/"
            elif '15 pro' in query.lower():
                return f"https://{domain}/iphone-15-pro/"
            elif '15' in query.lower():
                return f"https://{domain}/iphone-15/"
            else:
                return f"https://{domain}/iphone/"
        elif 'ipad' in query.lower():
            return f"https://{domain}/ipad/"
        elif 'macbook' in query.lower() or 'mac' in query.lower():
            return f"https://{domain}/mac/"
        elif 'watch' in query.lower():
            return f"https://{domain}/watch/"
        else:
            # Fallback to main store
            return f"https://{domain}/store"

    async def search(self, query: str, country: str, **kwargs) -> List[ProductResult]:
        """Search Apple Store for products."""
        await self._rate_limit_delay()

        # Only search for Apple products
        if not self._is_apple_product(query):
            return []

        search_url = self.build_search_url(query, country, **kwargs)
        logger.info(f"Apple Store: Searching {search_url}")

        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_apple_page(html, country, query)
                else:
                    logger.warning(f"Apple Store: HTTP {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Apple Store search error: {e}")
            return []

    def _is_apple_product(self, query: str) -> bool:
        """Check if query is for an Apple product."""
        apple_keywords = ['iphone', 'ipad', 'macbook', 'imac', 'mac mini', 'mac pro',
                         'apple watch', 'airpods', 'apple tv', 'homepod']
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in apple_keywords)

    def _parse_apple_page(self, html: str, country: str, query: str) -> List[ProductResult]:
        """Parse Apple Store product page."""
        soup = BeautifulSoup(html, 'lxml')
        results = []

        # Try to find product information
        # Apple uses various selectors for different product pages
        product_selectors = [
            '.rf-hcard-content',
            '.as-producttile',
            '.rf-ccard-content-info'
        ]

        products = []
        for selector in product_selectors:
            products = soup.select(selector)
            if products:
                break

        if not products:
            # Try to parse single product page
            return self._parse_single_product(soup, country, query)

        logger.info(f"Apple Store: Found {len(products)} product containers")

        for product in products[:10]:  # Limit results
            try:
                result = self._parse_product(product, country)
                if result and self._matches_query(result.product_name, query):
                    results.append(result)
            except Exception as e:
                logger.debug(f"Apple Store: Error parsing product: {e}")
                continue

        logger.info(f"Apple Store: Parsed {len(results)} valid results")
        return results

    def _parse_single_product(self, soup: BeautifulSoup, country: str, query: str) -> List[ProductResult]:
        """Parse single Apple product page."""
        try:
            # Extract title
            title_selectors = [
                'h1.rf-hcard-content-title',
                '.pd-title',
                'h1'
            ]

            title = None
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break

            if not title:
                return []

            # Extract price
            price_selectors = [
                '.rf-hcard-content-price',
                '.current_price .sr-only',
                '.price-current'
            ]

            price = None
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'[\d,]+', price_text)
                    if price_match:
                        price = price_match.group().replace(',', '')
                        break

            if not price:
                return []

            currency = self.CURRENCY_MAP.get(country.upper(), 'USD')
            current_url = soup.find('link', {'rel': 'canonical'})
            product_url = current_url.get('href') if current_url else f"https://apple.com"

            return [ProductResult(
                link=product_url,
                price=price,
                currency=currency,
                product_name=title,
                availability="Available",
                seller="Apple",
                source=self.name,
                scraped_at=datetime.now().isoformat()
            )]

        except Exception as e:
            logger.debug(f"Apple Store: Error parsing single product: {e}")
            return []

    def _parse_product(self, product_elem, country: str) -> Optional[ProductResult]:
        """Parse individual Apple product."""
        # Placeholder for product parsing
        return None

    def _matches_query(self, product_name: str, query: str) -> bool:
        """Check if product matches the search query."""
        query_words = query.lower().split()
        product_words = product_name.lower().split()

        # Check if at least 50% of query words are in product name
        matches = sum(1 for word in query_words if any(word in pword for pword in product_words))
        return matches >= len(query_words) * 0.5

    def get_priority(self, country: str) -> int:
        """Apple Store gets highest priority for Apple products."""
        if country.upper() in self.APPLE_DOMAINS:
            return 0  # Highest priority for Apple products
        return 999