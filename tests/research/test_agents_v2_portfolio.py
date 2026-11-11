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


def test_realized_funding_and_book_cost(tmp_path):
    import pandas as pd
    from tradingagents.agents_v2.portfolio_eval import book_returns, realized_funding
    f = pd.Timestamp("2024-01-05", tz="UTC")
    times = pd.date_range("2024-01-04", "2024-01-14", freq="8h", tz="UTC")
    pd.DataFrame({"fundingTime": times, "fundingRate": 0.0001}).to_parquet(tmp_path / "AAAUSDT.parquet")
    fund = realized_funding(["AAAUSDT", "MISSING"], [f], funding_dir=tmp_path)
    assert list(fund["symbol"]) == ["AAAUSDT"] and fund.iloc[0]["n_settlements"] == 21   # 7 days x 3 settlements
    assert abs(fund.iloc[0]["funding_week"] - 0.0021) < 1e-12
    fwd = pd.DataFrame({"date": [f], "symbol": ["AAAUSDT"], "fwd_ret": [0.0]})
    r0 = book_returns({f: {"AAAUSDT": 0.1}}, fwd, cost_per_side=0.0)
    r1 = book_returns({f: {"AAAUSDT": 0.1}}, fwd, cost_per_side=0.0, funding=fund)
    assert abs((r0 - r1).iloc[0] - 0.1 * 0.0021) < 1e-12                                   # long pays funding


def test_funding_window_excludes_entry_settlement_and_includes_exit_settlement(tmp_path):
    """The position opens at the close of the Friday bar (Friday 00:00 + 1 day) and closes seven days later. Each
    settlement carries a distinct rate, so a window shifted by one settlement or by one day changes the sum; the
    stamps carry the exchange's millisecond jitter on both sides of the boundary."""
    from tradingagents.agents_v2.portfolio_eval import realized_funding
    f = pd.Timestamp("2024-01-05", tz="UTC")
    times = pd.date_range("2024-01-04", "2024-01-15", freq="8h", tz="UTC")
    rates = pd.Series([10.0 ** -(3 + i % 3) * (1 + i) for i in range(len(times))], index=times)
    entry, exit_ = f + pd.Timedelta(days=1), f + pd.Timedelta(days=8)
    expected = float(rates[(times > entry) & (times <= exit_)].sum())
    for jitter_ms in (0, 7, -7):
        stamps = times + pd.Timedelta(milliseconds=jitter_ms)
        pd.DataFrame({"fundingTime": stamps, "fundingRate": rates.to_numpy()}).to_parquet(tmp_path / "AAAUSDT.parquet")
        fund = realized_funding(["AAAUSDT"], [f], funding_dir=tmp_path)
        assert fund.iloc[0]["n_settlements"] == 21 and abs(fund.iloc[0]["funding_week"] - expected) < 1e-15, jitter_ms
    assert abs(expected - float(rates[(times >= entry) & (times < exit_)].sum())) > 1e-6     # entry-inclusive window differs
    unshifted = realized_funding(["AAAUSDT"], [f], funding_dir=tmp_path, offset_days=0)      # the window of the first attempt
    assert abs(unshifted.iloc[0]["funding_week"] - expected) > 1e-6


def test_headline_sharpe_is_net_of_funding_and_placebos_use_the_same_basis():
    from tradingagents.agents_v2.portfolio_eval import book_components, placebo_pvalues
    weights, fwd = _data(1.0)
    long_only = {d: {s: abs(v) for s, v in w.items()} for d, w in weights.items()}          # funding does not net out
    rng = np.random.default_rng(5)
    fund = fwd[["date", "symbol"]].assign(funding_week=rng.normal(0.004, 0.004, len(fwd)))
    funded, plain = summarize_book(long_only, fwd, funding=fund, n_placebo=50), summarize_book(long_only, fwd, n_placebo=50)
    assert funded["funded"] and not plain["funded"]
    assert funded["sharpe"] == sharpe(book_returns(long_only, fwd, funding=fund)) == funded["placebo_basis_sharpe"]
    assert funded["sharpe_costs_no_funding"] == plain["sharpe"] == sharpe(book_returns(long_only, fwd))
    assert funded["sharpe"] < funded["sharpe_costs_no_funding"] < funded["sharpe_before_costs"]
    assert funded["sum_funding_pct"] > 0 and plain["sum_funding_pct"] == 0.0
    comp = book_components(long_only, fwd, funding=fund)
    assert np.allclose(comp["net"], comp["gross"] - comp["cost"] - comp["funding"]) and comp["missing_returns"].sum() == 0
    assert placebo_pvalues(long_only, fwd, n=50, funding=fund)["sharpe"] == funded["sharpe"]


def test_placebo_p_is_never_zero_and_missing_returns_are_counted():
    from tradingagents.agents_v2.portfolio_eval import book_components
    weights, fwd = _data(3.0)
    s = summarize_book(weights, fwd, n_placebo=40)
    assert s["p_date_shuffle"] == s["p_asset_shuffle"] == 1 / 41                           # (1 + 0) / (n + 1)
    first = min(weights)
    holed = fwd[~((fwd["date"] == first) & (fwd["symbol"].isin(["S0", "S1"])))]
    comp = book_components(weights, holed)
    assert comp.loc[first, "missing_returns"] == 2 and comp["missing_returns"].sum() == 2
    flat = summarize_book({d: {s: 0.0 for s in w} for d, w in weights.items()}, fwd, n_placebo=10)
    assert np.isnan(flat["sharpe"]) and flat["p_date_shuffle"] is None and flat["psr_vs_zero"] is None   # no variance, no p-value


def test_probabilistic_sharpe_bounds():
    from tradingagents.agents_v2.portfolio_eval import probabilistic_sharpe
    rng = np.random.default_rng(1)
    good, bad = pd.Series(rng.normal(0.01, 0.02, 60)), pd.Series(rng.normal(-0.01, 0.02, 60))
    assert 0.99 < probabilistic_sharpe(good) <= 1.0 and 0.0 <= probabilistic_sharpe(bad) < 0.01
    assert probabilistic_sharpe(good) > probabilistic_sharpe(good, benchmark_annual=2.0)
    assert probabilistic_sharpe(good.iloc[:7]) is None and probabilistic_sharpe(pd.Series([0.01] * 20)) is None
