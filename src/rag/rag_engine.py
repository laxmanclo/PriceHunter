"""
RAG (Retrieval-Augmented Generation) engine for PriceHunter.
Combines product knowledge with search results for intelligent insights.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from loguru import logger

from .knowledge_base import ProductKnowledgeBase, ProductKnowledge, PriceInsight
from .query_enhancer import QueryEnhancer, EnhancedQuery


@dataclass
class RAGInsight:
    """RAG-generated insight about search results."""
    query: str
    insight_type: str  # "price_analysis", "product_comparison", "recommendation"
    title: str
    content: str
    confidence_score: float
    supporting_data: Dict[str, Any]
    generated_at: str = ""
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


class RAGEngine:
    """RAG engine for intelligent product insights."""
    
    def __init__(self, knowledge_base: Optional[ProductKnowledgeBase] = None):
        """Initialize RAG engine."""
        self.knowledge_base = knowledge_base or ProductKnowledgeBase()
        self.query_enhancer = QueryEnhancer(self.knowledge_base)
        
        logger.info("RAG engine initialized")
    
    def enhance_search_query(self, query: str, country: str = "US") -> EnhancedQuery:
        """Enhance search query using product knowledge."""
        return self.query_enhancer.enhance_query(query, country)
    
    def analyze_search_results(self, query: str, results: List[Dict[str, Any]], 
                             enhanced_query: Optional[EnhancedQuery] = None) -> List[RAGInsight]:
        """
        Analyze search results and generate insights.
        
        Args:
            query: Original search query
            results: Search results from price fetcher
            enhanced_query: Enhanced query information
            
        Returns:
            List of RAG insights
        """
        insights = []
        
        if not results:
            return insights
        
        # Price analysis insight
        price_insight = self._generate_price_analysis(query, results, enhanced_query)
        if price_insight:
            insights.append(price_insight)
        
        # Product comparison insight
        comparison_insight = self._generate_product_comparison(query, results, enhanced_query)
        if comparison_insight:
            insights.append(comparison_insight)
        
        # Recommendation insight
        recommendation_insight = self._generate_recommendations(query, results, enhanced_query)
        if recommendation_insight:
            insights.append(recommendation_insight)
        
        # Market insight
        market_insight = self._generate_market_analysis(query, results, enhanced_query)
        if market_insight:
            insights.append(market_insight)
        
        return insights
    
    def _generate_price_analysis(self, query: str, results: List[Dict[str, Any]], 
                                enhanced_query: Optional[EnhancedQuery] = None) -> Optional[RAGInsight]:
        """Generate price analysis insight."""
        if len(results) < 2:
            return None
        
        prices = [float(r['price']) for r in results if r.get('price')]
        if not prices:
            return None
        
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        price_variance = max_price - min_price
        
        # Get expected price range from knowledge base
        expected_range = None
        if enhanced_query and enhanced_query.price_context:
            expected_range = enhanced_query.price_context.get("expected_range")
        
        # Generate analysis content
        content_parts = [
            f"Found {len(results)} results with prices ranging from ${min_price:.0f} to ${max_price:.0f}.",
            f"Average price: ${avg_price:.0f}"
        ]
        
        if price_variance > avg_price * 0.3:  # High variance
            content_parts.append(f"⚠️ High price variance (${price_variance:.0f}) - compare carefully!")
        
        if expected_range:
            expected_min = expected_range.get('min', 0)
            expected_max = expected_range.get('max', 0)
            
            if min_price < expected_min:
                content_parts.append(f"💰 Great deal! Lowest price (${min_price:.0f}) is below expected range (${expected_min}-${expected_max})")
            elif min_price > expected_max:
                content_parts.append(f"💸 Prices seem high. Lowest price (${min_price:.0f}) is above expected range (${expected_min}-${expected_max})")
        
        # Best value recommendation
        best_value = min(results, key=lambda x: float(x.get('price', float('inf'))))
        content_parts.append(f"🏆 Best price: ${best_value['price']} from {best_value['seller']}")
        
        return RAGInsight(
            query=query,
            insight_type="price_analysis",
            title="💰 Price Analysis",
            content="\n".join(content_parts),
            confidence_score=0.9,
            supporting_data={
                "price_stats": {
                    "min": min_price,
                    "max": max_price,
                    "avg": avg_price,
                    "variance": price_variance
                },
                "best_deal": best_value,
                "expected_range": expected_range
            }
        )
    
    def _generate_product_comparison(self, query: str, results: List[Dict[str, Any]], 
                                   enhanced_query: Optional[EnhancedQuery] = None) -> Optional[RAGInsight]:
        """Generate product comparison insight."""
        if len(results) < 2:
            return None
        
        # Group by seller
        sellers = {}
        for result in results:
            seller = result.get('seller', 'Unknown')
            if seller not in sellers:
                sellers[seller] = []
            sellers[seller].append(result)
        
        content_parts = [f"Found products from {len(sellers)} different sellers:"]
        
        # Analyze by seller
        for seller, seller_results in sellers.items():
            if len(seller_results) > 1:
                prices = [float(r['price']) for r in seller_results if r.get('price')]
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    content_parts.append(f"📱 {seller}: {len(seller_results)} options (${min_price:.0f} - ${max_price:.0f})")
            else:
                result = seller_results[0]
                content_parts.append(f"📱 {seller}: ${result.get('price', 'N/A')}")
        
        # Rating analysis
        rated_results = [r for r in results if r.get('rating')]
        if rated_results:
            avg_rating = sum(float(r['rating']) for r in rated_results) / len(rated_results)
            best_rated = max(rated_results, key=lambda x: float(x.get('rating', 0)))
            content_parts.append(f"⭐ Average rating: {avg_rating:.1f}/5")
            content_parts.append(f"🌟 Highest rated: {best_rated['rating']}/5 from {best_rated['seller']}")
        
        return RAGInsight(
            query=query,
            insight_type="product_comparison",
            title="📊 Product Comparison",
            content="\n".join(content_parts),
            confidence_score=0.8,
            supporting_data={
                "sellers": sellers,
                "seller_count": len(sellers),
                "total_options": len(results)
            }
        )
    
    def _generate_recommendations(self, query: str, results: List[Dict[str, Any]], 
                                enhanced_query: Optional[EnhancedQuery] = None) -> Optional[RAGInsight]:
        """Generate recommendation insight."""
        if not enhanced_query or not enhanced_query.suggested_alternatives:
            return None
        
        alternatives = enhanced_query.suggested_alternatives
        content_parts = [
            "🔍 You might also consider these alternatives:",
            ""
        ]
        
        for alt in alternatives[:3]:
            # Search for knowledge about the alternative
            alt_knowledge = self.knowledge_base.search_knowledge(alt, top_k=1)
            if alt_knowledge:
                metadata = alt_knowledge[0]["metadata"]
                if metadata.get("type") == "product_knowledge":
                    price_min = metadata.get("price_min", 0)
                    price_max = metadata.get("price_max", 0)
                    content_parts.append(f"• {alt} (${price_min} - ${price_max})")
            else:
                content_parts.append(f"• {alt}")
        
        # Add price context if available
        if enhanced_query.price_context:
            market_insights = enhanced_query.price_context.get("market_insights")
            if market_insights:
                content_parts.extend(["", "💡 Market Insights:", market_insights])
        
        return RAGInsight(
            query=query,
            insight_type="recommendation",
            title="🎯 Smart Recommendations",
            content="\n".join(content_parts),
            confidence_score=enhanced_query.confidence_score,
            supporting_data={
                "alternatives": alternatives,
                "price_context": enhanced_query.price_context
            }
        )
    
    def _generate_market_analysis(self, query: str, results: List[Dict[str, Any]], 
                                enhanced_query: Optional[EnhancedQuery] = None) -> Optional[RAGInsight]:
        """Generate market analysis insight."""
        if not enhanced_query or not enhanced_query.price_context:
            return None
        
        price_context = enhanced_query.price_context
        content_parts = []
        
        # Current market trend
        if price_context.get("trend"):
            trend = price_context["trend"]
            if trend == "decreasing":
                content_parts.append("📉 Prices are currently trending down - good time to buy!")
            elif trend == "increasing":
                content_parts.append("📈 Prices are trending up - consider buying soon")
            else:
                content_parts.append("📊 Prices are stable in the current market")
        
        # Best time to buy
        if price_context.get("best_time_to_buy"):
            content_parts.append(f"⏰ Best time to buy: {price_context['best_time_to_buy']}")
        
        # Market insights
        if price_context.get("market_insights"):
            content_parts.extend(["", "🧠 Market Intelligence:", price_context["market_insights"]])
        
        if not content_parts:
            return None
        
        return RAGInsight(
            query=query,
            insight_type="market_analysis",
            title="📈 Market Analysis",
            content="\n".join(content_parts),
            confidence_score=0.7,
            supporting_data=price_context
        )
    
    def learn_from_search(self, query: str, results: List[Dict[str, Any]], 
                         user_feedback: Optional[Dict[str, Any]] = None):
        """Learn from search results to improve future recommendations."""
        if not results:
            return
        
        # Extract product information from results
        for result in results:
            product_name = result.get('productName', '')
            price = result.get('price')
            seller = result.get('seller', '')
            
            if product_name and price:
                # Update price insights
                try:
                    price_float = float(price)
                    self._update_price_insights(product_name, price_float, seller)
                except (ValueError, TypeError):
                    continue
        
        # Save updated knowledge
        self.knowledge_base.save_knowledge_base()
    
    def _update_price_insights(self, product_name: str, price: float, seller: str):
        """Update price insights with new data."""
        product_id = product_name.replace(" ", "_").lower()
        
        # Get existing insights or create new
        insight = self.knowledge_base.get_price_insights(product_name)
        
        if insight:
            # Update existing insight
            insight.historical_prices.append({
                "date": datetime.now().isoformat(),
                "price": price,
                "source": seller
            })
            
            # Keep only last 30 price points
            insight.historical_prices = insight.historical_prices[-30:]
            
            # Update current price and trend
            insight.current_price = price
            insight.last_updated = datetime.now().isoformat()
            
            # Simple trend analysis
            if len(insight.historical_prices) >= 3:
                recent_prices = [p["price"] for p in insight.historical_prices[-3:]]
                if recent_prices[-1] > recent_prices[0]:
                    insight.price_trend = "increasing"
                elif recent_prices[-1] < recent_prices[0]:
                    insight.price_trend = "decreasing"
                else:
                    insight.price_trend = "stable"
        
        else:
            # Create new insight
            insight = PriceInsight(
                product_name=product_name,
                current_price=price,
                historical_prices=[{
                    "date": datetime.now().isoformat(),
                    "price": price,
                    "source": seller
                }],
                price_trend="stable",
                best_time_to_buy="Monitor for trends",
                price_prediction=None,
                market_analysis="Insufficient data for analysis"
            )
        
        # Add to knowledge base
        self.knowledge_base.add_price_insight(insight)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG engine statistics."""
        return {
            "knowledge_base_stats": self.knowledge_base.get_stats(),
            "engine_status": "active"
        }
