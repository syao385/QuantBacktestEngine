import pandas as pd
import numpy as np
import yfinance as yf
import logging
from datetime import datetime, timedelta
from typing import Optional, Union

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Universal Data Loader for QuantBacktestEngine.
    Fetches and standardizes OHLCV data from yfinance, CSV, Parquet, or pandas DataFrames.
    Ensures correct column naming (Open, High, Low, Close, Volume) required by backtesting.py core.
    """
    
    @staticmethod
    def load_data(
        source: Union[str, pd.DataFrame],
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Loads and cleans OHLCV price data.
        
        Args:
            source: Symbol string (e.g. 'SPY'), file path (CSV/Parquet), or pandas DataFrame.
            symbol: Ticker symbol if loading from yfinance or file.
            start_date: Start date string 'YYYY-MM-DD'.
            end_date: End date string 'YYYY-MM-DD'.
            timeframe: Bar timeframe ('1d', '1h', '5m', etc.).
            
        Returns:
            Standardized pandas DataFrame with DatetimeIndex and columns [Open, High, Low, Close, Volume].
        """
        df: Optional[pd.DataFrame] = None
        
        if isinstance(source, pd.DataFrame):
            df = source.copy()
        elif isinstance(source, str):
            if source.endswith(".csv"):
                df = pd.read_csv(source, parse_dates=True, index_col=0)
            elif source.endswith(".parquet") or source.endswith(".pq"):
                df = pd.read_parquet(source)
            else:
                # Assume source is ticker symbol for yfinance
                sym = symbol or source
                df = DataLoader._fetch_yfinance(sym, start_date, end_date, timeframe)
        else:
            raise ValueError(f"Unsupported data source type: {type(source)}")

        if df is None or df.empty:
            raise ValueError(f"No data returned for source: {source}")

        return DataLoader._clean_and_format(df)

    @staticmethod
    def _fetch_yfinance(
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetches historical price data using yfinance API."""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        logger.info(f"Fetching {symbol} from yfinance ({start_date} to {end_date}, interval={interval})...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval=interval)
        
        if df.empty:
            raise ValueError(f"yfinance returned empty dataset for {symbol}")
            
        return df

    @staticmethod
    def _clean_and_format(df: pd.DataFrame) -> pd.DataFrame:
        """Standardizes column names and index structure."""
        # Standardize column mapping case-insensitively
        col_map = {}
        for col in df.columns:
            c_lower = str(col).strip().lower()
            if c_lower in ['open', 'op']:
                col_map[col] = 'Open'
            elif c_lower in ['high', 'hi']:
                col_map[col] = 'High'
            elif c_lower in ['low', 'lo']:
                col_map[col] = 'Low'
            elif c_lower in ['close', 'c', 'adj close', 'adjclose']:
                col_map[col] = 'Close'
            elif c_lower in ['volume', 'vol', 'v']:
                col_map[col] = 'Volume'

        df = df.rename(columns=col_map)
        
        required_cols = ['Open', 'High', 'Low', 'Close']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise KeyError(f"DataFrame is missing required OHLC columns: {missing}")

        if 'Volume' not in df.columns:
            df['Volume'] = 10000.0

        # Select required columns
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()

        # Handle index timestamp formatting
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        df = df.sort_index()
        df = df.ffill().bfill()
        
        # Remove any non-positive prices
        df = df[(df['Open'] > 0) & (df['High'] > 0) & (df['Low'] > 0) & (df['Close'] > 0)]

        return df
