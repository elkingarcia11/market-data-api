"""
Schwab Market Data API Client

This module provides functionality to fetch historical price data from the Schwab Market Data API
with optimal period chunking and comprehensive data quality validation.
"""

import calendar
import os
import sys
import time
import logging
import pytz
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# Add the authentication module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'charles-schwab-authentication-module'))
from schwab_auth import SchwabAuth

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """Configuration for the Schwab Market Data API."""
    server: str = "https://api.schwabapi.com/marketdata/v1"
    timeout: int = 30
    rate_limit_delay: float = 1.0

@dataclass
class MarketConfig:
    """Market configuration settings."""
    timezone: str = 'America/New_York'
    market_open: str = '09:30:00'
    market_close: str = '16:00:00'
    early_close: str = '13:00:00'  # July 3rd early close, Fourth friday of November early close, December 24th early close

class DataQualityValidator:
    """Handles data quality validation for market data."""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> bool:
        """
        Comprehensive validation of market data dataframe.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if all validations pass, False otherwise
        """
        if df is None or df.empty:
            logger.error("DataFrame is None or empty - cannot validate")
            return False
        
        logger.info("🔍 Running comprehensive data quality validation...")
        
        validations = [
            DataQualityValidator._check_duplicate_timestamps,
            DataQualityValidator._check_duplicate_datetime,
            DataQualityValidator._check_null_values,
            DataQualityValidator._check_negative_prices,
            DataQualityValidator._check_volume_values,
            DataQualityValidator._check_timestamp_ordering
        ]
        
        for validation in validations:
            if not validation(df):
                return False
        
        logger.info("✅ All data quality validations passed!")
        return True
    
    @staticmethod
    def _check_duplicate_timestamps(df: pd.DataFrame) -> bool:
        """Check for duplicate timestamp values."""
        duplicate_timestamps = df[df.duplicated(subset=['timestamp'], keep=False)]
        if not duplicate_timestamps.empty:
            logger.error(f"Found {len(duplicate_timestamps)} duplicate timestamp records")
            logger.error(duplicate_timestamps[['timestamp', 'datetime']].head())
            return False
        logger.info("✅ No duplicate timestamps found")
        return True
    
    @staticmethod
    def _check_duplicate_datetime(df: pd.DataFrame) -> bool:
        """Check for duplicate datetime string values."""
        duplicate_datetime = df[df.duplicated(subset=['datetime'], keep=False)]
        if not duplicate_datetime.empty:
            logger.error(f"Found {len(duplicate_datetime)} duplicate datetime records")
            logger.error(duplicate_datetime[['timestamp', 'datetime']].head())
            return False
        logger.info("✅ No duplicate datetime values found")
        return True
    
    @staticmethod
    def _check_null_values(df: pd.DataFrame) -> bool:
        """Check for null values in critical columns."""
        critical_columns = ['timestamp', 'datetime', 'open', 'high', 'low', 'close', 'volume']
        null_counts = df[critical_columns].isnull().sum()
        if null_counts.sum() > 0:
            logger.warning(f"Found null values in dataframe:")
            logger.warning(null_counts[null_counts > 0])
        else:
            logger.info("✅ No null values found in critical columns")
        return True
    
    @staticmethod
    def _check_negative_prices(df: pd.DataFrame) -> bool:
        """Check for negative price values."""
        negative_prices = df[(df['open'] < 0) | (df['high'] < 0) | (df['low'] < 0) | (df['close'] < 0)]
        if not negative_prices.empty:
            logger.error(f"Found {len(negative_prices)} records with negative prices")
            return False
        logger.info("✅ No negative prices found")
        return True
    
    @staticmethod
    def _check_volume_values(df: pd.DataFrame) -> bool:
        """Check for zero or negative volume values."""
        zero_volume = df[df['volume'] <= 0]
        if not zero_volume.empty:
            logger.warning(f"Found {len(zero_volume)} records with zero or negative volume")
        else:
            logger.info("✅ All volume values are positive")
        return True
    
    @staticmethod
    def _check_timestamp_ordering(df: pd.DataFrame) -> bool:
        """Check that timestamps are in ascending order."""
        if not df['timestamp'].is_monotonic_increasing:
            logger.error("Timestamps are not in ascending order")
            return False
        logger.info("✅ Timestamps are in ascending order")
        return True

class PeriodOptimizer:
    """Handles optimal period calculation for API requests."""
    
    VALID_PERIODS = [10, 5, 4, 3, 2, 1]
    
    @staticmethod
    def get_optimal_period(days_remaining: int) -> int:
        """
        Determine the optimal period size for fetching data.
        Uses decreasing chunks: 10, 5, 4, 3, 2, 1 days.
        
        Args:
            days_remaining: Number of days left to fetch
            
        Returns:
            Optimal period size in days
        """
        for period in PeriodOptimizer.VALID_PERIODS:
            if days_remaining >= period:
                return period
        return 0

