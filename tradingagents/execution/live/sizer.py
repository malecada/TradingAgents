"""Single-step V2 sizing for the live cycle.

Wraps tradingagents.strategies.v2_sizing primitives and applies them to one
coin's most recent prediction + the rolling price history. Returns a SizingResult
with all components needed for journal logging.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tradingagents.strategies.v2_sizing import (
    apply_leverage,
    apply_trend_filter,
    compute_realized_vol,
    generate_term_structure_signals,
    vol_regime_mask,
    vol_targeted_size,
)


@dataclass
class SizingResult:
    coin: str
    signal: int
    confidence: float
    realized_vol: float
    base_size: float
    leverage: float
    sma_multiplier: float
    final_size_notional: float
    vol_ok: bool


def compute_size(
    *, coin, prediction, price_history,
    horizons, symmetric,
    target_vol, kelly_fraction, max_leverage,
    vol_lookback, vol_cap_pct, confidence_ref,
    trend_sma, trend_multiplier,
) -> SizingResult:
    df_coin = pd.DataFrame({
        "ref_price": [prediction["ref_price"]],
        **{f"pred_h{h}": [prediction[f"pred_h{h}"]] for h in horizons},
    })
    signals, conf = generate_term_structure_signals(
        df_coin, horizons=horizons, confidence_ref=confidence_ref,
        asymmetric=not symmetric,
    )
    signal = int(signals[0])
    confidence = float(conf[0])

    prices = price_history.sort_values("date")["close"].values
    vol_series = compute_realized_vol(prices, lookback=vol_lookback)
    realized_vol = float(vol_series[-1]) if len(vol_series) and not np.isnan(vol_series[-1]) else float("nan")
    mask = vol_regime_mask(vol_series, percentile_cap=vol_cap_pct)
    vol_ok = bool(mask[-1]) if len(mask) else False

    if not vol_ok or signal == 0:
        return SizingResult(coin=coin, signal=signal, confidence=confidence,
                             realized_vol=realized_vol, base_size=0.0, leverage=0.0,
                             sma_multiplier=1.0, final_size_notional=0.0, vol_ok=vol_ok)

    base = vol_targeted_size(signal, confidence, realized_vol, target_vol, kelly_fraction)
    sized = apply_leverage(base, confidence, max_leverage)

    # apply_trend_filter requires the full price history to compute SMA over the
    # final `trend_sma` bars; we build a positions array where only the last
    # element holds our sized position and read the filtered last element back.
    pos_arr = np.zeros(len(prices))
    pos_arr[-1] = sized
    filtered = apply_trend_filter(
        pos_arr, np.asarray(prices), sma_period=trend_sma,
        multiplier=trend_multiplier,
    )
    final_size = float(filtered[-1])
    sma_mult = final_size / sized if abs(sized) > 1e-9 else 1.0
    return SizingResult(
        coin=coin, signal=signal, confidence=confidence, realized_vol=realized_vol,
        base_size=base, leverage=sized, sma_multiplier=sma_mult,
        final_size_notional=final_size, vol_ok=True,
    )
