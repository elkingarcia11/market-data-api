# Market Data API

A comprehensive Python system for fetching, processing, and managing historical market data from the Schwab Market Data API. Features intelligent data fetching, quality validation, cloud-based authentication, and data aggregation capabilities.

## 🚀 Features

### Core Functionality

- **Optimal Period Chunking**: Intelligently fetches data in decreasing chunks (10→5→4→3→2→1 days) to maximize API efficiency
- **Comprehensive Data Validation**: Built-in quality checks for duplicates, null values, negative prices, and timestamp ordering
- **Market Hours Filtering**: Automatically filters data to regular market hours (9:30 AM - 4:00 PM ET)
- **Special Holiday Handling**: Supports early market closures (July 3rd, Black Friday, December 24th, etc.)
- **Smart Data Appending**: Automatically combines new data with existing files without duplicates

### Authentication & Security

- **GCS Authentication**: Integrated Google Cloud Storage authentication for secure token management
- **Automatic Token Refresh**: Handles token refresh and expiration automatically
- **Schwab OAuth Integration**: Complete OAuth 2.0 flow implementation

### Data Processing

- **Multiple Timeframes**: Support for 1m, 5m, 10m, 15m, 30m intervals with configurable fetching
- **Data Aggregation**: Built-in aggregation tools to convert minute data to higher timeframes
- **Structured Storage**: Organized file structure with `data/{timeframe}m/{symbol}.csv` format

### Development Features

- **Professional Logging**: Structured logging with timestamps and log levels
- **Type Safety**: Full type hints for better IDE support and code clarity
- **Modular Architecture**: Clean, maintainable object-oriented design
- **Rate Limiting**: Built-in rate limiting to respect API constraints
- **Error Handling**: Comprehensive error handling for network, API, and data quality issues

## 📋 Requirements

- Python 3.8+
- Charles Schwab Developer Account
- Google Cloud Storage Account (for secure token storage)
- Internet connection

## 🛠️ Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd market-data-api
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
   # Create .env file with your Schwab API credentials
   cat > .env << EOF
   SCHWAB_APP_KEY=your_schwab_app_key
   SCHWAB_APP_SECRET=your_schwab_app_secret
   GCS_BUCKET_NAME=your_gcs_bucket_name
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
   EOF
   ```

## 🔧 Configuration

### Configuration Files

The system uses configuration files for flexible operation:

1. **`symbols.txt`**: Lists symbols to fetch (one per line)

   ```
   SPY
   QQQ
   AAPL
   ```

2. **`timeframes.txt`**: Specifies time intervals in minutes (one per line)

   ```
   1
   5
   15
   ```

3. **`start_end_date.txt`**: Contains start and end dates (one per line)

   ```
   2025-08-23
   ```

   Note: If only one date is provided, it's used as the start date and the system fetches until today.

### Authentication Setup

The system uses Google Cloud Storage (GCS) for secure authentication token management:

1. **Schwab Authentication Module**: Uses the integrated `charles-schwab-authentication-module`
2. **GCS Integration**: Automatically retrieves refresh tokens from Google Cloud Storage
3. **Token Management**: Handles token refresh and expiration automatically

### Getting Your Schwab API Access

To use this system, you'll need Schwab API access:

1. **Register for Schwab Developer Account**: Visit the [Schwab Developer Portal](https://developer.schwab.com/)
2. **Create an Application**: Set up a new application in your developer dashboard
3. **Set up OAuth**: Configure OAuth flow for token generation
4. **Configure GCS**: Set up Google Cloud Storage for secure token storage

**Note**: The authentication system automatically handles token refresh and expiration.

### API Configuration

The system automatically handles authentication through the integrated Schwab authentication module. The `APIConfig` class in `schwab_market_data_client.py` is configured for optimal API usage:

```python
@dataclass
class APIConfig:
    server: str = "https://api.schwabapi.com/marketdata/v1"
    timeout: int = 30
    rate_limit_delay: float = 1.0
```

**Note**: Access tokens are automatically retrieved from GCS and refreshed as needed. No manual token management required.

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

### Quick Start

1. **Configure your symbols and timeframes**:

   ```bash
   echo "SPY" > symbols.txt
   echo "5" > timeframes.txt
   echo -e "2025-08-15\n2025-08-23" > start_end_date.txt
   ```

2. **Run the system**:
   ```bash
   source venv/bin/activate
   python schwab_market_data_client.py
   ```

The system will automatically:

- Fetch data for all symbols in `symbols.txt`
- Use all timeframes in `timeframes.txt`
- Save data to `data/{timeframe}m/{symbol}.csv`
- Append new data to existing files (no duplicates)
- Handle authentication and token refresh automatically

### Programmatic Usage

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
    start_date="2025-08-15",
    end_date="2025-08-23",
    time_interval=5  # 5-minute intervals
)

# Data is automatically saved to data/5m/SPY.csv
```

