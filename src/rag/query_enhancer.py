"""
Query enhancement using RAG for better product search.
Enhances user queries with product knowledge and context.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from .knowledge_base import ProductKnowledgeBase


@dataclass
class EnhancedQuery:
    """Enhanced query with additional context."""
    original_query: str
    enhanced_query: str
    extracted_features: Dict[str, Any]
    suggested_alternatives: List[str]
    price_context: Optional[Dict[str, Any]]
    confidence_score: float


class QueryEnhancer:
    """Enhances search queries using product knowledge."""
    
    def __init__(self, knowledge_base: ProductKnowledgeBase):
        """Initialize query enhancer."""
        self.knowledge_base = knowledge_base
        
        # Product feature patterns
        self.storage_patterns = [
            r'(\d+)\s*(gb|tb)',
            r'(\d+)\s*gigabyte',
            r'(\d+)\s*terabyte'
        ]
        
        self.memory_patterns = [
            r'(\d+)\s*gb\s*(ram|memory)',
            r'(\d+)\s*gb\s*ram',
            r'(\d+)\s*gigabyte\s*(ram|memory)'
        ]
        
        self.color_patterns = [
            r'\b(black|white|silver|gold|rose\s*gold|space\s*gray|midnight|starlight|blue|red|green|purple|pink|yellow|orange)\b'
        ]
        
        self.brand_patterns = [
            r'\b(apple|samsung|google|oneplus|xiaomi|huawei|sony|lg|motorola|nokia|oppo|vivo|realme)\b',
            r'\b(dell|hp|lenovo|asus|acer|msi|razer|alienware|surface|macbook)\b'
        ]
        
        logger.info("Query enhancer initialized")
    
    def extract_features(self, query: str) -> Dict[str, Any]:
        """Extract product features from query."""
        query_lower = query.lower()
        features = {}
        
        # Extract storage
        for pattern in self.storage_patterns:
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            if matches:
                storage_value, unit = matches[0]
                if unit.lower() == 'tb':
                    storage_gb = int(storage_value) * 1024
                else:
                    storage_gb = int(storage_value)
                features['storage'] = f"{storage_value}{unit.upper()}"
                features['storage_gb'] = storage_gb
                break
        
        # Extract memory/RAM
        for pattern in self.memory_patterns:
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            if matches:
                if len(matches[0]) == 2:
                    memory_value, _ = matches[0]
                else:
                    memory_value = matches[0]
                features['memory'] = f"{memory_value}GB"
                features['memory_gb'] = int(memory_value)
                break
        
        # Extract colors
        color_matches = re.findall(self.color_patterns[0], query_lower, re.IGNORECASE)
        if color_matches:
            features['color'] = color_matches[0].title()
        
        # Extract brands
        for pattern in self.brand_patterns:
            brand_matches = re.findall(pattern, query_lower, re.IGNORECASE)
            if brand_matches:
                features['brand'] = brand_matches[0].title()
                break
        
        # Extract model numbers/names
        model_patterns = [
            r'\b(iphone\s*\d+(?:\s*pro)?(?:\s*max)?)\b',
            r'\b(galaxy\s*s\d+(?:\s*ultra)?(?:\s*plus)?)\b',
            r'\b(pixel\s*\d+(?:\s*pro)?(?:\s*xl)?)\b',
            r'\b(oneplus\s*\d+(?:\s*pro)?)\b',
            r'\b(macbook\s*(?:air|pro)?(?:\s*m\d+)?)\b'
        ]
        
        for pattern in model_patterns:
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            if matches:
                features['model'] = matches[0].title()
                break
        
        return features
    
    def enhance_query(self, query: str, country: str = "US") -> EnhancedQuery:
        """
        Enhance query with product knowledge and context.
        
        Args:
            query: Original search query
            country: Target country for search
            
        Returns:
            Enhanced query with additional context
        """
        logger.info(f"Enhancing query: '{query}' for country: {country}")
        
        # Extract features from original query
        extracted_features = self.extract_features(query)
        
        # Search knowledge base for relevant products
        knowledge_results = self.knowledge_base.search_knowledge(query, top_k=3)
        
        # Build enhanced query
        enhanced_parts = [query]
        suggested_alternatives = []
        price_context = None
        confidence_score = 0.0
        
        if knowledge_results:
            best_match = knowledge_results[0]
            confidence_score = best_match["relevance_score"]
            
            # If we have a good match, enhance the query
            if confidence_score > 0.5:
                metadata = best_match["metadata"]
                
                if metadata.get("type") == "product_knowledge":
                    product_id = metadata["product_id"]
                    
                    # Get product knowledge
                    if product_id in self.knowledge_base.product_knowledge:
                        product = self.knowledge_base.product_knowledge[product_id]
                        
                        # Add missing specifications to query
                        if 'storage' not in extracted_features and product.specifications.get('storage_options'):
                            # Add most common storage option
                            common_storage = product.specifications['storage_options'][0]
                            enhanced_parts.append(common_storage)
                            extracted_features['storage'] = common_storage
                        
                        # Add brand if missing
                        if 'brand' not in extracted_features:
                            enhanced_parts.append(product.brand)
                            extracted_features['brand'] = product.brand
                        
                        # Get alternatives
                        suggested_alternatives = product.alternatives[:3]
                        
                        # Get price context
                        price_context = {
                            "expected_range": product.price_range,
                            "market_insights": product.market_insights
                        }
                        
                        # Get price insights if available
                        price_insight = self.knowledge_base.get_price_insights(product.product_name)
                        if price_insight:
                            price_context.update({
                                "current_price": price_insight.current_price,
                                "trend": price_insight.price_trend,
                                "best_time_to_buy": price_insight.best_time_to_buy
                            })
        
        # Build final enhanced query
        enhanced_query = " ".join(enhanced_parts)
        
        # Add country-specific enhancements
        if country == "IN":
            # Add India-specific terms for better local results
            if any(brand in query.lower() for brand in ['iphone', 'apple']):
                enhanced_query += " India official"
            elif any(brand in query.lower() for brand in ['samsung', 'oneplus']):
                enhanced_query += " India variant"
        
        result = EnhancedQuery(
            original_query=query,
            enhanced_query=enhanced_query,
            extracted_features=extracted_features,
            suggested_alternatives=suggested_alternatives,
            price_context=price_context,
            confidence_score=confidence_score
        )
        
        logger.info(f"Enhanced query: '{enhanced_query}' (confidence: {confidence_score:.3f})")
        
        return result
    
    def suggest_query_improvements(self, query: str) -> List[str]:
        """Suggest improvements to the search query."""
        suggestions = []
        
        # Check if query is too vague
        if len(query.split()) < 2:
            suggestions.append("Try adding more specific details like storage size, color, or model")
        
        # Check for missing brand
        features = self.extract_features(query)
        if 'brand' not in features:
            suggestions.append("Consider specifying a brand (Apple, Samsung, Google, etc.)")
        
        # Check for missing storage
        if 'storage' not in features and any(term in query.lower() for term in ['phone', 'iphone', 'galaxy', 'pixel']):
            suggestions.append("Add storage capacity (128GB, 256GB, etc.) for better results")
        
        # Check for missing model
        if 'model' not in features:
            suggestions.append("Include specific model name or number")
        
        return suggestions
    
    def get_query_context(self, query: str) -> Dict[str, Any]:
        """Get additional context for a query."""
        features = self.extract_features(query)
        knowledge_results = self.knowledge_base.search_knowledge(query, top_k=1)
        
        context = {
            "extracted_features": features,
            "feature_count": len(features),
            "has_knowledge_match": len(knowledge_results) > 0,
            "suggestions": self.suggest_query_improvements(query)
        }
        
        if knowledge_results:
            context["knowledge_confidence"] = knowledge_results[0]["relevance_score"]
            context["matched_product"] = knowledge_results[0]["metadata"]
        
        return context
