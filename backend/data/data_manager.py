import os
import time
import pandas as pd
import requests

class DataManager:
    """
    Historical data manager with CSV storage.
    Retrieves data from Binance and stores it locally.
    """
    
    def __init__(self):
        self.data_dir = "backend/data/historical"
        # Create the data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)

    def get_historical_data(self, symbol: str, start_date: pd.Timestamp, end_date: pd.Timestamp, timeframe: str) -> pd.DataFrame:
        """
        Retrieves historical OHLCV data for a given symbol and timeframe.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            start_date: Start date
            end_date: End date
            timeframe: Time interval (e.g., "1m", "5m", "1h", etc.)
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        
        filename = f"{symbol}_{timeframe}.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        # Normalize input dates (remove timezone if present)
        start_date = start_date.tz_localize(None) if start_date.tz is not None else start_date
        end_date = end_date.tz_localize(None) if end_date.tz is not None else end_date
        
        # Load existing data or create an empty DataFrame
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)  # Remove timezone
            df = df.sort_values('timestamp')
        else:
            df = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Check if we need to fetch missing data
        missing_ranges = self._find_missing_ranges(df, start_date, end_date, timeframe)
        
        # Fetch missing data from Binance
        for range_start, range_end in missing_ranges:
            new_data = self._fetch_from_binance(symbol, range_start, range_end, timeframe)
            print("New data fetched:", new_data)
            if not new_data.empty:
                df = pd.concat([df, new_data], ignore_index=True)
                print("Data concatenated:", df)
            else:
                raise ValueError(f"No data retrieved for {symbol} from {range_start} to {range_end}")

        # Clean and save
        if not df.empty:
            df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
            df.to_csv(filepath, index=False)
        
        # Return only the data within the requested range
        return df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)].copy()

    def _find_missing_ranges(self, df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp, timeframe: str) -> list:
        """Finds missing data ranges."""
        missing_ranges = []
        
        if df.empty:
            return [(start_date, end_date)]
        
        # Check before the first timestamp
        first_ts = df['timestamp'].min()
        if start_date < first_ts:
            # Correctly calculate the end of the missing range
            timeframe_delta = pd.Timedelta(timeframe)
            missing_ranges.append((start_date, first_ts - timeframe_delta))
        
        # Check after the last timestamp
        last_ts = df['timestamp'].max()
        if end_date > last_ts:
            timeframe_delta = pd.Timedelta(timeframe)
            missing_ranges.append((last_ts + timeframe_delta, end_date))
        
        # Check for gaps in the data
        df_in_range = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
        if len(df_in_range) > 1:
            expected_timestamps = pd.date_range(start=df_in_range['timestamp'].min(), 
                                              end=df_in_range['timestamp'].max(), 
                                              freq=timeframe)
            actual_timestamps = set(df_in_range['timestamp'])
            
            gap_start = None
            for ts in expected_timestamps:
                if ts not in actual_timestamps:
                    if gap_start is None:
                        gap_start = ts
                else:
                    if gap_start is not None:
                        timeframe_delta = pd.Timedelta(timeframe)
                        missing_ranges.append((gap_start, ts - timeframe_delta))
                        gap_start = None
            
            # Handle a gap that goes to the end
            if gap_start is not None:
                missing_ranges.append((gap_start, df_in_range['timestamp'].max()))
        
        return missing_ranges

    def _fetch_from_binance(self, symbol: str, start_date: pd.Timestamp, end_date: pd.Timestamp, interval: str) -> pd.DataFrame:
        """Fetches data from the Binance API."""
        base_url = "https://api.binance.com/api/v3/klines"
        
        print(f"Fetching data for {symbol} from {start_date} to {end_date} with interval {interval}")
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)

        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_ms,
            'endTime': end_ms,
            'limit': 1000
        }
        
        all_data = []
        
        while start_ms < end_ms:
            params['startTime'] = start_ms
            
            try:
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    break
                
                for kline in data:
                    all_data.append({
                        'timestamp': pd.to_datetime(kline[0], unit='ms').tz_localize(None),  # Remove timezone
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                
                # Update the start timestamp for the next request
                start_ms = data[-1][0] + 1
                
                if start_ms < end_ms:
                    time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"Error while fetching data: {e}")
                break

        return pd.DataFrame(all_data)