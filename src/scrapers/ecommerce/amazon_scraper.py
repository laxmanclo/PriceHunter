"""
Amazon scraper for price comparison.
Supports multiple Amazon domains worldwide with intelligent product parsing.
"""

import re
import json
import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin
from datetime import datetime
from bs4 import BeautifulSoup
from loguru import logger

from ...core.base_scraper import BaseScraper, ProductResult, ScraperType


class AmazonScraper(BaseScraper):
    """Amazon scraper supporting multiple regions."""

    # Amazon domains by country
    AMAZON_DOMAINS = {
        'US': 'amazon.com',
        'CA': 'amazon.ca',
        'UK': 'amazon.co.uk',
        'DE': 'amazon.de',
        'FR': 'amazon.fr',
        'IT': 'amazon.it',
        'ES': 'amazon.es',
        'JP': 'amazon.co.jp',
        'IN': 'amazon.in',
        'AU': 'amazon.com.au',
        'BR': 'amazon.com.br',
        'MX': 'amazon.com.mx',
        'NL': 'amazon.nl',
        'SE': 'amazon.se',
        'PL': 'amazon.pl',
        'TR': 'amazon.com.tr',
        'AE': 'amazon.ae',
        'SA': 'amazon.sa',
        'SG': 'amazon.sg'
    }

    # Currency mapping
    CURRENCY_MAP = {
        'US': 'USD', 'CA': 'CAD', 'UK': 'GBP', 'DE': 'EUR', 'FR': 'EUR',
        'IT': 'EUR', 'ES': 'EUR', 'JP': 'JPY', 'IN': 'INR', 'AU': 'AUD',
        'BR': 'BRL', 'MX': 'MXN', 'NL': 'EUR', 'SE': 'SEK', 'PL': 'PLN',
        'TR': 'TRY', 'AE': 'AED', 'SA': 'SAR', 'SG': 'SGD'
    }

    def __init__(self):
        """Initialize Amazon scraper."""
        super().__init__(
            name="Amazon",
            scraper_type=ScraperType.ECOMMERCE,
            base_url="https://amazon.com",
            supported_countries=list(self.AMAZON_DOMAINS.keys()),
            rate_limit=1.5,
            timeout=30
        )

    def is_supported_country(self, country: str) -> bool:
        """Check if country is supported."""
        return country.upper() in self.AMAZON_DOMAINS

    def build_search_url(self, query: str, country: str, **kwargs) -> str:
        """Build Amazon search URL for the given country."""
        country = country.upper()
        if not self.is_supported_country(country):
            country = 'US'  # Fallback to US

        domain = self.AMAZON_DOMAINS[country]
        encoded_query = quote_plus(query)

        # Build search URL with parameters for better results
        url = f"https://{domain}/s"
        params = {
            'k': query,
            'ref': 'sr_pg_1',
            'sort': 'relevanceblender'  # Sort by relevance
        }

        # Add category filter if specified
        if 'category' in kwargs:
            params['i'] = kwargs['category']

        # Build final URL
        param_string = '&'.join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        return f"{url}?{param_string}"

    async def search(self, query: str, country: str, **kwargs) -> List[ProductResult]:
        """Search Amazon for products."""
        await self._rate_limit_delay()

        search_url = self.build_search_url(query, country, **kwargs)
        logger.info(f"Amazon: Searching {search_url}")

        try:
            # Use rotating headers for better success rate
            headers = self._get_amazon_headers()

            async with self.session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_search_results(html, country, query)
                elif response.status == 503:
                    logger.warning("Amazon: Service unavailable (503)")
                    return []
                else:
                    logger.warning(f"Amazon: HTTP {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Amazon search error: {e}")
            return []

    def _get_amazon_headers(self) -> Dict[str, str]:
        """Get Amazon-specific headers."""
        headers = self._get_headers()
        headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        })
        return headers

    def _parse_search_results(self, html: str, country: str, query: str) -> List[ProductResult]:
        """Parse Amazon search results."""
        soup = BeautifulSoup(html, 'lxml')
        results = []

        # Multiple selectors for different Amazon layouts
        product_selectors = [
            '[data-component-type="s-search-result"]',
            '.s-result-item[data-asin]',
            '.sg-col-inner .s-widget-container'
        ]

        products = []
        for selector in product_selectors:
            products = soup.select(selector)
            if products:
                break

        logger.info(f"Amazon: Found {len(products)} product containers")

        for product in products[:20]:  # Limit to first 20 results
            try:
                result = self._parse_product(product, country)
                if result:
                    results.append(result)
            except Exception as e:
                logger.debug(f"Amazon: Error parsing product: {e}")
                continue

        logger.info(f"Amazon: Parsed {len(results)} valid results")
        return results

    def _parse_product(self, product_elem, country: str) -> Optional[ProductResult]:
        """Parse individual product from Amazon search results with advanced fallback strategies."""
        try:
            # Extract ASIN with multiple strategies
            asin = (product_elem.get('data-asin') or
                   product_elem.get('data-uuid') or
                   self._extract_asin_from_url(product_elem))

            if not asin:
                logger.debug("Amazon: No ASIN found, skipping product")
                return None

            # Extract product title with comprehensive selectors
            title_selectors = [
                # Modern Amazon layouts
                'h2 a span[aria-label]',
                'h2 a span:not([class])',
                'h2 .a-link-normal span',
                '[data-cy="title-recipe-title"] span',

                # Legacy selectors
                'h2 a span',
                '.s-size-mini .s-link-style a',
                'h2 .a-link-normal',
                '.s-title-instructions-style h2 a span',

                # Fallback selectors
                '.s-title .a-link-normal',
                '.a-size-base-plus',
                '.a-size-medium',
                'h2 span'
            ]

            title = self._extract_text_with_fallback(product_elem, title_selectors)
            if not title:
                logger.debug("Amazon: No title found, skipping product")
                return None

            # Extract price with sophisticated parsing
            price_selectors = [
                # Primary price selectors
                '.a-price .a-offscreen',
                '.a-price-whole',
                '.a-price-range .a-price .a-offscreen',

                # Alternative price formats
                '.a-price-symbol + .a-price-whole',
                '.a-price .a-price-whole',
                '.a-price-fraction',

                # Deal prices
                '.a-price.a-text-price .a-offscreen',
                '.a-price[data-a-color="price"] .a-offscreen',

                # Fallback price selectors
                '[data-a-color="price"]',
                '.a-color-price',
                '.sx-price .a-offscreen'
            ]

            price_text = self._extract_text_with_fallback(product_elem, price_selectors)

            if not price_text:
                logger.debug("Amazon: No price found, skipping product")
                return None

            # Clean and validate price
            price = self._clean_price(price_text)
            if not price:
                logger.debug(f"Amazon: Invalid price format: {price_text}")
                return None

            # Extract product URL
            url = self._extract_product_url(product_elem, country)
            if not url:
                logger.debug("Amazon: No URL found, skipping product")
                return None

            # Extract additional details
            rating = self._extract_rating(product_elem)
            reviews_count = self._extract_reviews_count(product_elem)
            availability = self._extract_availability(product_elem)
            image_url = self._extract_image_url(product_elem)

            # Get currency for country
            currency = self.CURRENCY_MAP.get(country.upper(), 'USD')

            return ProductResult(
                link=url,
                price=price,
                currency=currency,
                product_name=title,
                availability=availability or "Unknown",
                rating=rating,
                reviews_count=reviews_count,
                seller="Amazon",
                image_url=image_url,
                source=self.name,
                scraped_at=datetime.now().isoformat()
            )

        except Exception as e:
            logger.debug(f"Amazon: Error parsing product: {e}")
            return None

    def _extract_text_with_fallback(self, element, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple selector fallbacks."""
        for selector in selectors:
            try:
                elem = element.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 0:
                        return text
            except Exception:
                continue
        return None

    def _extract_asin_from_url(self, element) -> Optional[str]:
        """Extract ASIN from product URL."""
        try:
            link_elem = element.select_one('h2 a, .a-link-normal')
            if link_elem:
                href = link_elem.get('href', '')
                # Extract ASIN from URL pattern /dp/ASIN/ or /gp/product/ASIN/
                import re
                match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', href)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def _clean_price(self, price_text: str) -> Optional[str]:
        """Clean and extract numeric price from text."""
        if not price_text:
            return None

        import re
        # Remove currency symbols and extract numbers
        price_clean = re.sub(r'[^\d.,]', '', price_text)

        # Handle different decimal separators
        if ',' in price_clean and '.' in price_clean:
            # Format like 1,234.56
            price_clean = price_clean.replace(',', '')
        elif ',' in price_clean:
            # Could be European format 1234,56 or thousands separator 1,234
            if price_clean.count(',') == 1 and len(price_clean.split(',')[1]) <= 2:
                # Likely decimal separator
                price_clean = price_clean.replace(',', '.')
            else:
                # Likely thousands separator
                price_clean = price_clean.replace(',', '')

        try:
            float(price_clean)
            return price_clean
        except ValueError:
            return None

    def _extract_product_url(self, element, country: str) -> Optional[str]:
        """Extract product URL."""
        try:
            link_elem = element.select_one('h2 a, .a-link-normal')
            if link_elem:
                href = link_elem.get('href', '')
                if href.startswith('/'):
                    domain = self.AMAZON_DOMAINS.get(country.upper(), 'amazon.com')
                    return f"https://{domain}{href}"
                elif href.startswith('http'):
                    return href
        except Exception:
            pass
        return None

    def _extract_rating(self, element) -> Optional[float]:
        """Extract product rating."""
        try:
            rating_selectors = [
                '.a-icon-alt',
                '[aria-label*="stars"]',
                '.a-star-mini .a-icon-alt'
            ]

            for selector in rating_selectors:
                rating_elem = element.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get('aria-label', '') or rating_elem.get_text(strip=True)
                    import re
                    match = re.search(r'(\d+\.?\d*)', rating_text)
                    if match:
                        return float(match.group(1))
        except Exception:
            pass
        return None

    def _extract_reviews_count(self, element) -> Optional[int]:
        """Extract number of reviews."""
        try:
            reviews_selectors = [
                '.a-size-base',
                '[aria-label*="reviews"]',
                '.a-link-normal .a-size-base'
            ]

            for selector in reviews_selectors:
                reviews_elem = element.select_one(selector)
                if reviews_elem:
                    reviews_text = reviews_elem.get_text(strip=True)
                    import re
                    # Look for patterns like "1,234" or "(1,234)"
                    match = re.search(r'[\(]?([0-9,]+)[\)]?', reviews_text)
                    if match:
                        count_str = match.group(1).replace(',', '')
                        try:
                            return int(count_str)
                        except ValueError:
                            continue
        except Exception:
            pass
        return None

    def _extract_availability(self, element) -> Optional[str]:
        """Extract availability status."""
        try:
            availability_selectors = [
                '.a-size-base.a-color-price',
                '.a-size-base.a-color-secondary',
                '[data-cy="delivery-recipe"]'
            ]

            for selector in availability_selectors:
                avail_elem = element.select_one(selector)
                if avail_elem:
                    text = avail_elem.get_text(strip=True).lower()
                    if any(word in text for word in ['stock', 'available', 'delivery', 'ships']):
                        return "In Stock"
                    elif any(word in text for word in ['out', 'unavailable', 'sold']):
                        return "Out of Stock"
        except Exception:
            pass
        return "Unknown"

    def _extract_image_url(self, element) -> Optional[str]:
        """Extract product image URL."""
        try:
            img_selectors = [
                '.s-image',
                'img[data-src]',
                'img[src]'
            ]

            for selector in img_selectors:
                img_elem = element.select_one(selector)
                if img_elem:
                    img_url = img_elem.get('data-src') or img_elem.get('src')
                    if img_url and img_url.startswith('http'):
                        return img_url
        except Exception:
            pass
        return None

    def get_priority(self, country: str) -> int:
        """Amazon gets high priority for most countries."""
        if country.upper() in self.AMAZON_DOMAINS:
            return 1  # Highest priority
        return 999