### Data Aggregation

Convert minute data to higher timeframes:

```python
from market_data_aggregator import aggregate_market_data

# Aggregate 1-minute data to 3-minute
aggregate_market_data("1m", "3m", "SPY")

# Aggregate 1-minute data to 15-minute
aggregate_market_data("1m", "15m", "SPY")
```

### File Structure

The system organizes data in a structured format:

```
market-data-api/
├── data/
│   ├── 1m/
│   │   └── SPY.csv
│   ├── 3m/
│   │   └── SPY.csv
│   └── 5m/
│       ├── SPY.csv
│       └── SPY_indicators.csv
├── charles-schwab-authentication-module/
│   ├── schwab_auth.py
│   ├── gcs-python-module/
│   └── README.md
├── schwab_market_data_client.py
├── market_data_aggregator.py
├── symbols.txt
├── timeframes.txt
├── start_end_date.txt
├── requirements.txt
└── README.md
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

# Fetch data with validation
df = client.get_price_history(
    symbol="SPY",
    start_date="2025-08-15",
    end_date="2025-08-23",
    time_interval=1
)

if df is not None and not df.empty:
    # Data is automatically validated and saved
    print(f"✅ Fetched {len(df)} records")
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

### Core Components

- **`SchwabMarketDataClient`**: Main API client for data fetching
- **`DataQualityValidator`**: Comprehensive data validation logic
- **`MarketDataProcessor`**: Data processing and market hours filtering
- **`PeriodOptimizer`**: Optimal period calculation for API efficiency
- **`APIConfig`**: API configuration management
- **`MarketConfig`**: Market-specific settings and holiday handling

### Authentication Module

- **`SchwabAuth`**: OAuth 2.0 authentication with GCS integration
- **`GCSClient`**: Google Cloud Storage operations for secure token management

### Data Processing

- **`market_data_aggregator.py`**: Converts minute data to higher timeframes
- **Data Storage**: Structured CSV format with timestamp preservation

## 📝 Logging

The system uses structured logging with different levels:

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

The system handles various error scenarios:

- **Network Errors**: Automatic retry and graceful degradation
- **API Errors**: Detailed error messages with response codes
- **Data Quality Issues**: Comprehensive validation with specific error reporting
- **Rate Limiting**: Built-in delays to respect API constraints
- **Authentication Errors**: Automatic token refresh and GCS fallback

## 📚 API Documentation

For detailed API endpoint documentation, see [API.md](API.md).

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

   - Ensure your `.env` file exists and contains all required Schwab API credentials
   - Verify your Google Cloud Storage credentials are properly configured
   - Check that all dependencies are installed: `pip install -r requirements.txt`

2. **Authentication Issues**:

   - Check the [charles-schwab-authentication-module/README.md](charles-schwab-authentication-module/README.md) for detailed setup
   - Verify your Schwab API credentials are valid
   - Ensure your GCS bucket exists and is accessible
   - Check that your service account has proper permissions

3. **API Issues**:

   - Check the [API.md](API.md) for endpoint details
   - Verify your access token is valid and has proper permissions
   - Ensure you have proper internet connectivity
   - Check the logs for detailed error messages

4. **Common Error Messages**:
   - `"No valid refresh token available"`: Run authentication setup first
   - `"API request failed: 401"`: Token is invalid or expired
   - `"API request failed: 429"`: Rate limit exceeded, increase `rate_limit_delay`

For additional support, please open an issue on the project repository.

## 📊 Current Project Status

### Data Collected

The system has successfully collected market data for:

- **Symbol**: SPY (SPDR S&P 500 ETF Trust)
- **Timeframes**: 1m, 3m, 5m intervals
- **Date Range**: January 2, 2025 onwards
- **Data Quality**: All data validated and filtered for market hours

### File Structure

```
data/
├── 1m/SPY.csv          # 1-minute interval data
├── 3m/SPY.csv          # 3-minute interval data (aggregated)
└── 5m/
    ├── SPY.csv         # 5-minute interval data
    └── SPY_indicators.csv  # Additional indicators data
```

### Sample Data Format

```csv
timestamp,datetime,open,high,low,close,volume
1735828200000,2025-01-02 09:30:00 EST,589.39,589.65,587.81,587.83,1596109
1735828500000,2025-01-02 09:35:00 EST,587.8,587.91,586.23,586.26,762802
```

### Configuration

- **Current Symbol**: SPY
- **Current Timeframe**: 5 minutes
- **Start Date**: 2025-08-23 (configurable via `start_end_date.txt`)
