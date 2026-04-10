"""Random Forest forecasting model for cryptocurrency price prediction.

Ported from Krypto-v0/src/models/rf_model.py, adapted to use TradingAgents'
config system and CoinGecko/Binance data vendor.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler

from tradingagents.dataflows.config import get_config
from tradingagents.models import model_utils as mu
from tradingagents.models.prediction import Prediction

logger = logging.getLogger(__name__)


# ── Config helpers ─────────────────────────────────────────────────


def _cfg():
    """Return the prediction_models config dict."""
    return get_config().get("prediction_models", {})


# ── Model construction ─────────────────────────────────────────────


def _build_rf(**overrides):
    """Instantiate a RandomForestRegressor from config with optional overrides."""
    cfg = _cfg()
    params = dict(
        n_estimators=cfg.get("rf_n_estimators", 1000),
        max_depth=cfg.get("rf_max_depth", None),
        min_samples_split=cfg.get("rf_min_samples_split", 5),
        min_samples_leaf=cfg.get("rf_min_samples_leaf", 2),
        random_state=42,
    )
    params.update(overrides)
    return RandomForestRegressor(**params)


# ── Checkpoint I/O ─────────────────────────────────────────────────


def _checkpoint_dir() -> Path:
    return Path(_cfg().get("checkpoint_dir", "./data/checkpoints/"))


def save_checkpoint(model, scaler):
    """Save trained RF model and scaler to disk."""
    ckpt = _checkpoint_dir()
    ckpt.mkdir(parents=True, exist_ok=True)
    model_path = ckpt / "rf_model.joblib"
    scaler_path = ckpt / "rf_scaler.joblib"
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    logger.info(f"RF checkpoint saved -> {model_path}")


def load_checkpoint():
    """Load RF model and scaler from disk.

    Returns:
        (model, scaler) tuple.
    """
    ckpt = _checkpoint_dir()
    model_path = ckpt / "rf_model.joblib"
    scaler_path = ckpt / "rf_scaler.joblib"
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    logger.info(f"RF checkpoint loaded <- {model_path}")
    return model, scaler


def _checkpoint_exists() -> bool:
    ckpt = _checkpoint_dir()
    return (ckpt / "rf_model.joblib").exists() and (ckpt / "rf_scaler.joblib").exists()


# ── Core building blocks ───────────────────────────────────────────


def prepare_data(df_all, include_future_row=True):
    """Run data_transform and return features, target, and metadata.

    Returns:
        (reframed_lags, df_final, first_day_future)
    """
    first_day_future = pd.to_datetime(datetime.now() + timedelta(days=1))
    reframed_lags, df_final = mu.data_transform(
        df_all, first_day_future, include_future_row=include_future_row,
    )
    return reframed_lags, df_final, first_day_future


def train_and_predict(X_train, y_train, X_test, scaler=None):
    """Fit one RF model and return predictions on X_test.

    If *scaler* is None a new MinMaxScaler is fit on X_train.

    Returns:
        (predictions, model, scaler)
    """
    if scaler is None:
        scaler = MinMaxScaler(feature_range=(0, 1))
        X_train_s = scaler.fit_transform(X_train.astype("float32"))
    else:
        X_train_s = scaler.transform(X_train.astype("float32"))
    X_test_s = scaler.transform(X_test.astype("float32"))

    rf = _build_rf()
    rf.fit(X_train_s, y_train.astype("float32"))
    preds = rf.predict(X_test_s)
    return preds, rf, scaler


def predict_with_confidence(model, scaler, X_test, alpha=None):
    """Return point prediction with confidence interval from individual trees.

    Uses the distribution of individual tree predictions to compute
    percentile-based prediction intervals (Meinshausen 2006).

    Returns:
        (prediction, lower, upper) arrays
    """
    if alpha is None:
        alpha = _cfg().get("prediction_interval_alpha", 0.05)
    X_test_s = scaler.transform(X_test.astype("float32"))
    tree_preds = np.array([t.predict(X_test_s) for t in model.estimators_])
    prediction = np.mean(tree_preds, axis=0)
    lower = np.percentile(tree_preds, 100 * (alpha / 2), axis=0)
    upper = np.percentile(tree_preds, 100 * (1 - alpha / 2), axis=0)
    return prediction, lower, upper


def _forecast_from_df(df_all, save_checkpoint_flag=False):
    """Retrain on all available data and forecast one step ahead.

    Returns:
        Prediction object with confidence interval.
    """
    reframed_lags, df_final, first_day_future = prepare_data(df_all)
    target_col = "prices"

    X_all = reframed_lags.drop(columns=target_col)
    y_all = reframed_lags[target_col].values.astype("float32")

    # Isolate training rows (all except the last future row) and drop NaN.
    X_train_vals = X_all.values[:-1].astype("float32")
    y_train = y_all[:-1]
    valid = np.isfinite(y_train) & np.all(np.isfinite(X_train_vals), axis=1)
    X_train_vals = X_train_vals[valid]
    y_train = y_train[valid]

    if len(X_train_vals) == 0:
        raise ValueError(
            "No valid training rows after dropping NaN -- the scraped data "
            "has too many gaps to train on."
        )

    # Fit scaler on training rows only (exclude the future row).
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaler.fit(X_train_vals)

    rf = _build_rf()
    rf.fit(scaler.transform(X_train_vals), y_train)

    if save_checkpoint_flag:
        save_checkpoint(rf, scaler)

    pred, lower, upper = predict_with_confidence(
        rf, scaler, X_all.values[-1:],
    )

    return Prediction(
        value=float(pred[0]),
        lower=float(lower[0]),
        upper=float(upper[0]),
        model_name="RandomForest",
        timestamp=first_day_future.to_pydatetime(),
        features_used=list(X_all.columns),
    )


# ── Public forecast_next (called by prediction analyst tools) ──────


def forecast_next(symbol: str, lookback_days: Optional[int] = None) -> str:
    """Fetch data, train Random Forest model, and return a formatted prediction string.

    This is the entry point called by the prediction analyst tools.

    Args:
        symbol: CoinGecko ID (e.g. "bitcoin", "ethereum").
        lookback_days: Number of days of historical data. Defaults to config value.

    Returns:
        A formatted string with the prediction, confidence interval,
        direction, and relevant metrics -- suitable for LLM consumption.
    """
    try:
        cfg = _cfg()
        if lookback_days is None:
            lookback_days = cfg.get("lookback_days", 300)

        # Fetch OHLCV data via the data vendor
        df_model = mu.fetch_ohlcv_for_model(symbol, lookback_days)
        if df_model.empty:
            return (
                f"[RandomForest] ERROR: No price data available for '{symbol}'. "
                f"Could not fetch OHLCV data from CoinGecko/Binance."
            )

        # Get current price for direction/percentage calculation
        current_price = float(df_model["prices"].iloc[-1])

        # Run prediction
        prediction = _forecast_from_df(df_model, save_checkpoint_flag=True)

        # Calculate direction and percentage change
        pct_change = ((prediction.value - current_price) / current_price) * 100
        direction = "UP" if pct_change > 0 else "DOWN"

        # Format output for the LLM analyst
        lines = [
            f"=== Random Forest Price Prediction for {symbol.upper()} ===",
            f"",
            f"Current Price: ${current_price:,.2f}",
            f"Predicted Price (next day): ${prediction.value:,.2f}",
            f"Direction: {direction} ({pct_change:+.2f}%)",
            f"",
            f"95% Confidence Interval:",
            f"  Lower Bound: ${prediction.lower:,.2f}",
            f"  Upper Bound: ${prediction.upper:,.2f}",
            f"  Interval Width: ${prediction.interval_width:,.2f}",
            f"",
            f"Model Details:",
            f"  Training samples: {lookback_days} days of historical data",
            f"  Features used: {len(prediction.features_used)}",
            f"  N estimators: {cfg.get('rf_n_estimators', 1000)}",
            f"  Forecast date: {prediction.timestamp.strftime('%Y-%m-%d')}",
        ]

        # Add confidence assessment
        interval_pct = (prediction.interval_width / current_price) * 100 if current_price > 0 else 0
        if interval_pct < 3:
            confidence_note = "High confidence (narrow prediction interval)"
        elif interval_pct < 8:
            confidence_note = "Moderate confidence"
        else:
            confidence_note = "Low confidence (wide prediction interval)"
        lines.append(f"  Confidence: {confidence_note} (interval is {interval_pct:.1f}% of price)")

        return "\n".join(lines)

    except Exception as e:
        logger.exception(f"RandomForest forecast failed for {symbol}")
        return (
            f"[RandomForest] ERROR: Forecast failed for '{symbol}'. "
            f"Reason: {e}"
        )


# ── Walk-forward evaluation (retained for offline evaluation) ──────


def walk_forward_evaluate(reframed_lags, min_train_window=None):
    """Rolling-window evaluation. Returns (predictions, actuals, window_start).

    Each iteration trains on data[:end_train] and predicts data[end_train],
    guaranteeing no future information leaks into training.
    """
    target_col = "prices"

    if min_train_window is not None:
        window_start = min(min_train_window, len(reframed_lags) - 1)
    elif len(reframed_lags) > 500:
        window_start = int(len(reframed_lags) * 0.9)
    elif len(reframed_lags) > 200:
        window_start = int(len(reframed_lags) * 0.8)
    else:
        window_start = int(len(reframed_lags) * 0.7)

    predictions = []
    actuals = []

    for end_train in range(window_start, len(reframed_lags)):
        train_slice = reframed_lags.iloc[:end_train]
        test_slice = reframed_lags.iloc[end_train: end_train + 1]

        X_tr = train_slice.drop(columns=target_col).values.astype("float32")
        y_tr = train_slice[target_col].values.astype("float32")
        X_te = test_slice.drop(columns=target_col).values.astype("float32")
        y_te = test_slice[target_col].values.astype("float32")

        sc = MinMaxScaler(feature_range=(0, 1))
        X_tr_s = sc.fit_transform(X_tr)
        X_te_s = sc.transform(X_te)

        model = _build_rf()
        model.fit(X_tr_s, y_tr)
        predictions.append(model.predict(X_te_s)[0])
        actuals.append(y_te[0])

    return predictions, actuals, window_start
