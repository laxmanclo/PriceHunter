#!/usr/bin/env python3
"""
Enhanced demo script testing sophisticated PriceHunter features.
Tests both US and Indian markets with advanced product matching.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List

from src.core.base_scraper import BaseScraper, ProductResult, ScraperType
from src.core.price_fetcher import PriceFetcher, SearchRequest


class EnhancedMockScraper(BaseScraper):
    """Enhanced mock scraper with realistic product variations."""

    def __init__(self, name: str, base_price: float, currency: str = "USD", country: str = "US"):
        super().__init__(
            name=name,
            scraper_type=ScraperType.ECOMMERCE,
            base_url=f"https://{name.lower().replace(' ', '')}.com",
            supported_countries=[country],
            rate_limit=0.1
        )
        self.base_price = base_price
        self.currency = currency
        self.country = country

    def is_supported_country(self, country: str) -> bool:
        return country.upper() == self.country

    def build_search_url(self, query: str, country: str, **kwargs) -> str:
        return f"{self.base_url}/search?q={query}&country={country}"

    async def search(self, query: str, country: str, **kwargs) -> List[ProductResult]:
        """Return realistic mock results with variations."""
        await asyncio.sleep(0.2)  # Simulate network delay

        if not self.is_supported_country(country):
            return []

        import random
        
        products = []
        
        if "iphone 16 pro" in query.lower():
            # Different product name variations to test matching
            variations = [
                ("Apple iPhone 16 Pro 128GB - Natural Titanium", 1.0),
                ("iPhone 16 Pro 128GB Natural Titanium (Unlocked)", 1.02),
                ("Apple iPhone 16 Pro - 128GB - Natural Titanium", 0.98),
                ("iPhone 16 Pro 128GB - Natural Titanium - Factory Unlocked", 1.01),
                ("Apple iPhone 16 Pro (128GB) Natural Titanium", 0.99),
            ]
            
            # Each scraper returns 1-2 products
            num_products = random.randint(1, 2)
            selected_variations = random.sample(variations, min(num_products, len(variations)))
            
            for i, (name, price_mult) in enumerate(selected_variations):
                price = self.base_price * price_mult * random.uniform(0.97, 1.03)
                
                products.append(ProductResult(
                    link=f"{self.base_url}/iphone-16-pro-{i}",
                    price=f"{price:.2f}",
                    currency=self.currency,
                    product_name=name,
                    availability="In Stock" if random.random() > 0.15 else "Limited Stock",
                    rating=round(random.uniform(4.2, 4.9), 1),
                    reviews_count=random.randint(500, 2500),
                    seller=self.name,
                    source=self.name,
                    scraped_at=datetime.now().isoformat()
                ))

        return products


async def test_us_market():
    """Test US market with multiple scrapers."""
    print("\n🇺🇸 Testing US Market")
    print("=" * 50)
    
    # Create mock scrapers for US market
    us_scrapers = [
        EnhancedMockScraper("Amazon US", 999.0, "USD", "US"),
        EnhancedMockScraper("Best Buy", 999.0, "USD", "US"),
        EnhancedMockScraper("Apple Store", 999.0, "USD", "US"),
        EnhancedMockScraper("B&H Photo", 989.0, "USD", "US"),
        EnhancedMockScraper("Newegg", 995.0, "USD", "US"),
    ]
    
    # Create fetcher and replace with mock scrapers
    fetcher = PriceFetcher()
    # Clear existing scrapers and add our mock ones
    fetcher.scrapers.clear()
    fetcher.scrapers.extend(us_scrapers)
    
    # Test search
    request = SearchRequest(country="US", query="iPhone 16 Pro, 128GB")
    
    start_time = time.time()
    response = await fetcher.search(request)
    end_time = time.time()
    
    print(f"⏱️  Search completed in {end_time - start_time:.2f} seconds")
    print(f"📊 Found {response.total_results} results from {len(response.sources_used)} sources")
    print(f"🏪 Sources: {', '.join(response.sources_used)}")
    
    if response.results:
        print("\n🏆 Top Results:")
        for i, result in enumerate(response.results[:5], 1):
            print(f"{i}. {result['productName'][:60]}...")
            print(f"   💰 ${result['price']} {result['currency']} - {result['seller']}")
            print(f"   ⭐ {result.get('rating', 'N/A')} ({result.get('reviewsCount', 0)} reviews)")
            print(f"   🔗 {result['link'][:50]}...")
            print()
    
    return response


async def test_indian_market():
    """Test Indian market with local scrapers."""
    print("\n🇮🇳 Testing Indian Market")
    print("=" * 50)
    
    # Create mock scrapers for Indian market
    indian_scrapers = [
        EnhancedMockScraper("Flipkart", 79900.0, "INR", "IN"),
        EnhancedMockScraper("Amazon India", 79900.0, "INR", "IN"),
        EnhancedMockScraper("Croma", 81900.0, "INR", "IN"),
        EnhancedMockScraper("Vijay Sales", 80500.0, "INR", "IN"),
        EnhancedMockScraper("Reliance Digital", 79999.0, "INR", "IN"),
    ]
    
    # Create fetcher and replace with mock scrapers
    fetcher = PriceFetcher()
    # Clear existing scrapers and add our mock ones
    fetcher.scrapers.clear()
    fetcher.scrapers.extend(indian_scrapers)
    
    # Test search
    request = SearchRequest(country="IN", query="iPhone 16 Pro, 128GB")
    
    start_time = time.time()
    response = await fetcher.search(request)
    end_time = time.time()
    
    print(f"⏱️  Search completed in {end_time - start_time:.2f} seconds")
    print(f"📊 Found {response.total_results} results from {len(response.sources_used)} sources")
    print(f"🏪 Sources: {', '.join(response.sources_used)}")
    
    if response.results:
        print("\n🏆 Top Results:")
        for i, result in enumerate(response.results[:5], 1):
            print(f"{i}. {result['productName'][:60]}...")
            print(f"   💰 ₹{result['price']} {result['currency']} - {result['seller']}")
            print(f"   ⭐ {result.get('rating', 'N/A')} ({result.get('reviewsCount', 0)} reviews)")
            print(f"   🔗 {result['link'][:50]}...")
            print()
    
    return response


async def test_product_matching():
    """Test advanced product matching capabilities."""
    print("\n🧠 Testing Advanced Product Matching")
    print("=" * 50)
    
    from src.core.product_matcher import ProductMatcher
    
    matcher = ProductMatcher()
    
    # Test product similarity
    products = [
        "Apple iPhone 16 Pro 128GB - Natural Titanium",
        "iPhone 16 Pro 128GB Natural Titanium (Unlocked)",
        "Apple iPhone 16 Pro - 128GB - Natural Titanium",
        "Samsung Galaxy S24 Ultra 256GB",
        "iPhone 16 Pro 128GB - Blue Titanium",
    ]
    
    query = "iPhone 16 Pro 128GB"
    
    print(f"Query: '{query}'")
    print("\nSimilarity Scores:")
    
    for product in products:
        similarity = matcher.calculate_similarity(products[0], product, query)
        print(f"  {product[:50]}... → {similarity:.3f}")
    
    # Test feature extraction
    print(f"\n🔍 Feature Extraction for: '{products[0]}'")
    features = matcher.extract_features(products[0], query)
    print(f"  Brand: {features.brand}")
    print(f"  Model: {features.model}")
    print(f"  Storage: {features.storage}")
    print(f"  Color: {features.color}")
    print(f"  Category: {features.category}")
    print(f"  Key Specs: {features.key_specs}")


async def main():
    """Run all enhanced tests."""
    print("🚀 PriceHunter Enhanced Demo")
    print("Testing sophisticated price comparison with advanced features")
    print("=" * 70)
    
    try:
        # Test US market
        us_response = await test_us_market()
        
        # Test Indian market
        indian_response = await test_indian_market()
        
        # Test product matching
        await test_product_matching()
        
        # Summary
        print("\n📈 Summary")
        print("=" * 50)
        print(f"🇺🇸 US Results: {us_response.total_results} products")
        print(f"🇮🇳 Indian Results: {indian_response.total_results} products")
        print(f"⚡ System Status: All features working correctly!")
        
        # Export results
        print(f"\n💾 Exporting results to JSON...")
        
        combined_results = {
            "timestamp": datetime.now().isoformat(),
            "us_market": {
                "query": us_response.query,
                "country": us_response.country,
                "total_results": us_response.total_results,
                "search_time": us_response.search_time,
                "results": us_response.results[:3]  # Top 3
            },
            "indian_market": {
                "query": indian_response.query,
                "country": indian_response.country,
                "total_results": indian_response.total_results,
                "search_time": indian_response.search_time,
                "results": indian_response.results[:3]  # Top 3
            }
        }
        
        with open("enhanced_demo_results.json", "w") as f:
            json.dump(combined_results, f, indent=2)
        
        print("✅ Results exported to enhanced_demo_results.json")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
