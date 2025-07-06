#!/usr/bin/env python3
"""
Real scraper test against actual websites.
Tests the enhanced PriceHunter system with live data.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List

from src.core.price_fetcher import PriceFetcher, SearchRequest


async def test_us_real_scrapers():
    """Test US market with real scrapers."""
    print("\n🇺🇸 Testing US Market - REAL SCRAPERS")
    print("=" * 60)
    
    fetcher = PriceFetcher()
    
    # Test the exact query that was failing before
    request = SearchRequest(
        country="US", 
        query="iPhone 16 Pro, 128GB",
        max_results=10,
        timeout=30
    )
    
    print(f"🔍 Searching for: '{request.query}'")
    print(f"📍 Country: {request.country}")
    print(f"⏱️  Timeout: {request.timeout}s")
    print(f"📊 Max results: {request.max_results}")
    print()
    
    start_time = time.time()
    try:
        response = await fetcher.search(request)
        end_time = time.time()
        
        print(f"✅ Search completed in {end_time - start_time:.2f} seconds")
        print(f"📊 Found {response.total_results} results from {len(response.sources_used)} sources")
        print(f"🏪 Sources used: {', '.join(response.sources_used)}")
        print()
        
        if response.results:
            print("🏆 Top Results:")
            for i, result in enumerate(response.results[:5], 1):
                print(f"{i}. {result['productName'][:60]}...")
                print(f"   💰 ${result['price']} {result['currency']} - {result['seller']}")
                if result.get('rating'):
                    print(f"   ⭐ {result['rating']} ({result.get('reviewsCount', 0)} reviews)")
                print(f"   🔗 {result['link'][:70]}...")
                print(f"   📈 Similarity: {result.get('similarityScore', 0):.3f}")
                print()
        else:
            print("❌ No results found")
            print("🔍 This might be due to:")
            print("   - Anti-bot protection")
            print("   - Rate limiting")
            print("   - Changed website structure")
            print("   - Network issues")
        
        return response
        
    except Exception as e:
        end_time = time.time()
        print(f"❌ Error after {end_time - start_time:.2f} seconds: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_indian_real_scrapers():
    """Test Indian market with real scrapers."""
    print("\n🇮🇳 Testing Indian Market - REAL SCRAPERS")
    print("=" * 60)
    
    fetcher = PriceFetcher()
    
    request = SearchRequest(
        country="IN", 
        query="iPhone 16 Pro, 128GB",
        max_results=10,
        timeout=30
    )
    
    print(f"🔍 Searching for: '{request.query}'")
    print(f"📍 Country: {request.country}")
    print(f"⏱️  Timeout: {request.timeout}s")
    print(f"📊 Max results: {request.max_results}")
    print()
    
    start_time = time.time()
    try:
        response = await fetcher.search(request)
        end_time = time.time()
        
        print(f"✅ Search completed in {end_time - start_time:.2f} seconds")
        print(f"📊 Found {response.total_results} results from {len(response.sources_used)} sources")
        print(f"🏪 Sources used: {', '.join(response.sources_used)}")
        print()
        
        if response.results:
            print("🏆 Top Results:")
            for i, result in enumerate(response.results[:5], 1):
                print(f"{i}. {result['productName'][:60]}...")
                print(f"   💰 ₹{result['price']} {result['currency']} - {result['seller']}")
                if result.get('rating'):
                    print(f"   ⭐ {result['rating']} ({result.get('reviewsCount', 0)} reviews)")
                print(f"   🔗 {result['link'][:70]}...")
                print(f"   📈 Similarity: {result.get('similarityScore', 0):.3f}")
                print()
        else:
            print("❌ No results found")
            print("🔍 This might be due to:")
            print("   - Anti-bot protection")
            print("   - Rate limiting") 
            print("   - Changed website structure")
            print("   - Network issues")
        
        return response
        
    except Exception as e:
        end_time = time.time()
        print(f"❌ Error after {end_time - start_time:.2f} seconds: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_different_queries():
    """Test with different product queries."""
    print("\n🔍 Testing Different Product Queries")
    print("=" * 60)
    
    test_queries = [
        ("US", "MacBook Pro M3"),
        ("US", "Samsung Galaxy S24"),
        ("IN", "OnePlus 12"),
        ("IN", "MacBook Air M2"),
    ]
    
    fetcher = PriceFetcher()
    
    for country, query in test_queries:
        print(f"\n🔍 Testing: '{query}' in {country}")
        print("-" * 40)
        
        request = SearchRequest(
            country=country,
            query=query,
            max_results=3,
            timeout=20
        )
        
        try:
            start_time = time.time()
            response = await fetcher.search(request)
            end_time = time.time()
            
            print(f"⏱️  {end_time - start_time:.1f}s | 📊 {response.total_results} results | 🏪 {len(response.sources_used)} sources")
            
            if response.results:
                result = response.results[0]  # Show top result
                print(f"🏆 {result['productName'][:50]}... - ${result['price']} from {result['seller']}")
            else:
                print("❌ No results")
                
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}...")
        
        # Small delay between requests
        await asyncio.sleep(1)


async def main():
    """Run all real scraper tests."""
    print("🚀 PriceHunter Real Scraper Test")
    print("Testing enhanced system against actual websites")
    print("=" * 70)
    
    # Test 1: US Market (the original failing query)
    us_response = await test_us_real_scrapers()
    
    # Small delay between tests
    await asyncio.sleep(2)
    
    # Test 2: Indian Market
    indian_response = await test_indian_real_scrapers()
    
    # Small delay between tests
    await asyncio.sleep(2)
    
    # Test 3: Different queries
    await test_different_queries()
    
    # Summary
    print("\n📈 Test Summary")
    print("=" * 50)
    
    if us_response:
        print(f"🇺🇸 US Market: ✅ {us_response.total_results} results in {us_response.search_time:.2f}s")
    else:
        print("🇺🇸 US Market: ❌ Failed")
    
    if indian_response:
        print(f"🇮🇳 Indian Market: ✅ {indian_response.total_results} results in {indian_response.search_time:.2f}s")
    else:
        print("🇮🇳 Indian Market: ❌ Failed")
    
    # Export results if we have any
    if us_response or indian_response:
        print(f"\n💾 Exporting results...")
        
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "real_scrapers",
            "us_market": {
                "success": us_response is not None,
                "results": us_response.total_results if us_response else 0,
                "search_time": us_response.search_time if us_response else 0,
                "sources": us_response.sources_used if us_response else [],
                "top_result": us_response.results[0] if us_response and us_response.results else None
            },
            "indian_market": {
                "success": indian_response is not None,
                "results": indian_response.total_results if indian_response else 0,
                "search_time": indian_response.search_time if indian_response else 0,
                "sources": indian_response.sources_used if indian_response else [],
                "top_result": indian_response.results[0] if indian_response and indian_response.results else None
            }
        }
        
        with open("real_scraper_test_results.json", "w") as f:
            json.dump(export_data, f, indent=2)
        
        print("✅ Results exported to real_scraper_test_results.json")
    
    print(f"\n🎯 Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
