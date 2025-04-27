# Warframe Market API Client

A Python-based asynchronous client for tracking and analyzing Warframe Market data, with features for market analysis and price tracking.

## Features

- Asynchronous API client with rate limiting and automatic retries
- PostgreSQL database integration for storing market data
- Market analysis tools including:
  - Price trend analysis
  - Outlier detection
  - Market spread tracking
  - Price volatility calculation
- Historical order tracking and status management
- Automated warframe set identification and tracking

## Requirements

- Python 3.7+
- PostgreSQL database
- Dependencies listed in requirements.txt:
  - aiohttp
  - psycopg2
  - requests
  - python-dateutil
  - scipy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/WarframeMarketApi.git
cd WarframeMarketApi
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure database connection:
Configure your PostgreSQL connection details in `src/database/config.py`.

## Usage

Run the main application:

```bash
python src/main.py
```

The application will:
1. Fetch all items from Warframe Market
2. Identify and store warframe sets
3. Process market orders for all warframes
4. Analyze market trends and update order statuses

## Architecture

### Components

- **WarframeMarketClient** (`src/api/warframe_market_client.py`): Handles API communication with rate limiting
- **DatabaseOperations** (`src/database/operations.py`): Manages database operations and data persistence
- **MarketAnalysis** (`src/utils/market_analysis.py`): Provides market analysis tools and metrics
- **Data Models** (`src/models/`): Contains data structures and type definitions

### Database Schema

- `known_warframes`: Stores identified warframe sets
- `order_history`: Tracks order history and status
- `item_prices`: Records price points for market analysis
- `price_statistics`: Stores aggregated market statistics

## Features in Detail

### Market Analysis

- Price trend tracking over multiple time ranges
- Volatility calculation and outlier detection
- Market spread analysis
- Trading volume tracking
- Best buy/sell time identification
- Seasonal pattern detection

### Order Management

- Automatic order status updates
- Price change tracking
- Listing type identification (new vs. relist)
- Historical order archival
- Active order monitoring

### Rate Limiting

The API client implements rate limiting (2 requests per second) with:
- Request queuing
- Automatic retries on failure
- Connection pooling
- Session management

## Documentation

The project uses Sphinx for documentation. To build the documentation:

1. Ensure you have installed all requirements:
```bash
pip install -r requirements.txt
```

2. Navigate to the docs directory:
```bash
cd docs
```

3. Build the documentation:
- On Windows:
```bash
make.bat html
```
- On Linux/Mac:
```bash
make html
```

The built documentation will be available in `docs/build/html/index.html`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your chosen license here]

## Acknowledgments

- [Warframe Market](https://warframe.market/) for providing the API
- Digital Extremes for Warframe