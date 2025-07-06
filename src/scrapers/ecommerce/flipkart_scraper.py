#!/usr/bin/env python3
"""
Flipkart scraper for Indian e-commerce market.
Flipkart is India's largest e-commerce platform with comprehensive product coverage.
"""

import asyncio
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import quote_plus

from loguru import logger

from ...core.base_scraper import BaseScraper, ProductResult, ScraperType


class FlipkartScraper(BaseScraper):
    """Scraper for Flipkart - India's leading e-commerce platform."""

    def __init__(self):
        super().__init__(
            name="Flipkart",
            scraper_type=ScraperType.ECOMMERCE,
            base_url="https://www.flipkart.com",
            supported_countries=['IN'],
            rate_limit=2.0  # Flipkart is more lenient
        )

    def is_supported_country(self, country: str) -> bool:
        """Check if country is supported."""
        return country.upper() == 'IN'

    def build_search_url(self, query: str, country: str, **kwargs) -> str:
        """Build Flipkart search URL."""
        encoded_query = quote_plus(query)
        return f"https://www.flipkart.com/search?q={encoded_query}&sort=relevance"

    async def search(self, query: str, country: str, **kwargs) -> List[ProductResult]:
        """Search for products on Flipkart."""
        if not self.is_supported_country(country):
            logger.warning(f"Flipkart: Country {country} not supported")
            return []

        search_url = self.build_search_url(query, country)
        logger.info(f"Flipkart: Searching {search_url}")

        try:
            # Use mobile user agent for better success rate
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = await self.session.get(search_url, headers=headers, timeout=30)
            
            if response.status == 200:
                html_content = await response.text()
                return await self._parse_search_results(html_content, query)
            else:
                logger.warning(f"Flipkart: HTTP {response.status}")
                return []

        except Exception as e:
            logger.error(f"Flipkart: Search failed: {e}")
            return []

    async def _parse_search_results(self, html: str, query: str) -> List[ProductResult]:
        """Parse Flipkart search results."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        # Flipkart product containers
        product_selectors = [
            '[data-id]',  # Main product containers
            '._1AtVbE',    # Product cards
            '._13oc-S',    # Alternative layout
            '._2kHMtA',    # Grid layout
        ]

        products = []
        for selector in product_selectors:
            found_products = soup.select(selector)
            if found_products:
                products = found_products
                break

        logger.info(f"Flipkart: Found {len(products)} product containers")

        for product in products[:25]:  # Limit to first 25 results
            try:
                result = self._parse_product(product)
                if result:
                    results.append(result)
            except Exception as e:
                logger.debug(f"Flipkart: Error parsing product: {e}")
                continue

        logger.info(f"Flipkart: Parsed {len(results)} valid results")
        return results

    def _parse_product(self, product_elem) -> Optional[ProductResult]:
        """Parse individual product from Flipkart search results."""
        try:
            # Extract product title
            title_selectors = [
                '._4rR01T',      # Main title class
                '.s1Q9rs',       # Alternative title
                '._2WkVRV',      # Product name
                '.IRpwTa',       # Title link
                'a[title]',      # Fallback with title attribute
            ]

            title = self._extract_text_with_fallback(product_elem, title_selectors)
            if not title:
                # Try title attribute from links
                link_elem = product_elem.select_one('a')
                if link_elem:
                    title = link_elem.get('title', '').strip()
                
            if not title:
                return None

            # Extract price
            price_selectors = [
                '._30jeq3._1_WHN1',  # Current price
                '._30jeq3',          # Price container
                '._1_WHN1',          # Price text
                '.Nx9bqj',           # Alternative price
                '._3tbKJL',          # Deal price
            ]

            price_text = self._extract_text_with_fallback(product_elem, price_selectors)
            if not price_text:
                return None

            # Clean price
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
            image_url = self._extract_image_url(product_elem)

            return ProductResult(
                link=url,
                price=price,
                currency="INR",
                product_name=title,
                availability="In Stock",  # Flipkart usually shows available items
                rating=rating,
                reviews_count=reviews_count,
                seller="Flipkart",
                image_url=image_url,
                source=self.name,
                scraped_at=datetime.now().isoformat()
            )

        except Exception as e:
            logger.debug(f"Flipkart: Error parsing product: {e}")
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
        """Clean and extract numeric price from text."""
        if not price_text:
            return None
        
        # Remove ₹ symbol and other non-numeric characters
        price_clean = re.sub(r'[^\d,.]', '', price_text)
        
        # Handle Indian number format (1,23,456)
        if ',' in price_clean:
            price_clean = price_clean.replace(',', '')
        
        try:
            float(price_clean)
            return price_clean
        except ValueError:
            return None

    def _extract_product_url(self, element) -> Optional[str]:
        """Extract product URL."""
        try:
            link_elem = element.select_one('a')
            if link_elem:
                href = link_elem.get('href', '')
                if href.startswith('/'):
                    return f"https://www.flipkart.com{href}"
                elif href.startswith('http'):
                    return href
        except Exception:
            pass
        return None

    def _extract_rating(self, element) -> Optional[float]:
        """Extract product rating."""
        try:
            rating_selectors = [
                '._3LWZlK',  # Rating container
                '._1lRcqv',  # Star rating
                '.hGSR34',   # Rating text
            ]
            
            for selector in rating_selectors:
                rating_elem = element.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    match = re.search(r'(\d+\.?\d*)', rating_text)
                    if match:
                        rating = float(match.group(1))
                        if 0 <= rating <= 5:  # Valid rating range
                            return rating
        except Exception:
            pass
        return None

    def _extract_reviews_count(self, element) -> Optional[int]:
        """Extract number of reviews."""
        try:
            reviews_selectors = [
                '._2_R_DZ',  # Reviews count
                '._38sUEc',  # Alternative reviews
                '.hGSR34',   # Rating and reviews container
            ]
            
            for selector in reviews_selectors:
                reviews_elem = element.select_one(selector)
                if reviews_elem:
                    reviews_text = reviews_elem.get_text(strip=True)
                    # Look for patterns like "1,234 Ratings" or "(1,234)"
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

    def _extract_image_url(self, element) -> Optional[str]:
        """Extract product image URL."""
        try:
            img_selectors = [
                '._396cs4 img',  # Product image
                '._2r_T1I img',  # Alternative image
                'img[src]',      # Fallback
            ]
            
            for selector in img_selectors:
                img_elem = element.select_one(selector)
                if img_elem:
                    img_url = img_elem.get('src') or img_elem.get('data-src')
                    if img_url and ('flipkart' in img_url or img_url.startswith('http')):
                        return img_url
        except Exception:
            pass
        return None
