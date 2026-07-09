import numpy as np
import pandas as pd

from tradingagents.rebuild.compare import paired_bootstrap


def _series(mu, n=500, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq="D")
    return pd.Series(rng.normal(mu, 0.01, n), index=idx)


def test_identical_series_p_pos_half():
    a = _series(0.0005)
    r = paired_bootstrap(a, a.copy())
    assert r["delta_sr"] == 0.0
    assert 0.4 <= r["p_pos"] <= 0.6


def test_clearly_better_arm_wins():
    a = _series(0.0, seed=1)
    b = a + 0.002  # same noise, higher mean -> paired design must detect
    r = paired_bootstrap(a, b)
    assert r["delta_sr"] > 0
    assert r["p_pos"] > 0.99


def test_deterministic_given_seed():
    a, b = _series(0.0, seed=1), _series(0.001, seed=2)
    assert paired_bootstrap(a, b) == paired_bootstrap(a, b)