class MarketDataProcessor:
    """Handles processing and filtering of market data."""
    
    def __init__(self, config: MarketConfig):
        self.config = config
        self.timezone = pytz.timezone(config.timezone)
        self.market_open = datetime.strptime(config.market_open, '%H:%M:%S').time()
        self.market_close = datetime.strptime(config.market_close, '%H:%M:%S').time()
        self.early_close = datetime.strptime(config.early_close, '%H:%M:%S').time()
    
    def process_candles(self, candles: List[Dict]) -> pd.DataFrame:
        """
        Process raw candle data into a clean DataFrame.
        
        Args:
            candles: List of raw candle dictionaries from API
            
        Returns:
            Processed DataFrame with market hours filtering
        """
        df_data = []
        
        for candle in candles:
            processed_candle = self._process_single_candle(candle)
            if processed_candle:
                df_data.append(processed_candle)
        
        if not df_data:
            logger.warning("No valid candles found after processing")
            return pd.DataFrame()
        
        df = pd.DataFrame(df_data)
        df = df.sort_values('timestamp').drop_duplicates(subset=['timestamp'])
        
        logger.info(f"✅ Processed {len(df)} records from API (filtered to market hours)")
        return df
    
    def _process_single_candle(self, candle: Dict) -> Optional[Dict]:
        """Process a single candle with market hours filtering."""
        timestamp_ms = candle.get('datetime', 0)
        dt_utc = datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.UTC)
        dt_et = dt_utc.astimezone(self.timezone)
        
        # Filter out data outside market hours
        candle_time = dt_et.time()
        if candle_time < self.market_open or candle_time > self.market_close:
            return None
        
        # Special condition: July 3rd market closes at 1:00 PM EDT
        if dt_et.month == 7 and dt_et.day == 3 and candle_time > self.early_close:
            return None
        
        # Special condition: Fourth friday of November market closes at 1:00 PM EST
        # Figure out what day is the fourth friday of November
        if dt_et.month == 11 and self._is_fourth_friday(dt_et) and candle_time > self.early_close:
            return None
        
        # Special condition: December 24th market closes at 1:00 PM EST, 24th is a friday
        if dt_et.month == 12 and dt_et.day == 24 and candle_time > self.early_close:
            return None
        
        return {
            'timestamp': timestamp_ms,
            'datetime': dt_et.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'open': candle.get('open', 0),
            'high': candle.get('high', 0),
            'low': candle.get('low', 0),
            'close': candle.get('close', 0),
            'volume': candle.get('volume', 0)
        }
    
    @staticmethod
    def _is_fourth_friday(date: datetime) -> bool:
        # Get all Fridays in the month
        year, month = date.year, date.month
        fridays = []
        
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            if datetime(year, month, day).weekday() == 4:  # 4 = Friday
                fridays.append(day)
        
        return len(fridays) >= 4 and date.day == fridays[3]

