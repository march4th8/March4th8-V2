"""
data_source.py — swappable market data layer.

Swap this module later for Schwab API, Polygon, or Alpha Vantage
without touching analyzer.py or cli.py.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def fetch_ohlcv(ticker: str, lookback_days: int = 90) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: Open, High, Low, Close, Volume.
    Index is DatetimeIndex (UTC-normalized, tz-naive).
    Raises ValueError if the ticker is invalid or no data is returned.
    """
    end = datetime.today()
    # Add buffer so we always get 200-day MA even on a 90-day default window
    start = end - timedelta(days=max(lookback_days + 250, 400))

    raw = yf.download(
        ticker,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )

    if raw.empty:
        raise ValueError(f"No data returned for '{ticker}'. Check the symbol.")

    # Flatten MultiIndex columns that yfinance sometimes produces
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.dropna(inplace=True)

    return df
