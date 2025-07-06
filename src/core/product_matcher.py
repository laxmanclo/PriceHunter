#!/usr/bin/env python3
"""
Advanced product matching system using ML and NLP techniques.
Provides sophisticated product similarity scoring and duplicate detection.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from fuzzywuzzy import fuzz
from loguru import logger


@dataclass
class ProductFeatures:
    """Extracted product features for matching."""
    brand: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    storage: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    category: Optional[str] = None
    key_specs: List[str] = None

    def __post_init__(self):
        if self.key_specs is None:
            self.key_specs = []


class ProductMatcher:
    """Advanced product matching and similarity scoring."""

    def __init__(self):
        """Initialize the product matcher."""
        self.brand_patterns = {
            'apple': r'\b(apple|iphone|ipad|macbook|imac|airpods)\b',
            'samsung': r'\b(samsung|galaxy)\b',
            'oneplus': r'\b(oneplus|one\s*plus)\b',
            'xiaomi': r'\b(xiaomi|mi|redmi)\b',
            'oppo': r'\b(oppo)\b',
            'vivo': r'\b(vivo)\b',
            'realme': r'\b(realme)\b',
            'google': r'\b(google|pixel)\b',
            'sony': r'\b(sony|xperia)\b',
            'lg': r'\b(lg)\b',
            'motorola': r'\b(motorola|moto)\b',
            'nokia': r'\b(nokia)\b',
            'huawei': r'\b(huawei|honor)\b',
        }

        self.storage_patterns = {
            'storage': r'\b(\d+)\s*(gb|tb|mb)\b',
            'ram': r'\b(\d+)\s*gb\s*(ram|memory)\b',
        }

        self.color_patterns = {
            'colors': r'\b(black|white|blue|red|green|gold|silver|rose|pink|purple|yellow|orange|gray|grey|titanium|natural|pro|max)\b'
        }

        self.model_patterns = {
            'iphone': r'\biphone\s*(\d+(?:\s*pro)?(?:\s*max)?)\b',
            'galaxy': r'\bgalaxy\s*([a-z]\d+(?:\s*\+)?)\b',
            'pixel': r'\bpixel\s*(\d+(?:\s*pro)?(?:\s*xl)?)\b',
        }

    def extract_features(self, product_name: str, query: str = "") -> ProductFeatures:
        """Extract structured features from product name and query."""
        text = f"{product_name} {query}".lower()
        features = ProductFeatures()

        # Extract brand
        features.brand = self._extract_brand(text)

        # Extract model
        features.model = self._extract_model(text, features.brand)

        # Extract storage
        features.storage = self._extract_storage(text)

        # Extract color
        features.color = self._extract_color(text)

        # Extract category
        features.category = self._extract_category(text)

        # Extract key specifications
        features.key_specs = self._extract_key_specs(text)

        return features

    def calculate_similarity(self, product1: str, product2: str, query: str = "") -> float:
        """Calculate sophisticated similarity score between two products."""
        # Extract features for both products
        features1 = self.extract_features(product1, query)
        features2 = self.extract_features(product2, query)

        # Calculate different similarity components
        scores = {}

        # 1. Basic string similarity
        scores['fuzzy'] = fuzz.token_sort_ratio(product1.lower(), product2.lower()) / 100.0

        # 2. Brand similarity
        scores['brand'] = self._compare_brands(features1.brand, features2.brand)

        # 3. Model similarity
        scores['model'] = self._compare_models(features1.model, features2.model)

        # 4. Storage similarity
        scores['storage'] = self._compare_storage(features1.storage, features2.storage)

        # 5. Color similarity
        scores['color'] = self._compare_colors(features1.color, features2.color)

        # 6. Query relevance
        scores['query_relevance'] = self._calculate_query_relevance(product1, product2, query)

        # Weighted combination
        weights = {
            'fuzzy': 0.3,
            'brand': 0.25,
            'model': 0.2,
            'storage': 0.1,
            'color': 0.05,
            'query_relevance': 0.1
        }

        final_score = sum(scores[key] * weights[key] for key in scores)
        
        logger.debug(f"Similarity scores: {scores} -> {final_score:.3f}")
        return final_score

    def is_duplicate(self, product1: str, product2: str, price1: float, price2: float, 
                    threshold: float = 0.85, price_variance: float = 0.15) -> bool:
        """Determine if two products are duplicates."""
        similarity = self.calculate_similarity(product1, product2)
        
        # Check price variance
        if price1 > 0 and price2 > 0:
            price_diff = abs(price1 - price2) / max(price1, price2)
            if price_diff > price_variance:
                # Large price difference suggests different products
                threshold += 0.05
        
        return similarity >= threshold

    def _extract_brand(self, text: str) -> Optional[str]:
        """Extract brand from text."""
        for brand, pattern in self.brand_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return brand
        return None

    def _extract_model(self, text: str, brand: Optional[str]) -> Optional[str]:
        """Extract model from text."""
        if brand and brand in self.model_patterns:
            pattern = self.model_patterns[brand]
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Generic model extraction
        model_match = re.search(r'\b([a-z]+\s*\d+(?:\s*[a-z]+)*)\b', text, re.IGNORECASE)
        if model_match:
            return model_match.group(1).strip()
        
        return None

    def _extract_storage(self, text: str) -> Optional[str]:
        """Extract storage information."""
        storage_match = re.search(self.storage_patterns['storage'], text, re.IGNORECASE)
        if storage_match:
            return f"{storage_match.group(1)}{storage_match.group(2).upper()}"
        return None

    def _extract_color(self, text: str) -> Optional[str]:
        """Extract color information."""
        color_match = re.search(self.color_patterns['colors'], text, re.IGNORECASE)
        if color_match:
            return color_match.group(1).lower()
        return None

    def _extract_category(self, text: str) -> Optional[str]:
        """Extract product category."""
        categories = {
            'smartphone': r'\b(phone|smartphone|mobile)\b',
            'laptop': r'\b(laptop|notebook|macbook)\b',
            'tablet': r'\b(tablet|ipad)\b',
            'headphones': r'\b(headphones|earphones|airpods|earbuds)\b',
            'watch': r'\b(watch|smartwatch)\b',
        }
        
        for category, pattern in categories.items():
            if re.search(pattern, text, re.IGNORECASE):
                return category
        return None

    def _extract_key_specs(self, text: str) -> List[str]:
        """Extract key specifications."""
        specs = []
        
        # RAM
        ram_match = re.search(r'\b(\d+)\s*gb\s*(ram|memory)\b', text, re.IGNORECASE)
        if ram_match:
            specs.append(f"{ram_match.group(1)}GB RAM")
        
        # Camera
        camera_match = re.search(r'\b(\d+)\s*mp\b', text, re.IGNORECASE)
        if camera_match:
            specs.append(f"{camera_match.group(1)}MP")
        
        # Display size
        display_match = re.search(r'\b(\d+\.?\d*)\s*inch\b', text, re.IGNORECASE)
        if display_match:
            specs.append(f"{display_match.group(1)}\"")
        
        return specs

    def _compare_brands(self, brand1: Optional[str], brand2: Optional[str]) -> float:
        """Compare brand similarity."""
        if brand1 is None or brand2 is None:
            return 0.5  # Neutral score
        return 1.0 if brand1 == brand2 else 0.0

    def _compare_models(self, model1: Optional[str], model2: Optional[str]) -> float:
        """Compare model similarity."""
        if model1 is None or model2 is None:
            return 0.5
        return fuzz.ratio(model1.lower(), model2.lower()) / 100.0

    def _compare_storage(self, storage1: Optional[str], storage2: Optional[str]) -> float:
        """Compare storage similarity."""
        if storage1 is None or storage2 is None:
            return 0.5
        return 1.0 if storage1 == storage2 else 0.3

    def _compare_colors(self, color1: Optional[str], color2: Optional[str]) -> float:
        """Compare color similarity."""
        if color1 is None or color2 is None:
            return 0.8  # Colors are less important
        return 1.0 if color1 == color2 else 0.6

    def _calculate_query_relevance(self, product1: str, product2: str, query: str) -> float:
        """Calculate how relevant products are to the original query."""
        if not query:
            return 0.5
        
        relevance1 = fuzz.partial_ratio(query.lower(), product1.lower()) / 100.0
        relevance2 = fuzz.partial_ratio(query.lower(), product2.lower()) / 100.0
        
        # Return average relevance
        return (relevance1 + relevance2) / 2.0

    def rank_products(self, products: List[Dict], query: str) -> List[Dict]:
        """Rank products by relevance to query."""
        for product in products:
            product_name = product.get('productName', '')
            relevance = fuzz.partial_ratio(query.lower(), product_name.lower()) / 100.0
            product['relevanceScore'] = relevance
        
        # Sort by relevance score (descending)
        return sorted(products, key=lambda x: x.get('relevanceScore', 0), reverse=True)

    def group_similar_products(self, products: List[Dict], threshold: float = 0.8) -> List[List[Dict]]:
        """Group similar products together."""
        groups = []
        used_indices = set()
        
        for i, product1 in enumerate(products):
            if i in used_indices:
                continue
                
            group = [product1]
            used_indices.add(i)
            
            for j, product2 in enumerate(products[i+1:], i+1):
                if j in used_indices:
                    continue
                    
                similarity = self.calculate_similarity(
                    product1.get('productName', ''),
                    product2.get('productName', '')
                )
                
                if similarity >= threshold:
                    group.append(product2)
                    used_indices.add(j)
            
            groups.append(group)
        
        return groups
