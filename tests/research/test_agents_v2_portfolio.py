from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tradingagents.agents_v2.portfolio_eval import book_returns, sharpe, summarize_book  # noqa: E402


def _data(signal, seed=0, weeks=52, n=20):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2022-01-07", periods=weeks, freq="W-FRI", tz="UTC")
    rows, weights = [], {}
    for d in dates:
        latent = rng.normal(size=n)
        rets = 0.03 * latent * signal + 0.05 * rng.normal(size=n)
        syms = [f"S{i}" for i in range(n)]
        rows += [{"date": d, "symbol": s, "fwd_ret": r} for s, r in zip(syms, rets)]
        w = latent / np.abs(latent).sum()
        weights[d] = dict(zip(syms, w))
    return weights, pd.DataFrame(rows)


def test_book_returns_costs_and_sharpe():
    weights, fwd = _data(1.0)
    r = book_returns(weights, fwd)
    assert len(r) == 52 and sharpe(r) > 2
    r0 = book_returns(weights, fwd, cost_per_side=0.0)
    assert (r0 >= r).all()                      # costs only reduce returns


def test_placebos_separate_signal_from_noise():
    weights, fwd = _data(1.0)
    s = summarize_book(weights, fwd)
    assert s["p_date_shuffle"] < 0.05 and s["p_asset_shuffle"] < 0.05 and "2022" in s["by_year"]
    weights0, fwd0 = _data(0.0, seed=3)
    s0 = summarize_book(weights0, fwd0)
    assert s0["p_asset_shuffle"] > 0.05
