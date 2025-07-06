"""
Knowledge base for product information and price insights.
Manages product specifications, reviews, and historical data.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from .vector_store import VectorStore, Document


@dataclass
class ProductKnowledge:
    """Product knowledge entry."""
    product_name: str
    category: str
    brand: str
    specifications: Dict[str, Any]
    features: List[str]
    price_range: Dict[str, float]  # min, max, avg
    alternatives: List[str]
    reviews_summary: str
    market_insights: str
    last_updated: str = ""
    
    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


@dataclass
class PriceInsight:
    """Price insight entry."""
    product_name: str
    current_price: float
    historical_prices: List[Dict[str, Any]]  # [{"date": "", "price": float, "source": ""}]
    price_trend: str  # "increasing", "decreasing", "stable"
    best_time_to_buy: str
    price_prediction: Optional[float]
    market_analysis: str
    last_updated: str = ""
    
    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


class ProductKnowledgeBase:
    """Knowledge base for product information and insights."""
    
    def __init__(self, data_path: str = "data/knowledge_base"):
        """Initialize knowledge base."""
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize vector store
        self.vector_store = VectorStore(index_path=str(self.data_path / "vectors"))
        
        # Load existing knowledge
        self.product_knowledge: Dict[str, ProductKnowledge] = {}
        self.price_insights: Dict[str, PriceInsight] = {}
        
        self._load_knowledge_base()
        self._populate_initial_knowledge()
        
        logger.info(f"Knowledge base initialized with {len(self.product_knowledge)} products")
    
    def _load_knowledge_base(self):
        """Load existing knowledge base from disk."""
        try:
            # Load product knowledge
            products_path = self.data_path / "products.json"
            if products_path.exists():
                with open(products_path, 'r') as f:
                    products_data = json.load(f)
                    for product_id, data in products_data.items():
                        self.product_knowledge[product_id] = ProductKnowledge(**data)
            
            # Load price insights
            insights_path = self.data_path / "price_insights.json"
            if insights_path.exists():
                with open(insights_path, 'r') as f:
                    insights_data = json.load(f)
                    for product_id, data in insights_data.items():
                        self.price_insights[product_id] = PriceInsight(**data)
                        
        except Exception as e:
            logger.warning(f"Could not load existing knowledge base: {e}")
    
    def _populate_initial_knowledge(self):
        """Populate initial product knowledge if empty."""
        if len(self.product_knowledge) > 0:
            return
        
        logger.info("Populating initial product knowledge...")
        
        # iPhone knowledge
        iphone_knowledge = [
            {
                "product_name": "iPhone 16 Pro",
                "category": "smartphone",
                "brand": "Apple",
                "specifications": {
                    "storage_options": ["128GB", "256GB", "512GB", "1TB"],
                    "colors": ["Black Titanium", "White Titanium", "Natural Titanium", "Desert Titanium"],
                    "display": "6.3-inch Super Retina XDR",
                    "chip": "A18 Pro",
                    "camera": "48MP Main, 48MP Ultra Wide, 12MP Telephoto",
                    "battery": "Up to 27 hours video playback"
                },
                "features": [
                    "Camera Control button",
                    "Action Button",
                    "Dynamic Island",
                    "Face ID",
                    "5G connectivity",
                    "MagSafe compatible",
                    "Water resistant IP68"
                ],
                "price_range": {"min": 999, "max": 1599, "avg": 1200},
                "alternatives": ["iPhone 16", "iPhone 15 Pro", "Samsung Galaxy S24 Ultra", "Google Pixel 9 Pro"],
                "reviews_summary": "Excellent camera system with new Camera Control. Great performance with A18 Pro chip. Premium build quality with titanium design.",
                "market_insights": "High demand product. Prices typically stable for first 6 months, then gradual decrease. Best deals during Black Friday and carrier promotions."
            },
            {
                "product_name": "iPhone 16",
                "category": "smartphone", 
                "brand": "Apple",
                "specifications": {
                    "storage_options": ["128GB", "256GB", "512GB"],
                    "colors": ["Black", "White", "Pink", "Teal", "Ultramarine"],
                    "display": "6.1-inch Super Retina XDR",
                    "chip": "A18",
                    "camera": "48MP Main, 12MP Ultra Wide",
                    "battery": "Up to 22 hours video playback"
                },
                "features": [
                    "Camera Control button",
                    "Action Button", 
                    "Dynamic Island",
                    "Face ID",
                    "5G connectivity",
                    "MagSafe compatible"
                ],
                "price_range": {"min": 799, "max": 1099, "avg": 900},
                "alternatives": ["iPhone 15", "iPhone 16 Plus", "Samsung Galaxy S24", "Google Pixel 9"],
                "reviews_summary": "Great value iPhone with new Camera Control. Solid performance with A18 chip. Good camera system for the price.",
                "market_insights": "Popular mid-range option. More price flexibility than Pro models. Good trade-in values."
            }
        ]
        
        # Android knowledge
        android_knowledge = [
            {
                "product_name": "Samsung Galaxy S24 Ultra",
                "category": "smartphone",
                "brand": "Samsung", 
                "specifications": {
                    "storage_options": ["256GB", "512GB", "1TB"],
                    "colors": ["Titanium Black", "Titanium Gray", "Titanium Violet", "Titanium Yellow"],
                    "display": "6.8-inch Dynamic AMOLED 2X",
                    "chip": "Snapdragon 8 Gen 3",
                    "camera": "200MP Main, 50MP Periscope, 10MP Telephoto, 12MP Ultra Wide",
                    "battery": "5000mAh"
                },
                "features": [
                    "S Pen included",
                    "AI photo editing",
                    "100x Space Zoom",
                    "IP68 water resistance",
                    "Wireless charging",
                    "Samsung DeX"
                ],
                "price_range": {"min": 1199, "max": 1659, "avg": 1400},
                "alternatives": ["iPhone 16 Pro Max", "Google Pixel 9 Pro XL", "OnePlus 12"],
                "reviews_summary": "Excellent camera zoom capabilities. Great for productivity with S Pen. Premium build and display quality.",
                "market_insights": "Samsung phones depreciate faster than iPhones. Best deals 3-6 months after launch. Strong trade-in programs."
            },
            {
                "product_name": "OnePlus 12",
                "category": "smartphone",
                "brand": "OnePlus",
                "specifications": {
                    "storage_options": ["256GB", "512GB"],
                    "colors": ["Silky Black", "Flowy Emerald"],
                    "display": "6.82-inch LTPO AMOLED",
                    "chip": "Snapdragon 8 Gen 3",
                    "camera": "50MP Main, 64MP Periscope, 48MP Ultra Wide",
                    "battery": "5400mAh"
                },
                "features": [
                    "100W fast charging",
                    "50W wireless charging",
                    "Alert Slider",
                    "IP65 water resistance",
                    "OxygenOS",
                    "Gaming mode"
                ],
                "price_range": {"min": 699, "max": 899, "avg": 799},
                "alternatives": ["Samsung Galaxy S24", "iPhone 16", "Google Pixel 9"],
                "reviews_summary": "Excellent value flagship. Very fast charging. Clean software experience. Good camera performance.",
                "market_insights": "Great price-to-performance ratio. Limited availability in some markets. Prices drop quickly after 6 months."
            }
        ]
        
        # Laptop knowledge
        laptop_knowledge = [
            {
                "product_name": "MacBook Air M2",
                "category": "laptop",
                "brand": "Apple",
                "specifications": {
                    "storage_options": ["256GB", "512GB", "1TB", "2TB"],
                    "memory_options": ["8GB", "16GB", "24GB"],
                    "colors": ["Space Gray", "Silver", "Starlight", "Midnight"],
                    "display": "13.6-inch Liquid Retina",
                    "chip": "Apple M2",
                    "battery": "Up to 18 hours"
                },
                "features": [
                    "Fanless design",
                    "MagSafe charging",
                    "Touch ID",
                    "1080p FaceTime HD camera",
                    "Four-speaker sound system",
                    "macOS"
                ],
                "price_range": {"min": 999, "max": 2499, "avg": 1400},
                "alternatives": ["MacBook Pro 14-inch", "Dell XPS 13", "Surface Laptop 5"],
                "reviews_summary": "Excellent battery life and performance. Great for everyday tasks. Silent operation. Premium build quality.",
                "market_insights": "Strong resale value. Educational discounts available. Best deals during back-to-school season."
            }
        ]
        
        # Add all knowledge to the system
        all_knowledge = iphone_knowledge + android_knowledge + laptop_knowledge
        
        for knowledge in all_knowledge:
            self.add_product_knowledge(ProductKnowledge(**knowledge))
        
        logger.info(f"Added {len(all_knowledge)} initial product knowledge entries")
    
    def add_product_knowledge(self, knowledge: ProductKnowledge) -> str:
        """Add product knowledge to the knowledge base."""
        product_id = f"{knowledge.brand}_{knowledge.product_name}".replace(" ", "_").lower()
        
        # Store in memory
        self.product_knowledge[product_id] = knowledge
        
        # Create searchable content for vector store
        content = f"""
        Product: {knowledge.product_name}
        Brand: {knowledge.brand}
        Category: {knowledge.category}
        
        Specifications: {json.dumps(knowledge.specifications, indent=2)}
        
        Features: {', '.join(knowledge.features)}
        
        Price Range: ${knowledge.price_range['min']} - ${knowledge.price_range['max']} (avg: ${knowledge.price_range['avg']})
        
        Alternatives: {', '.join(knowledge.alternatives)}
        
        Reviews Summary: {knowledge.reviews_summary}
        
        Market Insights: {knowledge.market_insights}
        """.strip()
        
        metadata = {
            "type": "product_knowledge",
            "product_id": product_id,
            "brand": knowledge.brand,
            "category": knowledge.category,
            "price_min": knowledge.price_range['min'],
            "price_max": knowledge.price_range['max']
        }
        
        # Add to vector store
        self.vector_store.add_document(content, metadata)
        
        return product_id
    
    def add_price_insight(self, insight: PriceInsight) -> str:
        """Add price insight to the knowledge base."""
        product_id = insight.product_name.replace(" ", "_").lower()
        
        # Store in memory
        self.price_insights[product_id] = insight
        
        # Create searchable content for vector store
        content = f"""
        Price Analysis for: {insight.product_name}
        Current Price: ${insight.current_price}
        Price Trend: {insight.price_trend}
        Best Time to Buy: {insight.best_time_to_buy}
        
        Historical Prices: {json.dumps(insight.historical_prices, indent=2)}
        
        Market Analysis: {insight.market_analysis}
        
        Price Prediction: ${insight.price_prediction if insight.price_prediction else 'N/A'}
        """.strip()
        
        metadata = {
            "type": "price_insight",
            "product_id": product_id,
            "current_price": insight.current_price,
            "trend": insight.price_trend
        }
        
        # Add to vector store
        self.vector_store.add_document(content, metadata)
        
        return product_id
    
    def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant information."""
        results = self.vector_store.search(query, top_k=top_k)
        
        formatted_results = []
        for doc, score in results:
            result = {
                "content": doc.content,
                "metadata": doc.metadata,
                "relevance_score": score,
                "document_id": doc.id
            }
            formatted_results.append(result)
        
        return formatted_results
    
    def get_product_alternatives(self, product_name: str) -> List[str]:
        """Get alternative products for a given product."""
        # Search for the product in knowledge base
        results = self.search_knowledge(product_name, top_k=1)
        
        if results and results[0]["metadata"].get("type") == "product_knowledge":
            product_id = results[0]["metadata"]["product_id"]
            if product_id in self.product_knowledge:
                return self.product_knowledge[product_id].alternatives
        
        return []
    
    def get_price_insights(self, product_name: str) -> Optional[PriceInsight]:
        """Get price insights for a product."""
        product_id = product_name.replace(" ", "_").lower()
        return self.price_insights.get(product_id)
    
    def save_knowledge_base(self):
        """Save knowledge base to disk."""
        try:
            # Save product knowledge
            products_data = {}
            for product_id, knowledge in self.product_knowledge.items():
                products_data[product_id] = asdict(knowledge)
            
            with open(self.data_path / "products.json", 'w') as f:
                json.dump(products_data, f, indent=2)
            
            # Save price insights
            insights_data = {}
            for product_id, insight in self.price_insights.items():
                insights_data[product_id] = asdict(insight)
            
            with open(self.data_path / "price_insights.json", 'w') as f:
                json.dump(insights_data, f, indent=2)
            
            # Save vector store
            self.vector_store.save_index()
            
            logger.info("Knowledge base saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            "product_knowledge_count": len(self.product_knowledge),
            "price_insights_count": len(self.price_insights),
            "vector_store_stats": self.vector_store.get_stats()
        }
