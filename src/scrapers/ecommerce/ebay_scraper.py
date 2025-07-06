"""
eBay scraper for price comparison.
Supports multiple eBay domains worldwide.
"""

import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
from datetime import datetime
from bs4 import BeautifulSoup
from loguru import logger

from ...core.base_scraper import BaseScraper, ProductResult, ScraperType


class EbayScraper(BaseScraper):
    """eBay scraper supporting multiple regions."""

    EBAY_DOMAINS = {
        'US': 'ebay.com',
        'CA': 'ebay.ca',
        'UK': 'ebay.co.uk',
        'DE': 'ebay.de',
        'FR': 'ebay.fr',
        'IT': 'ebay.it',
        'ES': 'ebay.es',
        'AU': 'ebay.com.au',
        'IN': 'ebay.in',
        'SG': 'ebay.com.sg',
        'MY': 'ebay.com.my',
        'PH': 'ebay.ph'
    }

    CURRENCY_MAP = {
        'US': 'USD', 'CA': 'CAD', 'UK': 'GBP', 'DE': 'EUR', 'FR': 'EUR',
        'IT': 'EUR', 'ES': 'EUR', 'AU': 'AUD', 'IN': 'INR', 'SG': 'SGD',
        'MY': 'MYR', 'PH': 'PHP'
    }

    def __init__(self):
        """Initialize eBay scraper."""
        super().__init__(
            name="eBay",
            scraper_type=ScraperType.ECOMMERCE,
            base_url="https://ebay.com",
            supported_countries=list(self.EBAY_DOMAINS.keys()),
            rate_limit=2.0,
            timeout=25
        )

    def is_supported_country(self, country: str) -> bool:
        """Check if country is supported."""
        return country.upper() in self.EBAY_DOMAINS

    def build_search_url(self, query: str, country: str, **kwargs) -> str:
        """Build eBay search URL."""
        country = country.upper()
        if not self.is_supported_country(country):
            country = 'US'

        domain = self.EBAY_DOMAINS[country]
        encoded_query = quote_plus(query)

        # eBay search with Buy It Now filter for better price comparison
        url = f"https://{domain}/sch/i.html"
        params = {
            '_nkw': query,
            '_sacat': '0',
            'LH_BIN': '1',  # Buy It Now only
            '_sop': '15',   # Sort by price + shipping
            'rt': 'nc'
        }

        param_string = '&'.join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        return f"{url}?{param_string}"

    async def search(self, query: str, country: str, **kwargs) -> List[ProductResult]:
        """Search eBay for products."""
        await self._rate_limit_delay()

        search_url = self.build_search_url(query, country, **kwargs)
        logger.info(f"eBay: Searching {search_url}")

        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_search_results(html, country)
                else:
                    logger.warning(f"eBay: HTTP {response.status}")
                    return []

        except Exception as e:
            logger.error(f"eBay search error: {e}")
            return []

    def _parse_search_results(self, html: str, country: str) -> List[ProductResult]:
        """Parse eBay search results."""
        soup = BeautifulSoup(html, 'lxml')
        results = []

        # eBay product containers
        products = soup.select('.s-item')
        logger.info(f"eBay: Found {len(products)} product containers")

        for product in products[:15]:  # Limit results
            try:
                result = self._parse_product(product, country)
                if result:
                    results.append(result)
            except Exception as e:
                logger.debug(f"eBay: Error parsing product: {e}")
                continue

        logger.info(f"eBay: Parsed {len(results)} valid results")
        return results

    def _parse_product(self, product_elem, country: str) -> Optional[ProductResult]:
        """Parse individual eBay product."""
        try:
            # Extract title
            title_elem = product_elem.select_one('.s-item__title')
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)

            # Skip ads and non-products
            if 'shop on ebay' in title.lower() or not title:
                return None

            # Extract price
            price_elem = product_elem.select_one('.s-item__price .notranslate')
            if not price_elem:
                return None
            price_text = price_elem.get_text(strip=True)
            price = re.sub(r'[^\d.,]', '', price_text)

            if not price:
                return None

            # Extract URL
            link_elem = product_elem.select_one('.s-item__link')
            if not link_elem:
                return None
            product_url = link_elem.get('href')

            # Extract image
            image_url = None
            img_elem = product_elem.select_one('.s-item__image img')
            if img_elem:
                image_url = img_elem.get('src')

            # Extract shipping info
            shipping_cost = None
            shipping_elem = product_elem.select_one('.s-item__shipping')
            if shipping_elem:
                shipping_text = shipping_elem.get_text(strip=True)
                if 'free' in shipping_text.lower():
                    shipping_cost = "0"
                else:
                    shipping_match = re.search(r'[\d.,]+', shipping_text)
                    if shipping_match:
                        shipping_cost = shipping_match.group()

            # Extract seller info
            seller = "eBay Seller"
            seller_elem = product_elem.select_one('.s-item__seller-info-text')
            if seller_elem:
                seller = seller_elem.get_text(strip=True)

            currency = self.CURRENCY_MAP.get(country.upper(), 'USD')

            return ProductResult(
                link=product_url,
                price=price,
                currency=currency,
                product_name=title,
                availability="Available",
                seller=seller,
                shipping_cost=shipping_cost,
                image_url=image_url,
                source=self.name,
                scraped_at=datetime.now().isoformat()
            )

        except Exception as e:
            logger.debug(f"eBay: Error parsing product: {e}")
            return None