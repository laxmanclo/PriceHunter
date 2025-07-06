"""
Result processor for normalizing and ranking price comparison results.
Handles deduplication, price normalization, and intelligent ranking.
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
from fuzzywuzzy import fuzz
import price_parser
from currency_converter import CurrencyConverter

from .base_scraper import ProductResult
from .product_matcher import ProductMatcher


@dataclass
class ProcessedResult:
    """Processed and normalized result."""
    original_result: ProductResult
    normalized_price: float
    normalized_currency: str
    similarity_score: float
    duplicate_group: Optional[str] = None
    final_rank: int = 0


class ResultProcessor:
    """Processes and normalizes price comparison results."""

    def __init__(self):
        """Initialize the result processor."""
        self.currency_converter = CurrencyConverter()
        self.product_matcher = ProductMatcher()
        self.duplicate_threshold = 0.85
        self.price_variance_threshold = 0.1

    def process_results(self,
                       results: List[ProductResult],
                       query: str,
                       target_currency: str = "USD") -> List[Dict[str, Any]]:
        """
        Process and rank all results.

        Args:
            results: List of raw results from scrapers
            query: Original search query
            target_currency: Target currency for normalization

        Returns:
            List of processed results sorted by price
        """
        if not results:
            return []

        logger.info(f"Processing {len(results)} results for query: {query}")

        # Step 1: Normalize prices and currencies
        processed_results = []
        for result in results:
            try:
                processed = self._normalize_result(result, target_currency)
                if processed:
                    processed_results.append(processed)
            except Exception as e:
                logger.warning(f"Failed to process result from {result.source}: {e}")

        # Step 2: Calculate similarity scores
        for processed in processed_results:
            processed.similarity_score = self._calculate_similarity(
                processed.original_result.product_name, query
            )

        # Step 3: Remove duplicates
        deduplicated = self._remove_duplicates(processed_results)

        # Step 4: Rank results
        ranked_results = self._rank_results(deduplicated, query)

        # Step 5: Convert to output format
        output_results = []
        for processed in ranked_results:
            result_dict = processed.original_result.to_dict()
            result_dict["price"] = str(int(processed.normalized_price))
            result_dict["currency"] = processed.normalized_currency
            result_dict["similarityScore"] = processed.similarity_score
            result_dict["rank"] = processed.final_rank
            output_results.append(result_dict)

        logger.info(f"Processed results: {len(output_results)} final results")
        return output_results

    def _normalize_result(self, result: ProductResult, target_currency: str) -> Optional[ProcessedResult]:
        """Normalize a single result."""
        try:
            # Parse price
            price_info = price_parser.parse_price(result.price)
            if not price_info or not price_info.amount:
                logger.warning(f"Could not parse price: {result.price}")
                return None

            price_amount = float(price_info.amount)
            source_currency = price_info.currency or result.currency or target_currency

            # Convert currency if needed
            if source_currency != target_currency:
                try:
                    converted_price = self.currency_converter.convert(
                        price_amount, source_currency, target_currency
                    )
                except Exception as e:
                    logger.warning(f"Currency conversion failed: {e}")
                    converted_price = price_amount
                    target_currency = source_currency
            else:
                converted_price = price_amount

            return ProcessedResult(
                original_result=result,
                normalized_price=converted_price,
                normalized_currency=target_currency,
                similarity_score=0.0  # Will be calculated later
            )

        except Exception as e:
            logger.error(f"Error normalizing result: {e}")
            return None

    def _calculate_similarity(self, product_name: str, query: str) -> float:
        """Calculate similarity between product name and query."""
        if not product_name or not query:
            return 0.0

        # Clean and normalize strings
        clean_product = self._clean_text(product_name.lower())
        clean_query = self._clean_text(query.lower())

        # Calculate different similarity metrics
        token_sort_ratio = fuzz.token_sort_ratio(clean_product, clean_query)
        token_set_ratio = fuzz.token_set_ratio(clean_product, clean_query)
        partial_ratio = fuzz.partial_ratio(clean_product, clean_query)

        # Weighted average
        similarity = (
            token_sort_ratio * 0.4 +
            token_set_ratio * 0.4 +
            partial_ratio * 0.2
        ) / 100.0

        return similarity

    def _clean_text(self, text: str) -> str:
        """Clean text for comparison."""
        # Remove special characters and extra spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _remove_duplicates(self, results: List[ProcessedResult]) -> List[ProcessedResult]:
        """Remove duplicate results based on similarity."""
        if len(results) <= 1:
            return results

        # Group similar results
        groups = []
        for result in results:
            added_to_group = False

            for group in groups:
                # Check if this result is similar to any in the group
                for group_result in group:
                    similarity = self._calculate_similarity(
                        result.original_result.product_name,
                        group_result.original_result.product_name
                    )

                    # Also check price similarity
                    price_diff = abs(result.normalized_price - group_result.normalized_price)
                    price_similarity = 1.0 - (price_diff / max(result.normalized_price, group_result.normalized_price))

                    if (similarity > self.duplicate_threshold and
                        price_similarity > (1.0 - self.price_variance_threshold)):
                        group.append(result)
                        added_to_group = True
                        break

                if added_to_group:
                    break

            if not added_to_group:
                groups.append([result])

        # Select best result from each group
        deduplicated = []
        for group in groups:
            # Sort by similarity score and price
            best_result = max(group, key=lambda x: (x.similarity_score, -x.normalized_price))

            # Mark duplicate group
            group_id = hashlib.md5(
                best_result.original_result.product_name.encode()
            ).hexdigest()[:8]
            best_result.duplicate_group = group_id

            deduplicated.append(best_result)

        logger.info(f"Deduplication: {len(results)} -> {len(deduplicated)} results")
        return deduplicated

    def _rank_results(self, results: List[ProcessedResult], query: str) -> List[ProcessedResult]:
        """Rank results based on multiple factors."""
        if not results:
            return results

        # Calculate ranking scores
        for result in results:
            score = self._calculate_ranking_score(result, query)
            result.final_rank = score

        # Sort by ranking score (higher is better) then by price (lower is better)
        ranked = sorted(results, key=lambda x: (-x.final_rank, x.normalized_price))

        # Assign final rank positions
        for i, result in enumerate(ranked):
            result.final_rank = i + 1

        return ranked

    def _calculate_ranking_score(self, result: ProcessedResult, query: str) -> float:
        """Calculate comprehensive ranking score."""
        score = 0.0

        # Similarity score (40% weight)
        score += result.similarity_score * 0.4

        # Source reliability (20% weight)
        source_scores = {
            'amazon': 0.9,
            'apple': 0.95,
            'bestbuy': 0.85,
            'walmart': 0.8,
            'target': 0.75,
            'ebay': 0.7,
            'default': 0.6
        }
        source_name = result.original_result.source.lower()
        source_score = source_scores.get(source_name, source_scores['default'])
        score += source_score * 0.2

        # Availability bonus (15% weight)
        if result.original_result.availability.lower() in ['in stock', 'available']:
            score += 0.15
        elif 'limited' in result.original_result.availability.lower():
            score += 0.1

        # Rating bonus (10% weight)
        if result.original_result.rating:
            rating_score = min(result.original_result.rating / 5.0, 1.0)
            score += rating_score * 0.1

        # Reviews count bonus (10% weight)
        if result.original_result.reviews_count:
            # Logarithmic scale for reviews
            import math
            reviews_score = min(math.log10(result.original_result.reviews_count + 1) / 4.0, 1.0)
            score += reviews_score * 0.1

        # Shipping cost penalty (5% weight)
        if result.original_result.shipping_cost:
            try:
                shipping_price = price_parser.parse_price(result.original_result.shipping_cost)
                if shipping_price and shipping_price.amount:
                    if float(shipping_price.amount) == 0:
                        score += 0.05  # Free shipping bonus
                    else:
                        # Penalty for expensive shipping
                        shipping_ratio = float(shipping_price.amount) / result.normalized_price
                        penalty = min(shipping_ratio * 0.05, 0.05)
                        score -= penalty
            except:
                pass

        return max(0.0, min(1.0, score))  # Clamp between 0 and 1