# Schwab Market Data API Client

A robust Python client for fetching historical market data from the Schwab Market Data API with optimal period chunking and comprehensive data quality validation.

## 🚀 Features

- **Optimal Period Chunking**: Intelligently fetches data in decreasing chunks (10→5→4→3→2→1 days) to maximize API efficiency
- **Comprehensive Data Validation**: Built-in quality checks for duplicates, null values, negative prices, and timestamp ordering
- **Market Hours Filtering**: Automatically filters data to regular market hours (9:30 AM - 4:00 PM ET)
- **Special Holiday Handling**: Supports early market closures (July 3rd, Black Friday, December 24th, etc.)
- **Professional Logging**: Structured logging with timestamps and log levels
- **Type Safety**: Full type hints for better IDE support and code clarity
- **Modular Architecture**: Clean, maintainable object-oriented design
- **Rate Limiting**: Built-in rate limiting to respect API constraints

## 📋 Requirements

- Python 3.8+
- Schwab API access token
- Internet connection

## 🛠️ Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd schwab-market-data-api
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Create .env file
   cp .env.example .env  # if .env.example exists
   # OR create manually:
   echo "SCHWAB_ACCESS_TOKEN=your_access_token_here" > .env
   ```

## 🔧 Configuration

### Environment Setup

1. **Create a `.env` file** in the project root:

   ```bash
   touch .env
   ```

2. **Add your Schwab API access token** to the `.env` file:

   ```env
   SCHWAB_ACCESS_TOKEN=your_access_token_here
   ```

   **⚠️ Important**: Never commit your `.env` file to version control. It's already included in `.gitignore`.

### Getting Your Schwab API Access Token

To use this client, you'll need a Schwab API access token:

1. **Register for Schwab Developer Account**: Visit the [Schwab Developer Portal](https://developer.schwab.com/)
2. **Create an Application**: Set up a new application in your developer dashboard
3. **Generate Access Token**: Follow Schwab's OAuth flow to obtain your access token
4. **Add to .env File**: Place your token in the `.env` file as shown above

**Note**: The access token has expiration times and usage limits. Refer to Schwab's API documentation for current limits and renewal procedures.

3. **Install dependencies** (python-dotenv is already included in requirements.txt):

   ```bash
   pip install -r requirements.txt
   ```

### API Configuration

The client automatically reads the access token from the `.env` file. The `APIConfig` class in `schwab_market_data_client.py` is configured to use environment variables:

```python
@dataclass
class APIConfig:
    server: str = "https://api.schwabapi.com/marketdata/v1"
    access_token: str = os.getenv("SCHWAB_ACCESS_TOKEN") or ""
    timeout: int = 30
    rate_limit_delay: float = 1.0
```

**Note**: If you prefer to hardcode the token (not recommended for security), you can modify the `access_token` line to:

```python
access_token: str = "YOUR_ACCESS_TOKEN_HERE"  # Replace with your token
```

### Market Configuration

Customize market settings in the `MarketConfig` class:

```python
@dataclass
class MarketConfig:
    timezone: str = 'America/New_York'
    market_open: str = '09:30:00'
    market_close: str = '16:00:00'
    early_close: str = '13:00:00'  # Early closure times (July 3rd, Black Friday, December 24th)
```

## 📖 Usage

### Basic Usage

```python
from schwab_market_data_client import SchwabMarketDataClient, APIConfig, MarketConfig

# Initialize configuration
api_config = APIConfig()
market_config = MarketConfig()

# Create client
client = SchwabMarketDataClient(api_config, market_config)

# Fetch data
df = client.get_price_history(
    symbol="SPY",
    start_date="2025-01-01",
    end_date="2025-07-17",
    time_interval=5  # 5-minute intervals
)

# Save to CSV
if df is not None and not df.empty:
    df.to_csv("SPY_5m.csv", index=False)
```

### Advanced Usage

```python
from schwab_market_data_client import (
    SchwabMarketDataClient,
    APIConfig,
    MarketConfig,
    DataQualityValidator
)

# Custom configuration
api_config = APIConfig(
    access_token="YOUR_TOKEN",
    timeout=60,
    rate_limit_delay=2.0
)

market_config = MarketConfig(
    timezone='America/New_York',
    market_open='09:30:00',
    market_close='16:00:00'
)

# Create client
client = SchwabMarketDataClient(api_config, market_config)

# Fetch data for multiple symbols
symbols = ["SPY", "QQQ", "AAPL"]
time_intervals = [1, 5, 15]  # 1min, 5min, 15min

