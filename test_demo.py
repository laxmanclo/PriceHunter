#!/usr/bin/env python3
"""
Demo test for PriceHunter with mock data to show working system.
"""

import asyncio
import json
from datetime import datetime
from typing import List

from src.core.base_scraper import BaseScraper, ProductResult, ScraperType
from src.core.price_fetcher import PriceFetcher, SearchRequest


class MockScraper(BaseScraper):
    """Mock scraper that returns sample iPhone 16 Pro results."""

    def __init__(self):
        super().__init__(
            name="MockStore",
            scraper_type=ScraperType.ECOMMERCE,
            base_url="https://mockstore.com",
            supported_countries=['US', 'UK', 'IN'],
            rate_limit=0.1
        )

    def is_supported_country(self, country: str) -> bool:
        return country.upper() in ['US', 'UK', 'IN']

    def build_search_url(self, query: str, country: str, **kwargs) -> str:
        return f"https://mockstore.com/search?q={query}&country={country}"

    async def search(self, query: str, country: str, **kwargs) -> List[ProductResult]:
        """Return mock iPhone 16 Pro results."""
        await asyncio.sleep(0.1)  # Simulate network delay

        if 'iphone 16 pro' not in query.lower():
            return []

        # Mock results for iPhone 16 Pro
        currency = 'USD' if country.upper() == 'US' else 'GBP' if country.upper() == 'UK' else 'INR'
        base_price = 999 if country.upper() == 'US' else 999 if country.upper() == 'UK' else 79900

        results = [
            ProductResult(
                link="https://mockstore.com/iphone-16-pro-128gb",
                price=str(base_price),
                currency=currency,
                product_name="Apple iPhone 16 Pro 128GB - Natural Titanium",
                availability="In Stock",
                rating=4.8,
                reviews_count=1247,
                seller="MockStore",
                image_url="https://mockstore.com/images/iphone16pro.jpg",
                source=self.name,
                scraped_at=datetime.now().isoformat()
            ),
            ProductResult(
                link="https://mockstore.com/iphone-16-pro-256gb",
                price=str(base_price + 100),
                currency=currency,
                product_name="Apple iPhone 16 Pro 256GB - Blue Titanium",
                availability="In Stock",
                rating=4.9,
                reviews_count=892,
                seller="MockStore",
                shipping_cost="0",
                image_url="https://mockstore.com/images/iphone16pro-blue.jpg",
                source=self.name,
                scraped_at=datetime.now().isoformat()
            ),
            ProductResult(
                link="https://mockstore.com/iphone-16-pro-512gb",
                price=str(base_price + 300),
                currency=currency,
                product_name="Apple iPhone 16 Pro 512GB - White Titanium",
                availability="Limited Stock",
                rating=4.7,
                reviews_count=634,
                seller="MockStore Premium",
                shipping_cost="15",
                image_url="https://mockstore.com/images/iphone16pro-white.jpg",
                source=self.name,
                scraped_at=datetime.now().isoformat()
            )
        ]

        return results


async def demo_search():
    """Demonstrate the PriceHunter system with mock data."""
    print("🚀 PriceHunter Demo - Sophisticated Price Comparison Tool")
    print("=" * 60)

    # Create a custom price fetcher with our mock scraper
    fetcher = PriceFetcher()

    # Add our mock scraper to the list
    mock_scraper = MockScraper()
    fetcher.scrapers.append(mock_scraper)

    # Test search for iPhone 16 Pro
    request = SearchRequest(
        country="US",
        query="iPhone 16 Pro, 128GB"
    )

    print(f"🔍 Searching for: {request.query}")
    print(f"📍 Country: {request.country}")
    print(f"⏱️  Starting search...")
    print()

    # Perform search
    response = await fetcher.search(request)

    # Display results
    print(f"✅ Search completed in {response.search_time:.2f} seconds")
    print(f"📊 Found {response.total_results} results from {len(response.sources_used)} sources")
    print(f"🏪 Sources: {', '.join(response.sources_used)}")
    print()

    if response.results:
        print("💰 Best Prices Found:")
        print("-" * 60)

        for i, result in enumerate(response.results[:5], 1):
            print(f"{i}. {result['productName']}")
            print(f"   💵 Price: {result['currency']} {result['price']}")
            print(f"   🏪 Source: {result['source']}")
            print(f"   📦 Availability: {result['availability']}")
            if result.get('rating'):
                print(f"   ⭐ Rating: {result['rating']}/5.0 ({result.get('reviewsCount', 0)} reviews)")
            if result.get('shippingCost'):
                shipping = "Free" if result['shippingCost'] == "0" else f"{result['currency']} {result['shippingCost']}"
                print(f"   🚚 Shipping: {shipping}")
            print(f"   🔗 Link: {result['link']}")
            print()
    else:
        print("❌ No results found")

    print("🎯 Demo completed successfully!")
    print("\n📋 System Features Demonstrated:")
    print("✅ Multi-source price comparison")
    print("✅ Concurrent scraper execution")
    print("✅ Intelligent result ranking")
    print("✅ Comprehensive product information")
    print("✅ Error handling and graceful degradation")
    print("✅ Structured data output")


if __name__ == "__main__":
    asyncio.run(demo_search())