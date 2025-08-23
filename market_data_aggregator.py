"""
Aggregate market data from data/timeframe/symbol.csv files into a higher time frame.
"""

import pandas as pd

def aggregate_market_data(from_timeframe: str, to_timeframe: str, symbol: str):
    """
    Aggregate market data from data/timeframe/symbol.csv files into a higher time frame.
    """
    # Get the data/timeframe/symbol.csv file
    filename = f"data/{from_timeframe}/{symbol}.csv"
    df = pd.read_csv(filename)
    
    # Convert datetime column to datetime type and set as index
    # Handle the EDT timezone properly - parse as local time
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S EDT')
    df.set_index('datetime', inplace=True)
    
    # Filter to only include market hours (9:30 AM - 4:00 PM)
    market_open = pd.Timestamp('09:30').time()
    market_close = pd.Timestamp('16:00').time()
    df = df[(df.index.time >= market_open) & (df.index.time < market_close)]
    
    # Convert timeframe strings to pandas offset aliases
    timeframe_mapping = {
        "1m": "1min",
        "3m": "3min", 
        "5m": "5min",
        "10m": "10min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1H",
        "1d": "1D"
    }
    
    to_timeframe_pandas = timeframe_mapping.get(to_timeframe, to_timeframe)

    # Aggregate the data
    df_aggregated = df.resample(to_timeframe_pandas).agg({
        "timestamp": "first",  # Keep timestamp of the opening tick
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    })
    
    # Remove rows where all OHLC values are NaN (no data for that period)
    df_aggregated = df_aggregated.dropna(subset=['open', 'high', 'low', 'close'])
    
    # Reset index to make datetime a column again
    df_aggregated.reset_index(inplace=True)
    
    # Convert datetime back to string format for consistency
    df_aggregated['datetime'] = df_aggregated['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S EDT')

    # Reorder columns to put timestamp first
    df_aggregated = df_aggregated[['timestamp', 'datetime', 'open', 'high', 'low', 'close', 'volume']]
    
    # Convert timestamp back to integer to remove the .0
    df_aggregated['timestamp'] = df_aggregated['timestamp'].astype(int)
    
    # Save the aggregated data
    df_aggregated.to_csv(f"data/{to_timeframe}/{symbol}.csv", index=False)
    
    print(f"✅ Successfully aggregated {symbol} from {from_timeframe} to {to_timeframe}")
    print(f"📊 Original records: {len(df)}, Aggregated records: {len(df_aggregated)}")

if __name__ == "__main__":
    aggregate_market_data("1m", "3m", "SPY")