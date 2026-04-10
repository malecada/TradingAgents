"""Data transformation and metrics utilities for prediction models.

Adapted from Krypto-v0/src/models/model_utils.py to work with the OHLCV
DataFrame format returned by the CoinGecko/Binance data vendor.
"""

import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)

from tradingagents.dataflows.config import get_config

logger = logging.getLogger(__name__)


def compute_metrics(y_true, y_pred):
    """Return a dict of regression metrics (R2, MAE, RMSE, MAPE)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return {
        "r2": r2_score(y_true, y_pred),
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": root_mean_squared_error(y_true, y_pred),
        "mape": mean_absolute_percentage_error(y_true, y_pred),
    }


def ohlcv_to_model_df(df_ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Convert OHLCV DataFrame (from CoinGecko/Binance vendor) to model-ready format.

    The vendor returns columns: Date, Open, High, Low, Close, Volume.
    This function produces a date-indexed DataFrame with 'prices' as the
    close price column, plus derived features compatible with the original
    Krypto-v0 data_transform pipeline.

    Args:
        df_ohlcv: DataFrame with Date, Open, High, Low, Close, Volume columns.

    Returns:
        DataFrame indexed by date with 'prices' and supplementary features.
    """
    if df_ohlcv.empty:
        return pd.DataFrame()

    df = df_ohlcv.copy()

    # Ensure Date column is datetime
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
    df = df.sort_index()

    # Rename Close -> prices (the target column expected by all models)
    result = pd.DataFrame(index=df.index)
    result["prices"] = df["Close"].astype(float)

    # Derive supplementary features from OHLCV
    result["open"] = df["Open"].astype(float)
    result["high"] = df["High"].astype(float)
    result["low"] = df["Low"].astype(float)
    result["total_volumes"] = df["Volume"].astype(float)

    # Price-derived features
    result["daily_return"] = result["prices"].pct_change()
    result["high_low_spread"] = result["high"] - result["low"]
    result["open_close_spread"] = result["prices"] - result["open"]

    # Rolling statistics
    for window in [7, 14, 30]:
        result[f"ma_{window}"] = result["prices"].rolling(window).mean()
        result[f"vol_{window}"] = result["prices"].rolling(window).std()

    # Volume moving averages
    result["vol_ma_7"] = result["total_volumes"].rolling(7).mean()
    result["vol_ma_30"] = result["total_volumes"].rolling(30).mean()

    # Add an 'id' column (placeholder, used by data_transform for dummy encoding)
    result["id"] = "crypto"

    return result


def data_transform(df_all: pd.DataFrame, first_day_future, include_future_row=True):
    """Transform model DataFrame into features suitable for model training.

    Adapted from the original Krypto-v0 data_transform. The .shift(1) aligns
    features so that row i contains feature values from day i-1 -- no look-ahead.

    Args:
        df_all: Date-indexed DataFrame (output of ohlcv_to_model_df or similar).
        first_day_future: Date for the forecast horizon.
        include_future_row: If True, append a placeholder row for the forecast date.

    Returns:
        (reframed_lags, df_final)
    """
    cfg = get_config().get("prediction_models", {})
    n_lags = cfg.get("lag_features", 7)

    df_all = df_all.copy()

    # Drop 'market_caps' if present (not used in model training)
    if "market_caps" in df_all.columns:
        df_all = df_all.drop(columns="market_caps")

    if "index" in df_all.columns:
        df_all = df_all.drop(columns="index")

    if include_future_row:
        # Build a placeholder row for the forecast date, copying the last
        # known feature values (they will be shifted down by one position).
        future_idx = pd.to_datetime(first_day_future)
        future_row = df_all.iloc[[-1]].copy()
        future_row.index = [future_idx]
        # Cast to match dtypes before concat
        future_row = future_row.astype(
            {col: df_all[col].dtype for col in future_row.columns if col in df_all.columns},
            errors="ignore",
        )
        df_with_future = pd.concat([df_all, future_row], axis=0)
    else:
        df_with_future = df_all.copy()

    df_with_future.index.names = ["date"]
    df_with_future.index = pd.to_datetime(df_with_future.index).strftime("%Y-%m-%d")

    # Shift all columns down by 1 so features at position i originate
    # from day i-1 (prevents using same-day information for prediction).
    df_with_future = df_with_future.shift()

    # After shift(), row 0 is all-NaN -- drop it.
    df_with_future = df_with_future.iloc[1:]

    # Forward-fill, then fill remaining NaN with 0.
    df_final = df_with_future.infer_objects(copy=False).ffill().fillna(0)

    # Name/dummy encoding
    if "id" in df_final.columns:
        df_final["name"] = np.repeat(df_final["id"].iloc[0], len(df_final))
        df_final = df_final.drop(columns="id")
    else:
        df_final["name"] = "crypto"

    df_final["name_no"] = pd.get_dummies(df_final["name"], dtype="int")
    df_final.index = pd.to_datetime(df_final.index, utc=True)
    df_final["Day"] = df_final.index.day
    df_final["Month"] = df_final.index.month
    df_final["Year"] = df_final.index.year

    seasonal_dummy = pd.get_dummies(df_final.index.day, dtype="int")
    seasonal_dummy.index = df_final.index
    seasonal_dummy.columns = [f"day_{v}" for v in seasonal_dummy.columns]

    reframed = pd.concat([df_final, seasonal_dummy], axis=1).drop(columns="name")
    cols_to_drop = [c for c in reframed.columns if c == "date"]
    if cols_to_drop:
        reframed = reframed.drop(columns=cols_to_drop)
    reframed = reframed.reset_index(drop=True)

    # Lag features (backward-looking only)
    reframed_lags = reframed.copy()
    prices = reframed_lags["prices"].values
    for k in range(1, n_lags + 1):
        reframed_lags[f"lag{k}"] = pd.Series(prices).shift(k).values

    return reframed_lags, df_final


def fetch_ohlcv_for_model(coingecko_id: str, lookback_days: int) -> pd.DataFrame:
    """Fetch OHLCV data via the CoinGecko/Binance vendor and convert for model use.

    This is the bridge between TradingAgents' data vendor layer and the
    prediction model pipeline.

    Args:
        coingecko_id: CoinGecko coin ID (e.g. "bitcoin", "ethereum").
        lookback_days: Number of days of historical data to fetch.

    Returns:
        Date-indexed DataFrame ready for data_transform().
    """
    # Import here to avoid circular imports at module load time
    from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv

    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)

    # _load_crypto_ohlcv expects a date string for filtering
    end_str = end_date.strftime("%Y-%m-%d")

    df_ohlcv = _load_crypto_ohlcv(coingecko_id, end_str)

    if df_ohlcv.empty:
        logger.warning(f"No OHLCV data returned for {coingecko_id}")
        return pd.DataFrame()

    # Filter to lookback window
    start_dt = pd.to_datetime(start_date)
    if "Date" in df_ohlcv.columns:
        df_ohlcv = df_ohlcv[df_ohlcv["Date"] >= start_dt]

    # Convert to model format
    return ohlcv_to_model_df(df_ohlcv)
