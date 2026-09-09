"""Lead-0 (2026-09-02) convention fix: PnL steps consume SIMPLE returns.

Pins:
  * round-trip short — a full short over a doubling-then-halving path loses
    money under simple booking and books exactly 0 under log booking (the
    fake short edge of AUDIT_BACKTEST_2026-08-24 / AUDIT_RESEARCH_PROGRAM_2026-09-02);
  * fast weekly engine == reference engine bar-for-bar under both conventions;
  * build_matrices(with_simple=True) returns expm1 of the log matrix;
  * (slow, data-gated) the fixed engines reproduce the Sep-2 forensic simple
    numbers on the real dev window to 1e-6.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.portfolio import (
    build_fast_arrays, fast_weekly_portfolio, returns_from_close,
    run_weekly_portfolio, sr,
)
from tradingagents.xsect.trend import build_matrices, run_daily_portfolio

FORENSIC = Path("/home/malecada/master_thesis/data/audit_2026-09-02/convswap_results.json")


def _kl(prices, first="2021-01-01"):
    idx = pd.date_range(first, periods=len(prices), freq="D", tz="UTC")
    p = pd.Series(prices, index=idx, dtype=float)
    return pd.DataFrame({"open": p, "high": p, "low": p, "close": p, "quote_volume": 1e7})


def test_returns_from_close_conventions():
    close = pd.Series([100.0, 200.0, 100.0],
                      index=pd.date_range("2021-01-01", periods=3, freq="D", tz="UTC"))
    simple = returns_from_close(close, "simple")
    log = returns_from_close(close, "log")
    assert simple.iloc[1] == pytest.approx(1.0) and simple.iloc[2] == pytest.approx(-0.5)
    assert log.iloc[1] == pytest.approx(np.log(2)) and log.iloc[2] == pytest.approx(-np.log(2))
    with pytest.raises(ValueError):
        returns_from_close(close, "arith")


def test_round_trip_short_pin_simple_loses_log_books_zero():
    """Short 100% over +100% then -50%: true PnL = -1.0 + 0.5 = -0.5 (arithmetic
    daily booking). Log booking gives -(log 2) - (log 0.5) = 0 — the fake edge."""
    days = pd.date_range("2021-01-01", periods=3, freq="D", tz="UTC")
    close = pd.Series([100.0, 200.0, 100.0], index=days)
    R_simple = pd.DataFrame({"A": returns_from_close(close, "simple")})
    R_log = pd.DataFrame({"A": returns_from_close(close, "log")})
    W = pd.DataFrame({"A": [-1.0, -1.0, -1.0]}, index=days)
    assert run_daily_portfolio(W, R_simple, cost_bps=0.0).sum() == pytest.approx(-0.5)
    assert run_daily_portfolio(W, R_log, cost_bps=0.0).sum() == pytest.approx(0.0)


def test_round_trip_long_half_weight():
    """Half-weight long over -50% then +100%: simple books +0.25, log books 0."""
    days = pd.date_range("2021-01-01", periods=3, freq="D", tz="UTC")
    close = pd.Series([100.0, 50.0, 100.0], index=days)
    W = pd.DataFrame({"A": [0.5, 0.5, 0.5]}, index=days)
    s = run_daily_portfolio(W, pd.DataFrame({"A": returns_from_close(close, "simple")}), 0.0)
    l = run_daily_portfolio(W, pd.DataFrame({"A": returns_from_close(close, "log")}), 0.0)
    assert s.sum() == pytest.approx(0.25) and l.sum() == pytest.approx(0.0)


def test_weekly_engine_default_is_simple():
    up = [100.0 * 1.01 ** i for i in range(10)]
    kl = {"A": _kl(up)}
    reb = pd.DatetimeIndex([kl["A"].index[0]])
    series = run_weekly_portfolio(kl, reb, lambda t: ["A"], cost_bps=0.0)
    assert series.iloc[0] == pytest.approx(0.01, rel=1e-9)
    series_log = run_weekly_portfolio(kl, reb, lambda t: ["A"], cost_bps=0.0, convention="log")
    assert series_log.iloc[0] == pytest.approx(np.log(1.01), rel=1e-9)


@pytest.mark.parametrize("convention", ["simple", "log"])
def test_fast_engine_matches_reference(convention):
    rng = np.random.default_rng(3)
    n = 120
    kl = {}
    for s in ("A", "B", "C", "D"):
        path = 100 * np.exp(np.cumsum(rng.normal(0, 0.05, n)))
        kl[s] = _kl(path)
    kl["C"] = kl["C"].iloc[:70]  # delists mid-sample
    idx = kl["A"].index
    reb = idx[idx.dayofweek == 0]
    members = {t: sorted(rng.choice(["A", "B", "C", "D"], size=2, replace=False)) for t in reb}
    ref = run_weekly_portfolio(kl, reb, lambda t: members[t], cost_bps=10.0, convention=convention)
    all_days, day_pos, R, sym_idx = build_fast_arrays(kl, convention=convention)
    fast = fast_weekly_portfolio(members, reb, all_days, day_pos, R, sym_idx, cost_bps=10.0)
    j = pd.concat([ref, fast], axis=1, join="inner")
    assert len(j) == len(ref) == len(fast)
    assert np.abs(j.iloc[:, 0] - j.iloc[:, 1]).max() < 1e-12


def test_build_matrices_with_simple():
    rng = np.random.default_rng(1)
    kl = {s: _kl(100 * np.exp(np.cumsum(rng.normal(0, 0.03, 80)))) for s in ("A", "B")}
    all_days, R, VOTES, SIGMA = build_matrices(kl, ["A", "B"])
    all_days2, R2, VOTES2, SIGMA2, RS = build_matrices(kl, ["A", "B"], with_simple=True)
    assert R.equals(R2) and all_days.equals(all_days2)
    assert np.allclose(RS.to_numpy(), np.expm1(R.to_numpy()), equal_nan=True)


@pytest.mark.slow
def test_parity_with_sep2_forensic_simple_numbers():
    """Fixed engines reproduce the Sep-2 convention-swap forensic (simple) to 1e-6."""
    repo = Path(__file__).resolve().parents[2]
    if not FORENSIC.exists() or not (repo / "data/xsect/klines/BTCUSDT.parquet").exists():
        pytest.skip("forensic results or kline store not on this machine")
    from tradingagents.xsect.portfolio import momentum_scores
    from tradingagents.xsect.universe import eligibility, load_klines, weekly_rebalance_dates

    ref = json.loads(FORENSIC.read_text())
    klines = load_klines(repo / "data/xsect/klines")
    reb = weekly_rebalance_dates("2021-01-01", "2025-03-31")
    hi = pd.Timestamp("2025-03-31", tz="UTC")
    elig = {t: eligibility(klines, t) for t in reb}
    all_days, day_pos, R, sym_idx = build_fast_arrays(klines, convention="simple")
    bench = fast_weekly_portfolio(elig, reb, all_days, day_pos, R, sym_idx, 10.0).loc[:hi]
    assert sr(bench) == pytest.approx(ref["xs_mom_p1"]["benchmark"]["simple"]["sr"], abs=1e-6)
    scores = {t: momentum_scores(klines, elig[t], t, 28, 0) for t in reb}
    top10 = {t: [s for s, _ in sorted(scores[t].items(), key=lambda kv: -kv[1])[:10]] for t in reb}
    mom = fast_weekly_portfolio(top10, reb, all_days, day_pos, R, sym_idx, 10.0).loc[:hi]
    pin = next(c for c in ref["xs_mom_p1"]["configs"] if (c["L"], c["skip"], c["K"]) == (28, 0, 10))
    assert sr(mom) == pytest.approx(pin["simple"]["sr"], abs=1e-6)
