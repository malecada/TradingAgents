from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.predlab import xsec


def _panel(n_days=120, n_syms=40, seed=0, planted=0.0):
    """Panel of daily returns; optional planted momentum (signal predicts y)."""
    rng = np.random.default_rng(seed)
    days = pd.date_range("2022-01-01", periods=n_days, freq="D", tz="UTC")
    sig = rng.normal(0, 1, (n_days, n_syms))
    noise = rng.normal(0, 1, (n_days, n_syms))
    y = planted * sig + noise  # y[d] correlates with sig[d] (already aligned/lagged)
    return (pd.DataFrame(y, index=days, columns=[f"S{i}" for i in range(n_syms)]),
            pd.DataFrame(sig, index=days, columns=[f"S{i}" for i in range(n_syms)]))


def test_daily_spearman_ic_known_case():
    y = pd.DataFrame({"A": [1.0, 3.0], "B": [2.0, 2.0], "C": [3.0, 1.0]},
                     index=pd.date_range("2022-01-01", periods=2, freq="D", tz="UTC")).T
    sig = y.copy()
    ics = xsec.daily_ic(sig.T, y.T, min_breadth=2)
    assert np.allclose(ics.to_numpy(), [1.0, 1.0])
    ics_inv = xsec.daily_ic(-sig.T, y.T, min_breadth=2)
    assert np.allclose(ics_inv.to_numpy(), [-1.0, -1.0])


def test_ic_summary_planted_signal_detected():
    y, sig = _panel(planted=0.15)
    ics = xsec.daily_ic(sig, y)
    s = xsec.ic_summary(ics, nw_lag=5)
    assert s["mean_ic"] > 0.05
    assert s["nw_t"] > 3.0


def test_ic_summary_null_on_noise():
    y, sig = _panel(planted=0.0, seed=3)
    s = xsec.ic_summary(xsec.daily_ic(sig, y), nw_lag=5)
    assert abs(s["mean_ic"]) < 0.05
    assert abs(s["nw_t"]) < 2.5


def test_min_breadth_filter():
    y, sig = _panel(n_syms=10)
    y.iloc[5, :8] = np.nan  # day 5 has only 2 names
    ics = xsec.daily_ic(sig, y, min_breadth=5)
    assert pd.isna(ics.iloc[5])
    assert ics.drop(ics.index[5]).notna().all()
