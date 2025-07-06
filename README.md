# 🚀 PriceHunter - The Ultimate Price Comparison Tool

The most sophisticated and intelligent price comparison tool that fetches the best prices from multiple sources worldwide.

## 🌟 Features

- **Multi-Source Scraping**: Amazon, eBay, Best Buy, Walmart, Target, Apple Store, and more
- **Regional Intelligence**: Country-specific retailers (e.g., Sangeetha Mobiles for India)
- **API Integrations**: Google Shopping, PriceAPI for additional coverage
- **ML-Powered Matching**: Intelligent product matching using NLP and fuzzy matching
- **Anti-Detection**: Rotating proxies, user agents, CAPTCHA handling
- **Performance Optimized**: Redis caching, async processing
- **Docker Ready**: Fully containerized for easy deployment

## 🏗️ Architecture

```
PriceHunter/
├── src/
│   ├── core/
│   │   ├── price_fetcher.py      # Main engine
│   │   ├── base_scraper.py       # Abstract scraper base
│   │   └── result_processor.py   # Result normalization
│   ├── scrapers/
│   │   ├── ecommerce/           # Major e-commerce sites
│   │   ├── regional/            # Country-specific sites
│   │   └── apis/                # API integrations
│   ├── utils/
│   │   ├── product_matcher.py   # ML product matching
│   │   ├── anti_detection.py    # Proxy/UA rotation
│   │   └── cache.py             # Redis caching
│   └── api/
│       ├── cli.py               # Command line interface
│       └── rest_api.py          # REST API endpoints
├── tests/
├── docker/
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd PriceHunter

# Build and run with Docker Compose
docker-compose up --build

# Test with the example query
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"country": "US", "query": "iPhone 16 Pro, 128GB"}'
```

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (required for caching)
redis-server

# Run the CLI
python src/api/cli.py --country US --query "iPhone 16 Pro, 128GB"

# Or start the API server
python src/api/rest_api.py
```

## 📊 Example Output

```json
[
  {
    "link": "https://apple.com/iphone-16-pro",
    "price": "999",
    "currency": "USD",
    "productName": "Apple iPhone 16 Pro 128GB"
  },
  {
    "link": "https://amazon.com/dp/B0XXXXXXXX",
    "price": "1049",
    "currency": "USD",
    "productName": "Apple iPhone 16 Pro 128GB Natural Titanium"
  }
]
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_price_fetcher.py

# Test with coverage
pytest --cov=src tests/
```

## 🌍 Supported Countries & Regions

- **US**: Amazon, eBay, Best Buy, Walmart, Target, Apple Store
- **India**: Amazon.in, Flipkart, Sangeetha Mobiles, Croma
- **UK**: Amazon.co.uk, Currys, Argos, John Lewis
- **More regions coming soon...**

## 🔧 Configuration

Environment variables can be set in `.env` file:

```env
REDIS_URL=redis://localhost:6379
PROXY_ENABLED=true
RATE_LIMIT_DELAY=2
MAX_CONCURRENT_REQUESTS=10
```

## 📈 Performance

- **Caching**: Results cached for 1 hour to improve response times
- **Async Processing**: Concurrent scraping for faster results
- **Rate Limiting**: Intelligent delays to avoid being blocked
- **Proxy Rotation**: Multiple proxy sources for reliability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details