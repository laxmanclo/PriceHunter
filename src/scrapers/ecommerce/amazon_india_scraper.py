#!/usr/bin/env python3
"""
Amazon India scraper optimized for Indian market.
Specialized version with India-specific features and better parsing.
"""

import asyncio
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import quote_plus

from loguru import logger

from ...core.base_scraper import BaseScraper, ProductResult, ScraperType


class AmazonIndiaScraper(BaseScraper):
    """Specialized Amazon scraper for Indian market."""

    def __init__(self):
        super().__init__(
            name="Amazon India",
            scraper_type=ScraperType.ECOMMERCE,
            base_url="https://www.amazon.in",
            supported_countries=['IN'],
            rate_limit=1.5
        )

    def is_supported_country(self, country: str) -> bool:
        """Check if country is supported."""
        return country.upper() == 'IN'

    def build_search_url(self, query: str, country: str, **kwargs) -> str:
        """Build Amazon India search URL."""
        encoded_query = quote_plus(query)
        return f"https://www.amazon.in/s?k={encoded_query}&ref=sr_pg_1&sort=relevanceblender"

    async def search(self, query: str, country: str, **kwargs) -> List[ProductResult]:
        """Search for products on Amazon India."""
        if not self.is_supported_country(country):
            logger.warning(f"Amazon India: Country {country} not supported")
            return []

        search_url = self.build_search_url(query, country)
        logger.info(f"Amazon India: Searching {search_url}")

        try:
            # Use Indian user agent and headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-IN,en;q=0.9,hi;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }

            response = await self.session.get(search_url, headers=headers, timeout=30)
            
            if response.status == 200:
                html_content = await response.text()
                return await self._parse_search_results(html_content, query)
            elif response.status == 503:
                logger.warning("Amazon India: Service unavailable (503)")
                return []
            else:
                logger.warning(f"Amazon India: HTTP {response.status}")
                return []

        except Exception as e:
            logger.error(f"Amazon India: Search failed: {e}")
            return []

    async def _parse_search_results(self, html: str, query: str) -> List[ProductResult]:
        """Parse Amazon India search results."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        # Amazon India product containers
        product_selectors = [
            '[data-component-type="s-search-result"]',
            '[data-asin]:not([data-asin=""])',
            '.s-result-item[data-asin]',
            '.s-widget-container[data-asin]',
        ]

        products = []
        for selector in product_selectors:
            found_products = soup.select(selector)
            if found_products:
                products = found_products
                logger.info(f"Amazon India: Using selector {selector}")
                break

        logger.info(f"Amazon India: Found {len(products)} product containers")

        for product in products[:20]:  # Limit to first 20 results
            try:
                result = self._parse_product(product)
                if result:
                    results.append(result)
            except Exception as e:
                logger.debug(f"Amazon India: Error parsing product: {e}")
                continue

        logger.info(f"Amazon India: Parsed {len(results)} valid results")
        return results

    def _parse_product(self, product_elem) -> Optional[ProductResult]:
        """Parse individual product from Amazon India search results."""
        try:
            # Extract ASIN
            asin = product_elem.get('data-asin')
            if not asin:
                return None

            # Extract product title with India-specific selectors
            title_selectors = [
                'h2 a span[aria-label]',
                'h2 a span:not([class])',
                'h2 .a-link-normal span',
                '[data-cy="title-recipe-title"] span',
                'h2 span',
                '.a-size-medium.a-color-base',
                '.a-size-base-plus',
            ]

            title = self._extract_text_with_fallback(product_elem, title_selectors)
            if not title:
                return None

            # Extract price with INR-specific parsing
            price_selectors = [
                '.a-price .a-offscreen',
                '.a-price-whole',
                '.a-price-range .a-price .a-offscreen',
                '.a-price[data-a-color="price"] .a-offscreen',
                '.a-price.a-text-price .a-offscreen',
                '.sx-price .a-offscreen',
            ]

            price_text = self._extract_text_with_fallback(product_elem, price_selectors)
            if not price_text:
                return None

            # Clean and validate price
            price = self._clean_price(price_text)
            if not price:
                return None

            # Extract product URL
            url = self._extract_product_url(product_elem)
            if not url:
                return None

            # Extract additional details
            rating = self._extract_rating(product_elem)
            reviews_count = self._extract_reviews_count(product_elem)
            availability = self._extract_availability(product_elem)
            image_url = self._extract_image_url(product_elem)

            return ProductResult(
                link=url,
                price=price,
                currency="INR",
                product_name=title,
                availability=availability or "Unknown",
                rating=rating,
                reviews_count=reviews_count,
                seller="Amazon India",
                image_url=image_url,
                source=self.name,
                scraped_at=datetime.now().isoformat()
            )

        except Exception as e:
            logger.debug(f"Amazon India: Error parsing product: {e}")
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

    def _clean_price(self, price_text: str) -> Optional[str]:
        """Clean and extract numeric price from INR text."""
        if not price_text:
            return None
        
        # Remove ₹ symbol and other non-numeric characters
        price_clean = re.sub(r'[^\d,.]', '', price_text)
        
        # Handle Indian number format (1,23,456.00)
        if ',' in price_clean and '.' in price_clean:
            # Format like 1,23,456.00
            price_clean = price_clean.replace(',', '')
        elif ',' in price_clean:
            # Could be thousands separator or decimal (rare in India)
            parts = price_clean.split(',')
            if len(parts[-1]) <= 2:
                # Likely decimal separator (uncommon)
                price_clean = price_clean.replace(',', '.')
            else:
                # Thousands separator
                price_clean = price_clean.replace(',', '')
        
        try:
            float(price_clean)
            return price_clean
        except ValueError:
            return None

    def _extract_product_url(self, element) -> Optional[str]:
        """Extract product URL."""
        try:
            link_elem = element.select_one('h2 a, .a-link-normal')
            if link_elem:
                href = link_elem.get('href', '')
                if href.startswith('/'):
                    return f"https://www.amazon.in{href}"
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
                '.a-star-mini .a-icon-alt',
                '.a-icon-star-small .a-icon-alt',
            ]
            
            for selector in rating_selectors:
                rating_elem = element.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get('aria-label', '') or rating_elem.get_text(strip=True)
                    match = re.search(r'(\d+\.?\d*)', rating_text)
                    if match:
                        rating = float(match.group(1))
                        if 0 <= rating <= 5:
                            return rating
        except Exception:
            pass
        return None

    def _extract_reviews_count(self, element) -> Optional[int]:
        """Extract number of reviews."""
        try:
            reviews_selectors = [
                '.a-size-base',
                '[aria-label*="reviews"]',
                '.a-link-normal .a-size-base',
                '.a-size-small .a-link-normal',
            ]
            
            for selector in reviews_selectors:
                reviews_elem = element.select_one(selector)
                if reviews_elem:
                    reviews_text = reviews_elem.get_text(strip=True)
                    # Look for patterns like "1,234" or "(1,234)"
                    match = re.search(r'[\(]?([0-9,]+)[\)]?', reviews_text)
                    if match:
                        count_str = match.group(1).replace(',', '')
                        try:
                            count = int(count_str)
                            if count > 0:  # Sanity check
                                return count
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
                '[data-cy="delivery-recipe"]',
                '.a-color-state',
            ]
            
            for selector in availability_selectors:
                avail_elem = element.select_one(selector)
                if avail_elem:
                    text = avail_elem.get_text(strip=True).lower()
                    if any(word in text for word in ['stock', 'available', 'delivery', 'ships', 'get it']):
                        return "In Stock"
                    elif any(word in text for word in ['out', 'unavailable', 'sold', 'temporarily']):
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
                'img[src]',
                '.a-dynamic-image',
            ]
            
            for selector in img_selectors:
                img_elem = element.select_one(selector)
                if img_elem:
                    img_url = img_elem.get('data-src') or img_elem.get('src')
                    if img_url and ('amazon' in img_url or img_url.startswith('http')):
                        return img_url
        except Exception:
            pass
        return None