for symbol in symbols:
    for interval in time_intervals:
        df = client.get_price_history(
            symbol=symbol,
            start_date="2025-01-01",
            end_date="2025-01-31",
            time_interval=interval
        )

        if df is not None and not df.empty:
            # Validate data quality
            if DataQualityValidator.validate_dataframe(df):
                filename = f"{symbol}_{interval}m.csv"
                df.to_csv(filename, index=False)
                print(f"✅ Saved {filename}")
            else:
                print(f"❌ Data quality issues for {symbol}_{interval}m")
```

## 📊 Data Format

The API returns data in the following format:

| Column      | Type  | Description                           |
| ----------- | ----- | ------------------------------------- |
| `timestamp` | int   | Unix timestamp in milliseconds        |
| `datetime`  | str   | Human-readable datetime (ET timezone) |
| `open`      | float | Opening price                         |
| `high`      | float | Highest price                         |
| `low`       | float | Lowest price                          |
| `close`     | float | Closing price                         |
| `volume`    | int   | Trading volume                        |

### Example Output:

```csv
timestamp,datetime,open,high,low,close,volume
1640995200000,2025-01-01 09:30:00 EST,150.25,152.10,149.80,151.75,1234567
1640995500000,2025-01-01 09:35:00 EST,151.75,153.20,151.50,152.90,2345678
```

## 🔍 Data Quality Validation

The client includes comprehensive data quality checks:

- **Duplicate Detection**: Checks for duplicate timestamps and datetime values
- **Null Value Detection**: Identifies missing data in critical columns
- **Price Validation**: Ensures no negative prices
- **Volume Validation**: Checks for zero or negative volume
- **Timestamp Ordering**: Verifies chronological sequence
- **Market Hours Filtering**: Removes data outside trading hours
- **Holiday Schedule Handling**: Automatically handles early closures for:
  - July 3rd (Independence Day Eve)
  - Fourth Friday of November (Black Friday)
  - December 24th (Christmas Eve)

## ⚙️ API Parameters

### Supported Time Intervals

- `1` - 1 minute
- `5` - 5 minutes
- `10` - 10 minutes
- `15` - 15 minutes
- `30` - 30 minutes

### Period Optimization Strategy

The client uses an intelligent chunking strategy to maximize API efficiency:

1. **10 days** when ≥ 10 days remaining
2. **5 days** when ≥ 5 days remaining
3. **4 days** when ≥ 4 days remaining
4. **3 days** when ≥ 3 days remaining
5. **2 days** when ≥ 2 days remaining
6. **1 day** when ≥ 1 day remaining

This ensures optimal API usage while maintaining complete data coverage.

## 🏗️ Architecture

The project follows a modular, object-oriented design:

- **`SchwabMarketDataClient`**: Main API client
- **`DataQualityValidator`**: Data validation logic
- **`MarketDataProcessor`**: Data processing and filtering
- **`PeriodOptimizer`**: Optimal period calculation
- **`APIConfig`**: API configuration management
- **`MarketConfig`**: Market-specific settings

## 📝 Logging

The client uses structured logging with different levels:

- **INFO**: General information and progress updates
- **WARNING**: Non-critical issues (e.g., zero volume records)
- **ERROR**: Critical issues that prevent data processing

Example log output:

```
2025-07-17 12:37:45 - INFO - 🔄 Starting data fetch for SPY from 2025-01-01 to 2025-07-17
2025-07-17 12:37:45 - INFO - 📡 Fetching 10 days for SPY (5m) from 2025-01-01 to 2025-01-10
2025-07-17 12:37:46 - INFO - ✅ Retrieved 468 candles for this period
```

## 🚨 Error Handling

The client handles various error scenarios:

- **Network Errors**: Automatic retry and graceful degradation
- **API Errors**: Detailed error messages with response codes
- **Data Quality Issues**: Comprehensive validation with specific error reporting
- **Rate Limiting**: Built-in delays to respect API constraints

## 📚 API Documentation

For detailed API endpoint documentation, see [API_ENDPOINTS.md](API_ENDPOINTS.md).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes. Please ensure compliance with Schwab's API terms of service and rate limits. The authors are not responsible for any financial decisions made using this data.

## 🆘 Support

If you encounter any issues:

1. **Environment Setup Issues**:

   - Ensure your `.env` file exists and contains `SCHWAB_ACCESS_TOKEN=your_token`
   - Verify the token is not expired or invalid
   - Check that python-dotenv is installed: `pip install python-dotenv`

2. **API Issues**:

   - Check the [API_ENDPOINTS.md](API_ENDPOINTS.md) for endpoint details
   - Verify your access token is valid and has proper permissions
   - Ensure you have proper internet connectivity
   - Check the logs for detailed error messages

3. **Common Error Messages**:
   - `"No access token provided"`: Check your `.env` file and token value
   - `"API request failed: 401"`: Token is invalid or expired
   - `"API request failed: 429"`: Rate limit exceeded, increase `rate_limit_delay`

For additional support, please open an issue on the project repository.
