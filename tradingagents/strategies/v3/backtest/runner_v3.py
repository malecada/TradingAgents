"""V3 runner orchestrator: features → regime → models → sizing → trades.

Composes Phase 1-6 components into a single backtest entry point. Look-ahead-
safe: every per-bar computation slices inputs to ``index <= as_of`` before
running rolling/aggregation operations.

Calls into existing ``tradingagents.backtesting.engine.run_backtest`` for
trade execution (fees, slippage, hold logic, stop-loss, circuit breaker).
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from tradingagents.backtesting.engine import BacktestResult, run_backtest
from tradingagents.backtesting.strategies import FiveLevelSignal, SignalLevel
from tradingagents.strategies.v3.config import V3Config
from tradingagents.strategies.v3.models.multi_horizon import (
    MultiHorizonEnsemble,
    consensus_signal,
)
from tradingagents.strategies.v3.regime.ensemble import detect_regime_v3
from tradingagents.strategies.v3.regime.hmm_v2 import NHHmmBundle
from tradingagents.strategies.v3.sizing.vol_target import (
    cdap_adjust,
    vol_target_position,
)

logger = logging.getLogger(__name__)


def _position_to_signal(position: float) -> str:
    """Map a continuous position value to a 5-level signal string."""
    if position > 1.0:
        return SignalLevel.BUY.value
    if position > 0.3:
        return SignalLevel.OVERWEIGHT.value
    if position >= -0.3:
        return SignalLevel.HOLD.value
    if position >= -1.0:
        return SignalLevel.UNDERWEIGHT.value
    return SignalLevel.SELL.value


def _build_v3_features_at(
    prices: pd.Series,
    microstructure_features: pd.DataFrame,
    derivatives_features: pd.DataFrame,
    as_of: pd.Timestamp,
) -> pd.DataFrame:
    """Build a single-row feature vector usable by MultiHorizonEnsemble.

    Returns an empty DataFrame if not enough history is available.
    All slices are bounded to ``index <= as_of`` (look-ahead guard).
    """
    sub_prices = prices[prices.index <= as_of]
    if len(sub_prices) < 21:
        return pd.DataFrame()

    ret_1d = sub_prices.pct_change().iloc[-1]
    ret_5d = sub_prices.pct_change(5).iloc[-1]
    vol_5d = sub_prices.pct_change().rolling(5).std().iloc[-1]
    vol_21d = sub_prices.pct_change().rolling(21).std().iloc[-1]

    feats: dict[str, float] = {
        "ret_1d": float(ret_1d) if pd.notna(ret_1d) else 0.0,
        "ret_5d": float(ret_5d) if pd.notna(ret_5d) else 0.0,
        "vol_5d": float(vol_5d) if pd.notna(vol_5d) else 0.0,
        "vol_21d": float(vol_21d) if pd.notna(vol_21d) else 0.0,
    }

    # Append last microstructure row if available
    if not microstructure_features.empty:
        sub_m = microstructure_features[microstructure_features.index <= as_of]
        if not sub_m.empty:
            for col in sub_m.columns:
                val = sub_m.iloc[-1][col]
                feats[col] = float(val) if pd.notna(val) else 0.0

    if not derivatives_features.empty:
        sub_d = derivatives_features[derivatives_features.index <= as_of]
        if not sub_d.empty:
            for col in sub_d.columns:
                val = sub_d.iloc[-1][col]
                feats[col] = float(val) if pd.notna(val) else 0.0

    return pd.DataFrame([feats], index=[as_of])


def _extract_expected_features(mhe: MultiHorizonEnsemble) -> list[str]:
    """Extract the feature name list from a fitted MultiHorizonEnsemble.

    Tries ``feature_name_`` first (LightGBM native), then
    ``feature_names_in_`` (scikit-learn convention). Falls back to an empty
    list (runner will use whatever columns ``_build_v3_features_at`` produces).
    """
    for _h, ph in mhe._models.items():
        members = getattr(ph.ensemble, "_fitted_members", None)
        if not members:
            break
        first = next(iter(members.values()))
        # LightGBM: feature_name_ is "auto" when trained with plain arrays
        fn = getattr(first, "feature_name_", None)
        if fn is not None and fn != "auto" and len(fn) > 0:
            return list(fn)
        # scikit-learn convention
        fn2 = getattr(first, "feature_names_in_", None)
        if fn2 is not None and len(fn2) > 0:
            return list(fn2)
        break
    return []


def run_v3_backtest(
    coin: str,
    prices: pd.Series,
    returns: pd.Series,
    microstructure_features: pd.DataFrame,
    derivatives_features: pd.DataFrame,
    regime_bundle: NHHmmBundle,
    multi_horizon_bundle: MultiHorizonEnsemble,
    config: V3Config,
    start: pd.Timestamp,
    end: pd.Timestamp,
    ticker: str = "",
    initial_capital: float = 10_000.0,
) -> BacktestResult:
    """End-to-end V3 backtest.

    Per-bar loop (look-ahead-safe):

    1. For each ``as_of`` in ``[start, end]``:
       - Slice all inputs to ``index <= as_of``.
       - Build price + microstructure + derivatives features (single row).
       - Update ``RegimeState`` via ``detect_regime_v3``.
       - Per-horizon predictions via ``MultiHorizonEnsemble.predict_proba``.
       - ``consensus_signal`` → ``(direction, confidence)``.
       - ``vol_target_position`` + ``cdap_adjust`` → final position.
       - Convert position to 5-level agent signal string.

    2. Pass signal list + price arrays to
       ``tradingagents.backtesting.engine.run_backtest``.

    3. Return ``BacktestResult``.

    Args:
        coin: Coin name (e.g. ``"bitcoin"``).
        prices: Close-price series with DatetimeIndex.
        returns: Simple-return series aligned to ``prices``.
        microstructure_features: Optional microstructure feature DataFrame
            (empty DataFrame accepted — runner falls back to price-only feats).
        derivatives_features: Optional derivatives feature DataFrame.
        regime_bundle: Fitted ``NHHmmBundle`` from ``train_nh_hmm``.
        multi_horizon_bundle: Fitted ``MultiHorizonEnsemble``.
        config: ``V3Config`` instance.
        start: First bar (inclusive) in the backtest window.
        end: Last bar (inclusive) in the backtest window.
        ticker: Ticker label stored in the result (defaults to ``coin.upper()``).
        initial_capital: Starting equity.

    Returns:
        ``BacktestResult`` from the V2 engine.
    """
    if start > end:
        raise ValueError("start must be <= end")
    bars = prices.loc[start:end].index
    if len(bars) == 0:
        raise ValueError(f"No bars between {start} and {end}")

    # Probe model feature names once — used to align runtime feature columns to
    # training schema. LGB trained on arrays uses feature_name_ == "auto"; in
    # that case fall through and use whatever columns the builder produces.
    expected_features = _extract_expected_features(multi_horizon_bundle)

    agent_signals: list[str] = []
    portfolio_dd_running = 0.0
    equity_high = float(initial_capital)
    equity_curr = float(initial_capital)

    for as_of in bars:
        feat_df = _build_v3_features_at(
            prices, microstructure_features, derivatives_features, as_of
        )
        if feat_df.empty:
            agent_signals.append(SignalLevel.HOLD.value)
            continue

        # Align columns to training schema when we have explicit names.
        if expected_features:
            for col in expected_features:
                if col not in feat_df.columns:
                    feat_df[col] = 0.0
            feat_df = feat_df[expected_features]

        try:
            probas_dict = multi_horizon_bundle.predict_proba(feat_df)
        except Exception:
            logger.exception("predict_proba failed at %s; falling back to HOLD", as_of)
            agent_signals.append(SignalLevel.HOLD.value)
            continue

        # predict_proba returns dict[int, np.ndarray] — extract scalar per horizon
        scalar_probas: dict[int, float] = {
            h: float(arr[0]) for h, arr in probas_dict.items()
        }

        try:
            regime = detect_regime_v3(
                prices=prices, bundle=regime_bundle, as_of=as_of
            )
        except Exception:
            logger.exception("detect_regime_v3 failed at %s; falling back to HOLD", as_of)
            agent_signals.append(SignalLevel.HOLD.value)
            continue

        direction, confidence = consensus_signal(scalar_probas, regime, config)

        # Realized annualised vol from log returns (21-bar rolling)
        sub_rets = returns.loc[returns.index <= as_of].iloc[-21:]
        rv = float(sub_rets.std() * np.sqrt(252)) if len(sub_rets) > 1 else 0.15

        position = vol_target_position(
            direction=direction,
            confidence=confidence,
            realized_vol_annual=rv,
            target_vol_annual=config.target_annual_vol,
            max_leverage=config.max_leverage,
        )
        position = cdap_adjust(
            position=position,
            portfolio_dd_pct=portfolio_dd_running,
            regime=regime,
            config=config,
        )

        # Update running equity simulation for CDAP drawdown tracking
        # (approximate — does not replicate the engine's exact cost model)
        daily_ret = returns.loc[as_of] if as_of in returns.index else 0.0
        gross = position * float(daily_ret)
        equity_curr = equity_curr * (1.0 + gross)
        if equity_curr > equity_high:
            equity_high = equity_curr
        portfolio_dd_running = (
            (equity_high - equity_curr) / equity_high if equity_high > 0 else 0.0
        )

        agent_signals.append(_position_to_signal(position))

    # Safety: pad / truncate to exactly len(bars)
    while len(agent_signals) < len(bars):
        agent_signals.append(SignalLevel.HOLD.value)
    agent_signals = agent_signals[: len(bars)]

    actuals = prices.loc[bars].values
    dates = pd.Series(bars)

    return run_backtest(
        dates=dates,
        actuals=actuals,
        agent_signals=agent_signals,
        strategy=FiveLevelSignal(),
        ticker=ticker or coin.upper(),
        initial_capital=initial_capital,
    )
