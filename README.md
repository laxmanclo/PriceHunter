# 🔥 PriceHunter - Smart Price Comparison Tool

yo this thing is actually insane for finding the best deals online. built this to stop getting ripped off when shopping lol

## ✨ what it does

- scrapes prices from literally everywhere (amazon, flipkart, best buy, etc.)
- works in different countries (US, India, more coming)
- has AI that makes your searches way smarter
- finds alternatives you didn't even think of
- tells you if you're getting a good deal or not
- learns from searches to get better over time
- super fast with caching and async stuff

## 🧠 the cool AI stuff (RAG system)

this is where it gets interesting - built a whole knowledge base that:
- knows about different products and their specs
- remembers price trends and market data
- enhances your search queries automatically
- gives you smart insights about deals
- learns from every search to get smarter

basically it's like having a shopping expert that never sleeps

## 🏗️ how it's built

```
src/
├── core/           # main engine stuff
├── scrapers/       # all the website scrapers
├── rag/           # the AI brain (rag)
│   ├── vector_store.py      # stores product knowledge
│   ├── knowledge_base.py    # product database
│   ├── query_enhancer.py    # makes searches smarter
│   └── rag_engine.py        # puts it all together
├── utils/          # helper functions
└── api/           # ways to use it
```

## 🚀 how to use this thing

### quickest demo (see the AI in action)

```bash
# get the code
git clone <your-repo>
cd PriceHunter

# install the basics (just need these for demo)
pip install sentence-transformers faiss-cpu loguru

# run the demo - shows off all the AI features
python demo.py
```

### full setup

```bash
# install everything
pip install -r requirements.txt

# test the RAG system (comprehensive tests)
python test_rag_system.py

# or test with real scraping (careful - might get blocked)
python test_real_scrapers.py
```

### simple search example

```python
from src.core.price_fetcher import PriceFetcher, SearchRequest

# create the fetcher (with AI enabled)
fetcher = PriceFetcher(enable_rag=True)

# search for something
request = SearchRequest(
    query="iPhone 16 Pro, 128GB",
    country="US"
)

results = await fetcher.search(request)

# check out the AI insights
for insight in results.rag_insights:
    print(f"{insight.title}: {insight.content}")
```

## 📊 what you get back

the AI doesn't just give you prices - it gives you insights:

```
💰 Price Analysis
Found 5 results with prices ranging from $999 to $1199.
Average price: $1049
💰 Great deal! Lowest price ($999) is below expected range ($1050-$1200)
🏆 Best price: $999 from Apple Store

🎯 Smart Recommendations
You might also consider these alternatives:
• iPhone 15 Pro ($799 - $999)
• Samsung Galaxy S24 Ultra ($899 - $1199)
• Google Pixel 8 Pro ($699 - $999)

📈 Market Analysis
📉 Prices are currently trending down - good time to buy!
⏰ Best time to buy: Holiday season (November-December)
```

plus the actual product results with prices, ratings, links etc.

## 🌍 where it works

- **US**: amazon, best buy, walmart, target, apple store
- **India**: flipkart, amazon.in (works really well here)
- more countries coming when i get time

## 🧪 testing it out

```bash
# test the AI system
python test_rag_system.py

# test real scraping (careful - might get rate limited)
python test_real_scrapers.py

# run the basic tests
pytest tests/ -v
```

## ⚡ performance stuff

- caches results so it's fast on repeat searches
- runs scrapers in parallel (async ftw)
- smart rate limiting so sites don't block you
- learns from searches to get better over time

## 🔧 technical details (for the nerds)

**RAG System:**
- uses sentence-transformers for embeddings
- FAISS for vector similarity search
- learns product knowledge and price patterns
- enhances queries with context

**Scraping:**
- multiple fallback CSS selectors
- anti-bot detection evasion
- handles different currencies and formats
- fuzzy matching for product names

**Architecture:**
- async/await everywhere for speed
- modular scraper system
- comprehensive error handling
- extensive logging for debugging

sooo 
**RAG Implementation**: built a complete retrieval-augmented generation system from scratch
- vector embeddings with sentence-transformers
- FAISS for similarity search
- knowledge base that learns and grows
- query enhancement that makes searches smarter

**Real-world Problem**: price comparison is actually useful (not just another todo app)
- handles multiple countries and currencies
- deals with anti-bot protection
- processes messy real-world data
- provides actionable insights

**System Design**: shows understanding of complex architectures
- async/await for performance
- modular scraper system
- caching and optimization
- comprehensive error handling
- extensive testing

**AI Integration**: demonstrates modern AI concepts
- embeddings and vector search
- learning from user interactions
- context-aware recommendations
- intelligent query processing


## 📝 notes

- some scrapers might get blocked occasionally (that's just how it is)
- the AI gets smarter the more you use it
- works best for popular products (phones, laptops, etc.)
- built this for learning but it actually works pretty well

feel free to contribute or just use it to save money 💸