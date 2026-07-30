from __future__ import annotations

import numpy as np

from tradingagents.predlab import direction


def test_pt_size_under_independence():
    rng = np.random.default_rng(2)
    rejections = 0
    n_sims = 400
    for _ in range(n_sims):
        y = rng.normal(size=250) > 0
        x = rng.normal(size=250) > 0
        r = direction.pt_test(y, x)
        if (not r.degenerate) and r.pvalue < 0.05:
            rejections += 1
    assert 0.02 < rejections / n_sims < 0.09  # ~5% size under the null


def test_pt_power_on_informative_signal():
    rng = np.random.default_rng(3)
    lat = rng.normal(size=2000)
    y = (lat + rng.normal(0, 1.2, 2000)) > 0
    x = lat > 0
    r = direction.pt_test(y, x)
    assert r.pvalue < 1e-6 and r.stat > 5


def test_pt_accepts_sign_arrays():
    rng = np.random.default_rng(6)
    y = np.sign(rng.normal(size=500))
    r_signs = direction.pt_test(y, y)  # perfect agreement
    assert (not r_signs.degenerate) and r_signs.stat > 5


def test_pt_degenerate_constant_forecast():
    y = np.random.default_rng(4).normal(size=100) > 0
    r = direction.pt_test(y, np.ones(100, dtype=bool))
    assert r.degenerate and np.isnan(r.stat)


def test_hit_rate_base_rate_guard():
    y = np.array([1, 1, 1, 1, -1])  # base rate 0.8 up
    x = np.ones(5)
    out = direction.hit_rate_vs_base(y, x)
    assert np.isclose(out["acc"], 0.8)
    assert np.isclose(out["base_rate"], 0.8)
    assert np.isclose(out["edge_pp"], 0.0)


def test_brier_skill_positive_for_informative_probabilities():
    rng = np.random.default_rng(12)
    p_true = np.clip(rng.beta(2, 2, 3000), 0.01, 0.99)
    y = (rng.random(3000) < p_true).astype(float)
    clim = np.full(3000, y.mean())
    skill_perfect = direction.brier_skill(p_true, y, clim)
    skill_clim = direction.brier_skill(clim, y, clim)
    assert skill_perfect > 0.05
    assert np.isclose(skill_clim, 0.0)
