from __future__ import annotations

import numpy as np
from statsmodels.regression.linear_model import OLS

from tradingagents.predlab import meanstats


def test_nw_matches_statsmodels_hac():
    rng = np.random.default_rng(7)
    x = rng.normal(0.1, 1.0, 400) + np.r_[0.0, rng.normal(0, 0.5, 399)]
    lag = 5
    ours = meanstats.nw_tstat(x, lag=lag)
    # use_correction=False: reference for the plain Bartlett-kernel formula
    # (we implement the uncorrected estimator; correction is a scale factor)
    sm = (
        OLS(x, np.ones_like(x))
        .fit(cov_type="HAC", cov_kwds={"maxlags": lag, "use_correction": False})
        .tvalues[0]
    )
    assert np.isclose(ours, sm, rtol=1e-6)


def test_nw_lag_zero_is_plain_tstat():
    rng = np.random.default_rng(1)
    x = rng.normal(0.3, 1.0, 250)
    ours = meanstats.nw_tstat(x, lag=0)
    plain = x.mean() / np.sqrt(x.var(ddof=0) / len(x))
    assert np.isclose(ours, plain, rtol=1e-9)


def test_nw_short_series_nan():
    assert np.isnan(meanstats.nw_tstat(np.array([1.0, 2.0, 3.0]), lag=1))


def test_bootstrap_p_pos_extremes():
    rng = np.random.default_rng(0)
    up = rng.normal(1.0, 0.1, 300)
    dn = rng.normal(-1.0, 0.1, 300)
    assert meanstats.p_pos(up, n_boot=500, seed=1) > 0.99
    assert meanstats.p_pos(dn, n_boot=500, seed=1) < 0.01


def test_bootstrap_deterministic_under_seed():
    x = np.random.default_rng(3).normal(0, 1, 200)
    a = meanstats.stationary_bootstrap_means(x, n_boot=50, seed=42)
    b = meanstats.stationary_bootstrap_means(x, n_boot=50, seed=42)
    assert np.array_equal(a, b)
    assert len(a) == 50


def test_bootstrap_means_center_near_sample_mean():
    x = np.random.default_rng(5).normal(0.5, 1.0, 400)
    means = meanstats.stationary_bootstrap_means(x, n_boot=2000, mean_block=21, seed=2)
    assert abs(means.mean() - x.mean()) < 0.05
