# Market Data API - Price History Endpoint

## Overview

This endpoint retrieves historical price data for equity symbols.

## Endpoint

```
GET /price-history
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

## Example Request

```bash
GET /price-history?symbol=AAPL&periodType=day&period=5&frequencyType=minute&frequency=5
```

## Example Response

```json
{
  "symbol": "AAPL",
  "candles": [
    {
      "datetime": 1640995200000,
      "open": 150.25,
      "high": 152.1,
      "low": 149.8,
      "close": 151.75,
      "volume": 1234567
    }
  ],
  "previousClose": 149.5,
  "previousCloseDate": 1640908800000
}
```

## Error Responses

### 400 Bad Request

```json
{
  "error": "Invalid parameter value",
  "message": "Invalid symbol provided"
}
```

### 404 Not Found

```json
{
  "error": "Symbol not found",
  "message": "The requested symbol does not exist"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```