class SchwabMarketDataClient:
    """Client for fetching market data from Schwab API."""
    
    def __init__(self, api_config: APIConfig, market_config: MarketConfig):
        self.api_config = api_config
        self.market_config = market_config
        self.processor = MarketDataProcessor(market_config)
        self.validator = DataQualityValidator()
        
        # Initialize authentication module
        self.auth = SchwabAuth()
        self.access_token = None
    
    def get_price_history(self, symbol: str, start_date: Optional[str], 
                         end_date: Optional[str], time_interval: int) -> Optional[pd.DataFrame]:
        """
        Get historical price data with optimal period chunking.
        
        Args:
            symbol: Stock symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            time_interval: Time interval in minutes (1, 5, 10, 15, 30)
            
        Returns:
            DataFrame with price data or None if failed
        """
        if not self._validate_inputs(symbol, time_interval):
            return None
        
        start_dt, end_dt = self._parse_dates(start_date, end_date)
        logger.info(f"🔄 Starting data fetch for {symbol} from {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
        
        all_candles = self._fetch_all_periods(symbol, start_dt, end_dt, time_interval)
        
        if not all_candles:
            logger.warning(f"⚠️  No data retrieved for {symbol}_{time_interval}m")
            return None
        
        return self.processor.process_candles(all_candles)
    
    def _get_valid_access_token(self) -> Optional[str]:
        """Get a valid access token from GCS refresh token."""
        if self.access_token:
            return self.access_token
        
        logger.info("🔐 Getting access token from GCS refresh token...")
        self.access_token = self.auth.get_valid_access_token(use_gcs_refresh_token=True)
        
        if not self.access_token:
            logger.error("❌ Failed to get access token from GCS")
            return None
        
        logger.info("✅ Successfully obtained access token")
        return self.access_token
    
    def _validate_inputs(self, symbol: str, time_interval: int) -> bool:
        """Validate input parameters."""
        valid_intervals = [1, 5, 10, 15, 30]
        
        if time_interval not in valid_intervals:
            logger.error(f"❌ Invalid time interval: {time_interval}. Valid values: {valid_intervals}")
            return False
        
        if not symbol:
            logger.error("❌ Invalid symbol provided")
            return False
        
        # Get access token automatically
        if not self._get_valid_access_token():
            logger.error("❌ Failed to get valid access token")
            return False
        
        return True
    
    def _parse_dates(self, start_date: Optional[str], end_date: Optional[str]) -> Tuple[datetime, datetime]:
        """Parse and localize start and end dates."""
        if start_date and end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            start_dt = datetime.strptime("2025-01-01", "%Y-%m-%d")
            end_dt = datetime.now()
        
        # Make timezone-aware
        timezone = pytz.timezone(self.market_config.timezone)
        if not start_dt.tzinfo:
            start_dt = timezone.localize(start_dt)
        if not end_dt.tzinfo:
            end_dt = timezone.localize(end_dt)
        
        return start_dt, end_dt
    
    def _fetch_all_periods(self, symbol: str, start_dt: datetime, end_dt: datetime, 
                          time_interval: int) -> List[Dict]:
        """Fetch data for all periods using optimal chunking."""
        all_candles = []
        current_start_dt = start_dt
        
        while current_start_dt <= end_dt:
            days_remaining = (end_dt - current_start_dt).days + 1
            period = PeriodOptimizer.get_optimal_period(days_remaining)
            
            if period == 0:
                logger.info(f"✅ Completed fetching data for {symbol}")
                break
            
            period_end_dt = current_start_dt + timedelta(days=period - 1)
            if period_end_dt > end_dt:
                period_end_dt = end_dt
            
            candles = self._fetch_period(symbol, current_start_dt, period_end_dt, period, time_interval)
            if candles is None:
                return []
            
            all_candles.extend(candles)
            current_start_dt = period_end_dt + timedelta(days=1)
        
        return all_candles
    
    def _fetch_period(self, symbol: str, start_dt: datetime, end_dt: datetime, 
                     period: int, time_interval: int) -> Optional[List[Dict]]:
        """Fetch data for a single period."""
        start_time_ms = int(start_dt.timestamp() * 1000)
        end_time_ms = int(end_dt.timestamp() * 1000)
        
        params = {
            'symbol': symbol,
            'periodType': 'day',
            'period': period,
            'frequencyType': 'minute',
            'frequency': time_interval,
            'startDate': start_time_ms,
            'endDate': end_time_ms,
            'needExtendedHoursData': 'false',
            'needPreviousClose': 'false'
        }
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        url = f"{self.api_config.server}/pricehistory"
        
        logger.info(f"📡 Fetching {period} days for {symbol} ({time_interval}m) from {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=self.api_config.timeout)
            time.sleep(self.api_config.rate_limit_delay)
            
            if response.status_code == 200:
                data = response.json()
                if 'candles' in data and data['candles']:
                    candles = data['candles']
                    logger.info(f"✅ Retrieved {len(candles)} candles for this period")
                    return candles
                else:
                    logger.info("📊 No candle data found in API response for this period")
                    return []
            else:
                logger.error(f"❌ API request failed: {response.status_code}")
                if response.text:
                    logger.error(f"Response: {response.text[:200]}...")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error sfetching price history: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching price history: {e}")
            return None 

def main():
    """Main function to demonstrate the market data client."""
    # Configuration
    api_config = APIConfig()
    market_config = MarketConfig()
    
    # Create client
    client = SchwabMarketDataClient(api_config, market_config)
    
    # Parameters
    symbols = open("symbols.txt").read().splitlines()
    timeframes = open("timeframes.txt").read().splitlines()
    start_date = "2025-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    for symbol in symbols:
        for timeframe in timeframes:
            time_interval = int(timeframe.split("m")[0])
            df = client.get_price_history(symbol, start_date, end_date, time_interval)
            if df is not None and not df.empty:
                filename = f"data/{timeframe}/{symbol}.csv"
                df.to_csv(filename, index=False)
    
    if df is not None and not df.empty:
        # Validate data quality
        if DataQualityValidator.validate_dataframe(df):
            filename = f"data/{symbol}_{time_interval}m.csv"
            df.to_csv(filename, index=False)
            logger.info(f"💾 Data saved to {filename}")
        else:
            logger.error("❌ Data quality issues detected - not saving to file")
    else:
        logger.error("❌ No data retrieved - cannot run tests")

if __name__ == "__main__":
    main()