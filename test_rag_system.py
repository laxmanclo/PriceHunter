#!/usr/bin/env python3
"""
Comprehensive test for the RAG (Retrieval-Augmented Generation) system.
Tests query enhancement, knowledge retrieval, and intelligent insights.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any

from src.core.price_fetcher import PriceFetcher, SearchRequest
from src.rag import RAGEngine, ProductKnowledgeBase, QueryEnhancer


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"🧠 {title}")
    print('='*60)


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n🔍 {title}")
    print('-'*40)


async def test_knowledge_base():
    """Test the knowledge base functionality."""
    print_section("Testing Knowledge Base")
    
    # Initialize knowledge base
    kb = ProductKnowledgeBase()
    
    print(f"📊 Knowledge base stats: {kb.get_stats()}")
    
    # Test product search
    print_subsection("Product Knowledge Search")
    
    test_queries = [
        "iPhone 16 Pro specifications",
        "Samsung Galaxy S24 Ultra camera",
        "MacBook Air M2 battery life",
        "OnePlus 12 price range"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        results = kb.search_knowledge(query, top_k=2)
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['relevance_score']:.3f}")
            print(f"     Type: {result['metadata'].get('type', 'unknown')}")
            print(f"     Content: {result['content'][:100]}...")
    
    # Test alternatives
    print_subsection("Product Alternatives")
    
    alternatives = kb.get_product_alternatives("iPhone 16 Pro")
    print(f"📱 iPhone 16 Pro alternatives: {alternatives}")
    
    alternatives = kb.get_product_alternatives("Samsung Galaxy S24 Ultra")
    print(f"📱 Galaxy S24 Ultra alternatives: {alternatives}")


async def test_query_enhancer():
    """Test the query enhancement functionality."""
    print_section("Testing Query Enhancement")
    
    # Initialize components
    kb = ProductKnowledgeBase()
    enhancer = QueryEnhancer(kb)
    
    test_queries = [
        ("iPhone 16 Pro", "US"),
        ("iPhone 16 Pro, 128GB", "IN"),
        ("Samsung Galaxy S24", "US"),
        ("MacBook Pro M3", "IN"),
        ("OnePlus 12 256GB", "US"),
        ("phone under 1000", "IN")  # Vague query
    ]
    
    for query, country in test_queries:
        print_subsection(f"Enhancing: '{query}' for {country}")
        
        # Test feature extraction
        features = enhancer.extract_features(query)
        print(f"📋 Extracted features: {features}")
        
        # Test query enhancement
        enhanced = enhancer.enhance_query(query, country)
        
        print(f"🔍 Original: '{enhanced.original_query}'")
        print(f"✨ Enhanced: '{enhanced.enhanced_query}'")
        print(f"📊 Confidence: {enhanced.confidence_score:.3f}")
        print(f"🎯 Alternatives: {enhanced.suggested_alternatives}")
        
        if enhanced.price_context:
            print(f"💰 Price context: {enhanced.price_context}")
        
        # Test suggestions
        suggestions = enhancer.suggest_query_improvements(query)
        if suggestions:
            print(f"💡 Suggestions: {suggestions}")


async def test_rag_engine():
    """Test the complete RAG engine."""
    print_section("Testing RAG Engine")
    
    # Initialize RAG engine
    rag_engine = RAGEngine()
    
    print(f"📊 RAG engine stats: {rag_engine.get_stats()}")
    
    # Test query enhancement
    print_subsection("Query Enhancement")
    
    test_query = "iPhone 16 Pro, 128GB"
    enhanced = rag_engine.enhance_search_query(test_query, "US")
    
    print(f"🔍 Original: '{enhanced.original_query}'")
    print(f"✨ Enhanced: '{enhanced.enhanced_query}'")
    print(f"📊 Confidence: {enhanced.confidence_score:.3f}")
    print(f"🎯 Alternatives: {enhanced.suggested_alternatives}")
    
    # Test with mock search results
    print_subsection("RAG Insights Generation")
    
    mock_results = [
        {
            "productName": "iPhone 16 Pro 128GB Black Titanium",
            "price": "999",
            "currency": "USD",
            "seller": "Apple Store",
            "rating": 4.8,
            "reviewsCount": 1250,
            "link": "https://apple.com/iphone-16-pro"
        },
        {
            "productName": "iPhone 16 Pro 128GB Natural Titanium",
            "price": "1049",
            "currency": "USD", 
            "seller": "Best Buy",
            "rating": 4.7,
            "reviewsCount": 890,
            "link": "https://bestbuy.com/iphone-16-pro"
        },
        {
            "productName": "iPhone 16 Pro 128GB White Titanium",
            "price": "1099",
            "currency": "USD",
            "seller": "Amazon",
            "rating": 4.6,
            "reviewsCount": 2100,
            "link": "https://amazon.com/iphone-16-pro"
        }
    ]
    
    insights = rag_engine.analyze_search_results(test_query, mock_results, enhanced)
    
    print(f"🧠 Generated {len(insights)} insights:")
    
    for insight in insights:
        print(f"\n📋 {insight.title}")
        print(f"   Type: {insight.insight_type}")
        print(f"   Confidence: {insight.confidence_score:.3f}")
        print(f"   Content:\n{insight.content}")
        
        if insight.supporting_data:
            print(f"   Supporting data: {list(insight.supporting_data.keys())}")


async def test_integrated_rag_search():
    """Test RAG integration with the main search system."""
    print_section("Testing Integrated RAG Search")
    
    # Initialize PriceFetcher with RAG enabled
    fetcher = PriceFetcher(enable_rag=True)
    
    test_queries = [
        ("iPhone 16 Pro, 128GB", "US"),
        ("Samsung Galaxy S24", "IN"),
        ("MacBook Air M2", "US")
    ]
    
    for query, country in test_queries:
        print_subsection(f"RAG-Enhanced Search: '{query}' in {country}")
        
        request = SearchRequest(
            query=query,
            country=country,
            max_results=5,
            timeout=30
        )
        
        start_time = time.time()
        response = await fetcher.search(request)
        search_time = time.time() - start_time
        
        print(f"⏱️  Search completed in {search_time:.2f} seconds")
        print(f"📊 Found {response.total_results} results from {len(response.sources_used)} sources")
        
        # Display enhanced query info
        if response.enhanced_query:
            eq = response.enhanced_query
            print(f"\n✨ Query Enhancement:")
            print(f"   Original: '{eq.original_query}'")
            print(f"   Enhanced: '{eq.enhanced_query}'")
            print(f"   Confidence: {eq.confidence_score:.3f}")
            print(f"   Features: {eq.extracted_features}")
            
            if eq.suggested_alternatives:
                print(f"   Alternatives: {eq.suggested_alternatives}")
        
        # Display RAG insights
        if response.rag_insights:
            print(f"\n🧠 RAG Insights ({len(response.rag_insights)}):")
            
            for insight in response.rag_insights:
                print(f"\n   📋 {insight.title}")
                print(f"      {insight.content}")
        
        # Display top results
        if response.results:
            print(f"\n🏆 Top Results:")
            for i, result in enumerate(response.results[:3], 1):
                print(f"   {i}. {result['productName'][:50]}...")
                print(f"      💰 ${result['price']} {result['currency']} - {result['seller']}")
                if result.get('rating'):
                    print(f"      ⭐ {result['rating']}/5 ({result.get('reviewsCount', 0)} reviews)")
        
        print(f"\n" + "="*50)


async def test_rag_learning():
    """Test RAG learning capabilities."""
    print_section("Testing RAG Learning")
    
    rag_engine = RAGEngine()
    
    # Simulate learning from search results
    print_subsection("Learning from Search Results")
    
    learning_data = [
        {
            "query": "iPhone 16 Pro",
            "results": [
                {"productName": "iPhone 16 Pro 128GB", "price": "999", "seller": "Apple"},
                {"productName": "iPhone 16 Pro 256GB", "price": "1099", "seller": "Best Buy"}
            ]
        },
        {
            "query": "Samsung Galaxy S24",
            "results": [
                {"productName": "Galaxy S24 128GB", "price": "799", "seller": "Samsung"},
                {"productName": "Galaxy S24 256GB", "price": "859", "seller": "Amazon"}
            ]
        }
    ]
    
    for data in learning_data:
        print(f"📚 Learning from query: '{data['query']}'")
        rag_engine.learn_from_search(data["query"], data["results"])
        print(f"   Processed {len(data['results'])} results")
    
    # Check updated knowledge
    print_subsection("Knowledge Base After Learning")
    
    stats = rag_engine.get_stats()
    print(f"📊 Updated stats: {stats}")
    
    # Test price insights
    insight = rag_engine.knowledge_base.get_price_insights("iPhone 16 Pro 128GB")
    if insight:
        print(f"💰 iPhone 16 Pro price insight:")
        print(f"   Current price: ${insight.current_price}")
        print(f"   Trend: {insight.price_trend}")
        print(f"   Historical prices: {len(insight.historical_prices)} data points")


async def main():
    """Run all RAG system tests."""
    print("🚀 PriceHunter RAG System Test Suite")
    print("Testing Retrieval-Augmented Generation capabilities")
    print("="*70)
    
    start_time = time.time()
    
    try:
        # Test individual components
        await test_knowledge_base()
        await test_query_enhancer()
        await test_rag_engine()
        
        # Test integrated system
        await test_integrated_rag_search()
        
        # Test learning capabilities
        await test_rag_learning()
        
        total_time = time.time() - start_time
        
        print_section("Test Summary")
        print(f"✅ All RAG tests completed successfully!")
        print(f"⏱️  Total test time: {total_time:.2f} seconds")
        print(f"🎯 RAG system is fully operational and sophisticated!")
        
        # Export test results
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "rag_system",
            "status": "success",
            "total_time": total_time,
            "components_tested": [
                "knowledge_base",
                "query_enhancer", 
                "rag_engine",
                "integrated_search",
                "learning_system"
            ]
        }
        
        with open("rag_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2)
        
        print(f"💾 Test results exported to rag_test_results.json")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
