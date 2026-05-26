"""Shared stockstats column-rename helper for the market-v2 subpackage."""
from __future__ import annotations

import pandas as pd
from stockstats import StockDataFrame


def to_stockstats(df: pd.DataFrame) -> StockDataFrame:
    """Return a StockDataFrame view with lowercase OHLCV columns."""
    cols = {c.lower(): c for c in df.columns}
    rename = {
        cols.get("open", "Open"):   "open",
        cols.get("high", "High"):   "high",
        cols.get("low",  "Low"):    "low",
        cols.get("close","Close"):  "close",
        cols.get("volume","Volume"):"volume",
    }
    return StockDataFrame.retype(df.rename(columns=rename).copy())
