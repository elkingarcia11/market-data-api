# Market Data API Documentation

## Overview

This document describes the Schwab Market Data API client functionality and the underlying price history endpoint used for fetching historical market data.

## Client Features

### Data Fetching

- **Multi-symbol Support**: Fetch data for multiple symbols simultaneously
- **Multiple Timeframes**: Support for 1m, 5m, 10m, 15m, 30m intervals
- **Date Range Configuration**: Configurable start and end dates via config files
- **Smart Appending**: Automatically appends new data to existing files without duplicates

### Data Storage

- **Structured Organization**: Files stored as `data/{timeframe}m/{symbol}.csv`
- **Timestamp Preservation**: Maintains original timestamps for precise time alignment
- **Market Hours Filtering**: Only includes data during regular trading hours (9:30 AM - 4:00 PM ET)

### Authentication

- **GCS Integration**: Secure token storage using Google Cloud Storage
- **Automatic Refresh**: Handles token refresh automatically
- **Schwab OAuth**: Integrated with Schwab's authentication system

## Schwab API Endpoint

```
GET https://api.schwabapi.com/marketdata/v1/pricehistory
```

## Parameters

### Required Parameters

#### `symbol` (string)

- **Description**: The equity symbol used to look up price history
- **Valid Values**: AAPL, SPY, QQQ, etc.
- **Example**: `AAPL`

#### `periodType` (string)

- **Description**: The chart period being requested
- **Valid Values**: `day`, `month`, `year`, `ytd`

### Optional Parameters

#### `period` (integer)

- **Description**: The number of chart period types
- **Valid Values**:

  - If `periodType` is `day`: 1, 2, 3, 4, 5, 10
  - If `periodType` is `month`: 1, 2, 3, 6
  - If `periodType` is `year`: 1, 2, 3, 5, 10, 15, 20
  - If `periodType` is `ytd`: 1

- **Defaults**:
  - `day`: 10
  - `month`: 1
  - `year`: 1
  - `ytd`: 1

#### `frequencyType` (string)

- **Description**: The time frequency type
- **Valid Values**: `minute`, `daily`, `weekly`, `monthly`

- **Valid Combinations**:

  - If `periodType` is `day`: only `minute`
  - If `periodType` is `month`: `daily`, `weekly`
  - If `periodType` is `year`: `daily`, `weekly`, `monthly`
  - If `periodType` is `ytd`: `daily`, `weekly`

- **Defaults**:
  - `day`: `minute`
  - `month`: `weekly`
  - `year`: `monthly`
  - `ytd`: `weekly`

#### `frequency` (integer)

- **Description**: The time frequency duration
- **Valid Values**:
  - If `frequencyType` is `minute`: 1, 5, 10, 15, 30
  - If `frequencyType` is `daily`: 1
  - If `frequencyType` is `weekly`: 1
  - If `frequencyType` is `monthly`: 1
- **Default**: 1

#### `startDate` (integer)

- **Description**: The start date in milliseconds since the UNIX epoch
- **Example**: `1451624400000`
- **Default**: If not specified, calculated as `(endDate - period)` excluding weekends and holidays

#### `endDate` (integer)

- **Description**: The end date in milliseconds since the UNIX epoch
- **Example**: `1451624400000`
- **Default**: Market close of the previous business day

#### `needExtendedHoursData` (boolean)

- **Description**: Whether to include extended hours data
- **Default**: `false`

#### `needPreviousClose` (boolean)

- **Description**: Whether to include previous close price/date
- **Default**: `false`

## Client Configuration

### Configuration Files

The client uses three configuration files:

1. **`symbols.txt`**: One symbol per line

   ```
   SPY
   QQQ
   AAPL
   MSFT
   ```

2. **`timeframes.txt`**: Time intervals (minutes), one per line

   ```
   1
   5
   15
   30
   ```

3. **`start_end_date.txt`**: Start and end dates, one per line
   ```
   2025-08-15
   2025-08-23
   ```

## Example API Request

The client automatically constructs requests like:

```bash
GET https://api.schwabapi.com/marketdata/v1/pricehistory?symbol=SPY&periodType=day&period=5&frequencyType=minute&frequency=5&startDate=1755255600000&endDate=1755906900000&needExtendedHoursData=true&needPreviousClose=true
```

## API Response Format

```json
{
  "symbol": "SPY",
  "candles": [
    {
      "datetime": 1755264600000,
      "open": 644.25,
      "high": 645.1,
      "low": 643.8,
      "close": 644.75,
      "volume": 1234567
    }
  ],
  "previousClose": 643.5,
  "previousCloseDate": 1755177600000,
  "empty": false
}
```

## Client Data Format

The client processes and saves data as CSV with the following format:

```csv
timestamp,datetime,open,high,low,close,volume
1755264600000,2025-08-15 09:30:00 EDT,644.25,645.10,643.80,644.75,1234567
1755264900000,2025-08-15 09:35:00 EDT,644.75,645.20,644.50,644.90,2345678
```

## Data Aggregation

The client includes a data aggregation module for converting minute data to higher timeframes:

```python
from market_data_aggregator import aggregate_market_data

# Convert 1-minute to 3-minute data
aggregate_market_data("1m", "3m", "SPY")

# Convert 1-minute to 15-minute data
aggregate_market_data("1m", "15m", "SPY")
```

### Aggregation Features

- **OHLC Aggregation**: Proper Open/High/Low/Close calculation
- **Volume Summation**: Accurate volume aggregation across periods
- **Timestamp Preservation**: Maintains timestamp of opening tick in each period
- **Market Hours Only**: Only aggregates data during regular market hours

## Error Handling

### Authentication Errors

```
Error refreshing token: 400 - {"error":"unsupported_token_type"}
```

- **Solution**: Check GCS authentication and refresh token validity

### API Errors

```
❌ API request failed: 401
```

- **Solution**: Token expired or invalid

```
❌ Invalid time interval: 3. Valid values: [1, 5, 10, 15, 30]
```

- **Solution**: Use supported time intervals only

### Data Quality Errors

```
❌ Data quality issues detected - not saving to file
```

- **Solution**: Check for duplicate timestamps, negative prices, or null values

## Usage Examples

### Basic Fetch

```bash
# Configure symbols and timeframes
echo "SPY" > symbols.txt
echo "5" > timeframes.txt
echo -e "2025-08-15\n2025-08-23" > start_end_date.txt

# Run client
python schwab_market_data_client.py
```

### Multiple Symbols and Timeframes

```bash
# Configure multiple symbols
cat > symbols.txt << EOF
SPY
QQQ
AAPL
MSFT
EOF

# Configure multiple timeframes
cat > timeframes.txt << EOF
1
5
15
EOF

# Run client
python schwab_market_data_client.py
```

## Rate Limits

The client implements rate limiting to respect Schwab API constraints:

- **Default Delay**: 1 second between requests
- **Configurable**: Adjust via `APIConfig.rate_limit_delay`
- **Automatic Backoff**: Built-in error handling for rate limit responses
