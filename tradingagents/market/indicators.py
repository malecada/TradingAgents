"""Deterministic 13-name indicator whitelist + direction rules.

Indicator values are computed via stockstats (the same backend used by
``tradingagents.dataflows.stockstats_utils``). Direction rules are
asymmetric-default-friendly: a typical RSI in the 45-55 band registers
0 (neutral) so it does NOT amplify a one-sided category vote. This is
the key to making ``conflict_score`` informative across coins.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
from stockstats import StockDataFrame

INDICATOR_WHITELIST = [
    "close_30_sma", "close_50_sma", "close_200_sma", "close_10_ema",
    "macd", "macds", "macdh", "rsi",
    "boll", "boll_ub", "boll_lb", "atr",
    "vwma",
]

INDICATOR_CATEGORY: Dict[str, str] = {
    "close_30_sma":  "trend",
    "close_50_sma":  "trend",
    "close_200_sma": "trend",
    "close_10_ema":  "trend",
    "macd":          "momentum",
    "macds":         "momentum",
    "macdh":         "momentum",
    "rsi":           "momentum",
    "boll":          "volatility",
    "boll_ub":       "volatility",
    "boll_lb":       "volatility",
    "atr":           "volatility",
    "vwma":          "volume",
}

_ATR_PCT_WINDOW = 90
_RSI_HIGH = 55.0
_RSI_LOW = 45.0


def _ohlcv_to_stockstats(df: pd.DataFrame) -> StockDataFrame:
    cols = {c.lower(): c for c in df.columns}
    rename = {
        cols.get("open", "Open"):   "open",
        cols.get("high", "High"):   "high",
        cols.get("low",  "Low"):    "low",
        cols.get("close","Close"):  "close",
        cols.get("volume","Volume"):"volume",
    }
    sdf = df.rename(columns=rename).copy()
    return StockDataFrame.retype(sdf)


def compute_indicator_values(df: pd.DataFrame) -> Dict[str, float]:
    """Compute the 13 whitelist indicator values at the most recent bar.

    Caller is responsible for filtering ``df`` to ``Date <= trade_date``
    upstream (the existing OHLCV loaders already do this).
    """
    sdf = _ohlcv_to_stockstats(df)
    out: Dict[str, float] = {}
    for name in INDICATOR_WHITELIST:
        try:
            series = sdf[name]
            val = float(series.iloc[-1])
        except Exception:
            val = float("nan")
        out[name] = val
    return out


def _atr_percentile(df: pd.DataFrame, window: int = _ATR_PCT_WINDOW) -> float:
    sdf = _ohlcv_to_stockstats(df)
    atr_series = sdf["atr"]
    tail = atr_series.tail(window).dropna()
    if len(tail) < 10 or not np.isfinite(atr_series.iloc[-1]):
        return 0.5
    rank = (tail < atr_series.iloc[-1]).mean()
    return float(np.clip(rank, 0.0, 1.0))


def compute_indicator_directions(
    df: pd.DataFrame, values: Dict[str, float]
) -> Dict[str, int]:
    """Return -1 / 0 / +1 per whitelist indicator using the rules table."""
    close = float(df["Close"].iloc[-1])
    atr_pct = _atr_percentile(df)
    macd = values.get("macd", float("nan"))
    macds = values.get("macds", float("nan"))
    macdh = values.get("macdh", float("nan"))
    rsi = values.get("rsi", float("nan"))
    boll = values.get("boll", float("nan"))
    boll_ub = values.get("boll_ub", float("nan"))
    boll_lb = values.get("boll_lb", float("nan"))
    vwma = values.get("vwma", float("nan"))

    d: Dict[str, int] = {}
    for sma_name in ("close_30_sma", "close_50_sma",
                     "close_200_sma", "close_10_ema"):
        v = values.get(sma_name, float("nan"))
        d[sma_name] = (
            1 if np.isfinite(v) and close > v else
           -1 if np.isfinite(v) and close < v else 0
        )
    d["macd"]  = 1 if macd > 0 else -1 if macd < 0 else 0
    d["macds"] = (
        1 if np.isfinite(macd) and np.isfinite(macds) and macd > macds else
       -1 if np.isfinite(macd) and np.isfinite(macds) and macd < macds else 0
    )
    d["macdh"] = 1 if macdh > 0 else -1 if macdh < 0 else 0
    d["rsi"]   = (
        1 if np.isfinite(rsi) and rsi > _RSI_HIGH else
       -1 if np.isfinite(rsi) and rsi < _RSI_LOW else 0
    )
    d["boll"]  = (
        1 if np.isfinite(boll) and close > boll else
       -1 if np.isfinite(boll) and close < boll else 0
    )
    d["boll_ub"] = (
        1 if np.isfinite(boll_ub) and close > boll_ub else
       -1 if np.isfinite(boll_lb) and close < boll_lb else 0
    )
    d["boll_lb"] = (
        1 if np.isfinite(boll_lb) and close < boll_lb else
       -1 if np.isfinite(boll_ub) and close > boll_ub else 0
    )
    d["atr"]  = 1 if atr_pct < 0.4 else -1 if atr_pct > 0.8 else 0
    d["vwma"] = (
        1 if np.isfinite(vwma) and close > vwma else
       -1 if np.isfinite(vwma) and close < vwma else 0
    )
    return d
