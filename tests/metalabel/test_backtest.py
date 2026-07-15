import numpy as np
import pandas as pd
import pytest

from tradingagents.metalabel.primary import compute_votes, extract_events
from tradingagents.metalabel.labeler import triple_barrier_labels
from tradingagents.metalabel.backtest import (
    evaluate_g2, max_drawdown, portfolio_returns, replay_coin, sharpe,
    size_multiplier,
)


def _trendy(n=300, seed=5):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq="D")
    c = 100 * np.exp(np.cumsum(rng.normal(0.001, 0.03, n)))
    return pd.DataFrame({"Date": idx, "Open": c, "High": c * 1.02,
                         "Low": c * 0.98, "Close": c, "Volume": 1.0})


def test_size_multiplier_contract():
    assert size_multiplier(0.40, 0.50) == 0.0
    assert size_multiplier(0.50, 0.50) == pytest.approx(0.25)  # clip floor
    assert size_multiplier(0.70, 0.50) == pytest.approx(1.0)
    assert size_multiplier(0.95, 0.50) == 1.0


def test_replay_skip_all_equals_zero_returns():
    df = _trendy()
    votes = compute_votes(df)
    labels = triple_barrier_labels(df, extract_events(votes))
    p = pd.Series(0.0, index=labels.index)  # meta rejects everything
    rets = replay_coin(df, votes, labels, p, tau=0.5)
    assert (rets.fillna(0) == 0).all()


def test_replay_meta_all_ones_equals_primary():
    df = _trendy()
    votes = compute_votes(df)
    labels = triple_barrier_labels(df, extract_events(votes))
    prim = replay_coin(df, votes, labels, None, tau=0.5)
    p = pd.Series(1.0, index=labels.index)  # mult -> 1.0 for every event
    meta = replay_coin(df, votes, labels, p, tau=0.5)
    pd.testing.assert_series_equal(prim, meta)


def test_costs_reduce_returns():
    df = _trendy()
    votes = compute_votes(df)
    labels = triple_barrier_labels(df, extract_events(votes))
    free = replay_coin(df, votes, labels, None, tau=0.5, cost_bps_rt=0.0)
    paid = replay_coin(df, votes, labels, None, tau=0.5, cost_bps_rt=10.0)
    assert paid.sum() < free.sum()


def test_sharpe_zero_variance_is_zero():
    assert sharpe(pd.Series([0.0] * 100)) == 0.0


def test_max_drawdown_positive_fraction():
    rets = pd.Series([0.1, -0.2, 0.05, -0.1])
    dd = max_drawdown(rets)
    assert 0 < dd < 1


def test_g2_pass_on_improvement():
    rng = np.random.default_rng(1)
    idx = pd.date_range("2022-01-01", periods=400, freq="D")
    prim = pd.Series(rng.normal(0.0005, 0.02, 400), index=idx)
    meta = prim + 0.002  # strictly better
    g2 = evaluate_g2(prim, meta)
    assert g2["g2_pass"] is True
    assert g2["delta_sr"] > 0


def test_portfolio_equal_weight():
    idx = pd.date_range("2022-01-01", periods=10, freq="D")
    a = pd.Series(0.02, index=idx)
    b = pd.Series(0.00, index=idx)
    port = portfolio_returns({"a": a, "b": b})
    assert np.allclose(port.values, 0.01)
