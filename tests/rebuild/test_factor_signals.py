"""Causality unit tests for the model-free factor floor signal builders.

Every signal value at index t must be computable from data up to index t-1
only. These tests assert that property directly: a spike injected at the last
index must not change that index's own signal.
"""
import numpy as np

from scripts.factor_baselines import (
    donchian_signal,
    ma_cross_signal,
    tsmom_signal,
)


# ── Brief tests (VERBATIM) ────────────────────────────────────────────────
def test_tsmom_uses_only_past():
    closes = np.array([100.0] * 40)
    closes[-1] = 200.0  # today's spike must not affect today's signal
    sig = tsmom_signal(closes, k=7)
    assert sig[-1] == tsmom_signal(np.array([100.0] * 40), k=7)[-1]


def test_ma_cross_shapes_and_warmup():
    closes = np.linspace(100, 200, 300)
    sig = ma_cross_signal(closes, fast=10, slow=50)
    assert sig.shape == closes.shape
    assert (sig[:50] == 0).all()      # warm-up neutral
    assert (sig[60:] == 1).all()      # steady uptrend -> long


# ── Additional Donchian causality test (same style) ───────────────────────
def test_donchian_uses_only_past():
    rng = np.random.default_rng(0)
    highs = 100.0 + np.cumsum(rng.normal(0.0, 1.0, 120))
    lows = highs - 2.0
    closes = highs - 1.0

    highs2, lows2, closes2 = highs.copy(), lows.copy(), closes.copy()
    # Inject a large spike at the final bar; it must not move sig[-1].
    highs2[-1] += 50.0
    lows2[-1] += 50.0
    closes2[-1] += 50.0

    s1 = donchian_signal(highs, lows, closes, n=20)
    s2 = donchian_signal(highs2, lows2, closes2, n=20)
    assert s1[-1] == s2[-1]
