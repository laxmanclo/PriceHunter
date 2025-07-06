#!/usr/bin/env python3
"""
Quick demo of PriceHunter's RAG capabilities.
Shows off the AI features without needing to scrape real sites.
"""

import asyncio
import json
from datetime import datetime

from src.rag import RAGEngine, ProductKnowledgeBase, QueryEnhancer


def print_header(text):
    print(f"\n{'='*50}")
    print(f"🔥 {text}")
    print('='*50)


def print_subheader(text):
    print(f"\n💡 {text}")
    print('-'*30)


async def demo_query_enhancement():
    """Demo the query enhancement features."""
    print_header("Query Enhancement Demo")
    
    kb = ProductKnowledgeBase()
    enhancer = QueryEnhancer(kb)
    
    test_queries = [
        "iPhone 16 Pro",
        "Samsung Galaxy",
        "MacBook",
        "phone under 1000"
    ]
    
    for query in test_queries:
        print_subheader(f"Enhancing: '{query}'")
        
        enhanced = enhancer.enhance_query(query, "US")
        
        print(f"📝 Original: '{enhanced.original_query}'")
        print(f"✨ Enhanced: '{enhanced.enhanced_query}'")
        print(f"📊 Confidence: {enhanced.confidence_score:.2f}")
        
        if enhanced.extracted_features:
            print(f"🔍 Features found: {enhanced.extracted_features}")
        
        if enhanced.suggested_alternatives:
            print(f"🎯 Alternatives: {enhanced.suggested_alternatives[:3]}")
        
        if enhanced.price_context:
            price_range = enhanced.price_context.get('expected_range', {})
            if price_range:
                print(f"💰 Expected price: ${price_range.get('min', 0)} - ${price_range.get('max', 0)}")


async def demo_rag_insights():
    """Demo the RAG insights generation."""
    print_header("RAG Insights Demo")
    
    rag_engine = RAGEngine()
    
    # Mock some search results
    mock_results = [
        {
            "productName": "iPhone 16 Pro 128GB Black Titanium",
            "price": "999",
            "currency": "USD",
            "seller": "Apple Store",
            "rating": 4.8,
            "reviewsCount": 1250
        },
        {
            "productName": "iPhone 16 Pro 128GB Natural Titanium", 
            "price": "1049",
            "currency": "USD",
            "seller": "Best Buy",
            "rating": 4.7,
            "reviewsCount": 890
        },
        {
            "productName": "iPhone 16 Pro 128GB White Titanium",
            "price": "1199",
            "currency": "USD", 
            "seller": "Amazon",
            "rating": 4.6,
            "reviewsCount": 2100
        }
    ]
    
    query = "iPhone 16 Pro, 128GB"
    enhanced_query = rag_engine.enhance_search_query(query, "US")
    
    print_subheader("Search Results Analysis")
    print(f"🔍 Query: '{query}'")
    print(f"📊 Found {len(mock_results)} results")
    
    # Generate insights
    insights = rag_engine.analyze_search_results(query, mock_results, enhanced_query)
    
    print_subheader("AI-Generated Insights")
    
    for insight in insights:
        print(f"\n📋 {insight.title}")
        print(f"   {insight.content}")
        print(f"   Confidence: {insight.confidence_score:.2f}")


async def demo_knowledge_search():
    """Demo the knowledge base search."""
    print_header("Knowledge Base Demo")
    
    kb = ProductKnowledgeBase()
    
    print(f"📊 Knowledge base contains: {kb.get_stats()}")
    
    search_queries = [
        "iPhone camera features",
        "Samsung Galaxy display",
        "MacBook battery life",
        "OnePlus charging speed"
    ]
    
    for query in search_queries:
        print_subheader(f"Searching: '{query}'")
        
        results = kb.search_knowledge(query, top_k=2)
        
        for i, result in enumerate(results, 1):
            print(f"   {i}. Score: {result['relevance_score']:.3f}")
            print(f"      {result['content'][:100]}...")


async def demo_price_insights():
    """Demo price insights and learning."""
    print_header("Price Learning Demo")
    
    rag_engine = RAGEngine()
    
    # Simulate learning from searches
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
    
    print_subheader("Learning from Search Data")
    
    for data in learning_data:
        print(f"📚 Processing: '{data['query']}'")
        rag_engine.learn_from_search(data["query"], data["results"])
        print(f"   Learned from {len(data['results'])} price points")
    
    print_subheader("Price Insights Generated")
    
    # Check what was learned
    insight = rag_engine.knowledge_base.get_price_insights("iPhone 16 Pro 128GB")
    if insight:
        print(f"💰 iPhone 16 Pro insights:")
        print(f"   Current price: ${insight.current_price}")
        print(f"   Price trend: {insight.price_trend}")
        print(f"   Data points: {len(insight.historical_prices)}")


async def demo_complete_workflow():
    """Demo the complete RAG workflow."""
    print_header("Complete RAG Workflow Demo")
    
    rag_engine = RAGEngine()
    
    # Step 1: Query enhancement
    original_query = "iPhone"
    enhanced = rag_engine.enhance_search_query(original_query, "US")
    
    print_subheader("Step 1: Query Enhancement")
    print(f"📝 '{original_query}' → '{enhanced.enhanced_query}'")
    print(f"🎯 Suggested alternatives: {enhanced.suggested_alternatives[:2]}")
    
    # Step 2: Mock search results
    mock_results = [
        {"productName": "iPhone 16 Pro 128GB", "price": "999", "seller": "Apple", "rating": 4.8},
        {"productName": "iPhone 15 Pro 128GB", "price": "799", "seller": "Best Buy", "rating": 4.7},
        {"productName": "iPhone 16 128GB", "price": "699", "seller": "Amazon", "rating": 4.6}
    ]
    
    print_subheader("Step 2: Search Results")
    for result in mock_results:
        print(f"   📱 {result['productName']} - ${result['price']} ({result['seller']})")
    
    # Step 3: Generate insights
    insights = rag_engine.analyze_search_results(original_query, mock_results, enhanced)
    
    print_subheader("Step 3: AI Insights")
    for insight in insights:
        print(f"\n{insight.title}")
        lines = insight.content.split('\n')
        for line in lines[:3]:  # Show first 3 lines
            if line.strip():
                print(f"   {line}")
    
    # Step 4: Learning
    rag_engine.learn_from_search(original_query, mock_results)
    
    print_subheader("Step 4: Learning Complete")
    print("🧠 RAG system updated with new price data")
    print("📈 Future searches will be even smarter!")


async def main():
    """Run the complete demo."""
    print("🚀 PriceHunter RAG System Demo")
    print("Showcasing AI-powered price comparison features")
    
    try:
        await demo_query_enhancement()
        await demo_knowledge_search() 
        await demo_rag_insights()
        await demo_price_insights()
        await demo_complete_workflow()
        
        print_header("Demo Complete!")
        print("🎉 RAG system is working perfectly!")
        print("💡 Try running 'python test_rag_system.py' for full tests")
        print("🔍 Or 'python test_real_scrapers.py' for real scraping")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
