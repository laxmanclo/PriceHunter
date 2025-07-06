#!/usr/bin/env python3
"""
PriceHunter CLI - Command line interface for price comparison.
"""

import asyncio
import json
import sys
from typing import Dict, Any
import argparse
from loguru import logger

from src.core.price_fetcher import PriceFetcher, SearchRequest


async def search_prices(country: str, query: str) -> Dict[str, Any]:
    """Search for product prices."""
    logger.info(f"Searching for '{query}' in {country}")

    try:
        # Initialize price fetcher
        fetcher = PriceFetcher()

        # Create search request
        request = SearchRequest(
            country=country,
            query=query
        )

        # Perform search
        response = await fetcher.search(request)

        return {
            "success": True,
            "data": {
                "results": response.results,
                "query": response.query,
                "country": response.country,
                "search_time_seconds": response.search_time,
                "total_results": response.total_results,
                "sources_used": response.sources_used
            }
        }

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def format_results(response: Dict[str, Any]) -> str:
    """Format search results for display."""
    if not response.get("success"):
        return f"❌ Error: {response.get('error', 'Unknown error')}"

    data = response.get("data", {})
    results = data.get("results", [])

    if not results:
        return "❌ No results found"

    output = []
    output.append(f"🔍 Found {len(results)} results for '{data.get('query', '')}'")
    output.append(f"📍 Country: {data.get('country', '')}")
    output.append(f"⏱️  Search time: {data.get('search_time_seconds', 0):.2f}s")
    output.append("")

    for i, result in enumerate(results[:10], 1):  # Show top 10
        output.append(f"{i}. {result.get('product_name', 'Unknown Product')}")
        output.append(f"   💰 Price: {result.get('currency', '')} {result.get('price', 'N/A')}")
        output.append(f"   🏪 Source: {result.get('source', 'Unknown')}")
        output.append(f"   🔗 Link: {result.get('link', 'N/A')}")

        if result.get('availability'):
            output.append(f"   📦 Availability: {result.get('availability')}")
        if result.get('rating'):
            output.append(f"   ⭐ Rating: {result.get('rating')}")
        if result.get('shipping_cost'):
            output.append(f"   🚚 Shipping: {result.get('shipping_cost')}")

        output.append("")

    return "\n".join(output)


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="PriceHunter - Find the best prices for any product",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --country US --query "iPhone 16 Pro, 128GB"
  python cli.py --country IN --query "Samsung Galaxy S24"
  python cli.py --country UK --query "MacBook Air M2"
        """
    )

    parser.add_argument(
        "--country",
        required=True,
        help="Country code (US, UK, IN, CA, etc.)"
    )

    parser.add_argument(
        "--query",
        required=True,
        help="Product search query"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    # Perform search
    print("🔍 Searching for best prices...")
    response = await search_prices(args.country, args.query)

    # Output results
    if args.json:
        print(json.dumps(response, indent=2))
    else:
        print(format_results(response))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Search cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)