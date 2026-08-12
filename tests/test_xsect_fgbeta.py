import numpy as np
import pandas as pd
import pytest
from tradingagents.xsect.fgbeta import exclude_extreme_quintiles, fg_beta, middle_quintile


def _mk(n=200, seed=0, beta=0.0):
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    rng = np.random.default_rng(seed)
    dfg = pd.Series(rng.normal(0, 5, n), index=idx)
    noise = rng.normal(0, 0.001, n)
    ret = beta * dfg / 100.0 + noise
    price = 100 * np.exp(np.cumsum(ret))
    kl = pd.DataFrame({"open": price, "high": price, "low": price, "close": price,
                       "quote_volume": 1e7}, index=idx)
    fng = 50 + dfg.cumsum().clip(-45, 45)
    return kl, fng


def test_beta_recovers_sign_and_causality():
    kl, fng = _mk(beta=2.0)
    d = kl.index[-1]
    b = fg_beta({"A": kl}, fng, ["A"], d)
    # NOTE: _mk's ret = beta * dfg / 100.0 + noise, so the true OLS slope of
    # ret on raw (unscaled) dfg is beta/100 = 0.02, not beta itself (0.5+
    # threshold in the original brief draft assumed a 1:1 recovery, which is
    # not how the /100 scaling works). Empirically verified: beta=0.0 (no
    # signal) recovers ~4e-5, beta=2.0 recovers ~0.0209 — 0.01 cleanly
    # discriminates signal from noise while matching the actual math.
    assert b["A"] > 0.01  # strongly positive beta recovered (2 orders of magnitude above noise floor)
    # causality: changing the last day's fng/price must not change beta at d...
    kl2 = kl.copy(); kl2.iloc[-1, kl2.columns.get_loc("close")] *= 2.0
    fng2 = fng.copy(); fng2.iloc[-1] = 90.0
    b2 = fg_beta({"A": kl2}, fng2, ["A"], d)
    assert b2["A"] == pytest.approx(b["A"], rel=1e-9)


def test_min_obs_gate():
    kl, fng = _mk(n=50)
    assert fg_beta({"A": kl}, fng, ["A"], kl.index[-1]) == {}


def test_quintile_helpers():
    betas = {f"S{i}": float(i) for i in range(10)}  # 0..9
    mid = middle_quintile(betas)
    assert mid == ["S4", "S5"]
    kept = exclude_extreme_quintiles(betas, [f"S{i}" for i in range(10)])
    assert "S0" not in kept and "S9" not in kept and "S4" in kept
