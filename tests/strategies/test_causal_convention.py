"""Causal sizing convention: positions must not depend on the same bar's close.

Audit 2026-07-07 finding C1/F2: the legacy convention feeds close(D) into the
trend filter / vol / hold logic for the position credited with bar D's return,
which live trading (00:05 UTC, asof = D-1) structurally cannot replicate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.baseline_v5_mix import _v2_positions


def _merged(n: int = 120, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.cumprod(1 + rng.normal(0.004, 0.01, n))
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="D"),
            "Close": close,
        }
    )
    df["ref_price"] = df["Close"].shift(1).fillna(df["Close"].iloc[0])
    # always-long predictions vs ref: both horizons agree UP with 8% magnitude
    df["pred_h7"] = df["ref_price"] * 1.08
    df["pred_h14"] = df["ref_price"] * 1.08
    return df


def test_causal_last_position_ignores_same_bar_close():
    base = _merged()
    pos_a = _v2_positions(base, convention="causal")

    bumped = base.copy()
    bumped.loc[bumped.index[-1], "Close"] *= 0.65  # crash the final bar
    pos_b = _v2_positions(bumped, convention="causal")

    assert pos_a[-1] != 0.0, "warmup should be over; expected a live position"
    assert pos_b[-1] == pytest.approx(pos_a[-1])


def test_causal_costs_use_realistic_funding():
    from scripts.baseline_v5_mix import COSTS, costs_for_coin

    legacy = costs_for_coin("bitcoin")
    assert legacy["funding_rate"] == COSTS["funding_rate"]  # unchanged default

    causal = costs_for_coin("bitcoin", convention="causal")
    # 3 funding events/day at 0.01% each — not 0.01%/8
    assert causal["funding_rate"] == pytest.approx(0.0003)


def test_legacy_last_position_depends_on_same_bar_close():
    base = _merged()
    pos_a = _v2_positions(base, convention="legacy")

    bumped = base.copy()
    bumped.loc[bumped.index[-1], "Close"] *= 0.65
    pos_b = _v2_positions(bumped, convention="legacy")

    assert pos_a[-1] != pytest.approx(pos_b[-1])
