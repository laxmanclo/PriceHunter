"""
Main PriceFetcher engine that orchestrates all scrapers and APIs.
This is the core component that coordinates price fetching from multiple sources.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import os
from concurrent.futures import ThreadPoolExecutor

from .base_scraper import BaseScraper, ProductResult, ScraperType
from .result_processor import ResultProcessor
from ..rag import RAGEngine, RAGInsight, EnhancedQuery


@dataclass
class SearchRequest:
    """Search request structure."""
    query: str
    country: str
    max_results: int = 50
    timeout: int = 60
    target_currency: str = "USD"
    include_sources: Optional[List[str]] = None
    exclude_sources: Optional[List[str]] = None


@dataclass
class SearchResponse:
    """Search response structure."""
    results: List[Dict[str, Any]]
    total_results: int
    search_time: float
    sources_used: List[str]
    query: str
    country: str
    timestamp: str
    enhanced_query: Optional[EnhancedQuery] = None
    rag_insights: Optional[List[RAGInsight]] = None


class PriceFetcher:
    """Main price fetching engine."""

    def __init__(self, max_concurrent_scrapers: int = 10, enable_rag: bool = True):
        """
        Initialize the PriceFetcher.

        Args:
            max_concurrent_scrapers: Maximum number of concurrent scrapers
            enable_rag: Whether to enable RAG features
        """
        self.scrapers: List[BaseScraper] = []
        self.result_processor = ResultProcessor()
        self.max_concurrent_scrapers = max_concurrent_scrapers
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_scrapers)

        # Initialize RAG engine
        self.enable_rag = enable_rag
        self.rag_engine = RAGEngine() if enable_rag else None

        # Load scrapers
        self._load_scrapers()

    def _load_scrapers(self):
        """Load all available scrapers."""
        logger.info("Loading scrapers...")

        # Import and register scrapers
        try:
            # E-commerce scrapers
            from ..scrapers.ecommerce.amazon_scraper import AmazonScraper
            from ..scrapers.ecommerce.ebay_scraper import EbayScraper
            from ..scrapers.ecommerce.bestbuy_scraper import BestBuyScraper
            from ..scrapers.ecommerce.walmart_scraper import WalmartScraper
            from ..scrapers.ecommerce.target_scraper import TargetScraper
            from ..scrapers.ecommerce.flipkart_scraper import FlipkartScraper
            from ..scrapers.ecommerce.amazon_india_scraper import AmazonIndiaScraper

            # Regional scrapers
            from ..scrapers.regional.apple_store_scraper import AppleStoreScraper
            from ..scrapers.regional.sangeetha_scraper import SangeethaScraper

            # Register scrapers
            scraper_classes = [
                AmazonScraper, EbayScraper, BestBuyScraper, WalmartScraper,
                TargetScraper, FlipkartScraper, AmazonIndiaScraper,
                AppleStoreScraper, SangeethaScraper
            ]

            for scraper_class in scraper_classes:
                try:
                    scraper = scraper_class()
                    self.scrapers.append(scraper)
                    logger.info(f"Loaded scraper: {scraper.name}")
                except Exception as e:
                    logger.warning(f"Failed to load scraper {scraper_class.__name__}: {e}")

        except ImportError as e:
            logger.warning(f"Some scrapers not available: {e}")

        logger.info(f"Loaded {len(self.scrapers)} scrapers")

    def register_scraper(self, scraper: BaseScraper):
        """Register a new scraper."""
        self.scrapers.append(scraper)
        logger.info(f"Registered scraper: {scraper.name}")

    def get_available_scrapers(self, country: str) -> List[BaseScraper]:
        """Get scrapers available for a specific country."""
        available = []
        for scraper in self.scrapers:
            if scraper.is_supported_country(country):
                available.append(scraper)
        return available

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Search for products across all available sources.

        Args:
            request: Search request parameters

        Returns:
            SearchResponse with results
        """
        start_time = time.time()
        logger.info(f"Starting search for '{request.query}' in {request.country}")

        # RAG: Enhance query if RAG is enabled
        enhanced_query = None
        search_query = request.query

        if self.enable_rag and self.rag_engine:
            enhanced_query = self.rag_engine.enhance_search_query(request.query, request.country)
            search_query = enhanced_query.enhanced_query
            logger.info(f"RAG enhanced query: '{search_query}' (confidence: {enhanced_query.confidence_score:.3f})")

        # Get available scrapers for the country
        available_scrapers = self.get_available_scrapers(request.country)

        # Filter scrapers based on include/exclude lists
        if request.include_sources:
            available_scrapers = [
                s for s in available_scrapers
                if s.name.lower() in [src.lower() for src in request.include_sources]
            ]
        if request.exclude_sources:
            available_scrapers = [
                s for s in available_scrapers
                if s.name.lower() not in [src.lower() for src in request.exclude_sources]
            ]

        # Sort scrapers by priority
        available_scrapers.sort(key=lambda s: s.get_priority(request.country))

        logger.info(f"Using {len(available_scrapers)} scrapers: {[s.name for s in available_scrapers]}")

        # Execute searches concurrently
        all_results = []
        sources_used = []

        # Limit concurrent scrapers
        semaphore = asyncio.Semaphore(self.max_concurrent_scrapers)

        async def run_scraper(scraper: BaseScraper) -> List[ProductResult]:
            """Run a single scraper with semaphore control."""
            async with semaphore:
                try:
                    async with scraper:
                        results = await asyncio.wait_for(
                            scraper.search(search_query, request.country),
                            timeout=request.timeout / len(available_scrapers)
                        )
                        sources_used.append(scraper.name)
                        logger.info(f"{scraper.name}: Found {len(results)} results")
                        return results
                except asyncio.TimeoutError:
                    logger.warning(f"{scraper.name}: Timeout")
                    return []
                except Exception as e:
                    logger.error(f"{scraper.name}: Error - {e}")
                    return []

        # Run all scrapers concurrently
        tasks = [run_scraper(scraper) for scraper in available_scrapers]
        scraper_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all results
        for results in scraper_results:
            if isinstance(results, list):
                all_results.extend(results)

        logger.info(f"Collected {len(all_results)} total results")

        # Process and rank results
        processed_results = self.result_processor.process_results(
            all_results, request.query, request.target_currency
        )

        # Limit results
        if request.max_results > 0:
            processed_results = processed_results[:request.max_results]

        # RAG: Generate insights if RAG is enabled
        rag_insights = None
        if self.enable_rag and self.rag_engine and processed_results:
            rag_insights = self.rag_engine.analyze_search_results(
                request.query, processed_results, enhanced_query
            )
            logger.info(f"RAG generated {len(rag_insights)} insights")

            # Learn from search results
            self.rag_engine.learn_from_search(request.query, processed_results)

        search_time = time.time() - start_time

        response = SearchResponse(
            results=processed_results,
            total_results=len(processed_results),
            search_time=search_time,
            sources_used=sources_used,
            query=request.query,
            country=request.country,
            timestamp=datetime.now().isoformat(),
            enhanced_query=enhanced_query,
            rag_insights=rag_insights
        )

        logger.info(f"Search completed in {search_time:.2f}s with {len(processed_results)} results")
        return response