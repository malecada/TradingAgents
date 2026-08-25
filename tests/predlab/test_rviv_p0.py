"""Tests for rviv_p0 core math (charter: 2026-08-25-rviv-p0-charter.md).

Covers the F3 PIT audit (training-pair rule, no post-t data in forecasts),
target alignment, QLIKE, and the DM/HAC test.
"""

import numpy as np
import pandas as pd
import pytest

from scripts.predlab_rviv_p0 import (
    dm_test,
    expanding_pit_ols_forecast,
    qlike,
    rv30_target,
    trailing_rv,
)


def _cal_index(start, n):
    return pd.date_range(start, periods=n, freq="D", tz="UTC")


class TestRV30Target:
    def test_window_alignment_no_own_day_leak(self):
        idx = _cal_index("2024-01-01", 120)
        r = pd.Series(0.0, index=idx)
        spike_day = idx[60]
        r.loc[spike_day] = 0.10
        # min_obs relaxed so zeros count as observations
        tgt = rv30_target(r, min_obs=1)
        nonzero = tgt[tgt > 0].index
        # target at t covers t+1..t+30 => spike visible iff t in [spike-30, spike-1]
        assert nonzero.min() == spike_day - pd.Timedelta(days=30)
        assert nonzero.max() == spike_day - pd.Timedelta(days=1)
        assert tgt.loc[spike_day] == 0.0  # own day excluded

    def test_annualization_constant_vol(self):
        idx = _cal_index("2024-01-01", 200)
        r = pd.Series(0.02, index=idx)
        tgt = rv30_target(r, min_obs=25)
        expected = np.sqrt(365 * 0.02**2)
        assert np.isclose(tgt.dropna().iloc[0], expected)

    def test_min_obs_nan(self):
        idx = _cal_index("2024-01-01", 60)
        r = pd.Series(0.01, index=idx)
        r.iloc[35:] = np.nan  # tail windows lose observations
        tgt = rv30_target(r, min_obs=25)
        # at t=idx[0]: window idx[1..30] has 30 obs -> value
        assert not np.isnan(tgt.iloc[0])
        # at t=idx[20]: window idx[21..50] has 14 obs -> NaN
        assert np.isnan(tgt.iloc[20])


class TestTrailingRV:
    def test_trailing_excludes_future(self):
        idx = _cal_index("2024-01-01", 50)
        r = pd.Series(0.0, index=idx)
        r.loc[idx[40]] = 0.10
        tr = trailing_rv(r, k=5, min_obs=1)
        assert tr.loc[idx[39]] == 0.0  # spike is at 40, trailing at 39 clean
        assert tr.loc[idx[40]] > 0.0  # trailing includes own day


class TestQlike:
    def test_perfect_forecast_zero(self):
        v = np.array([0.04, 0.09])
        assert np.allclose(qlike(v, v), 0.0)

    def test_known_value(self):
        # true=0.04, pred=0.02: 2 - ln2 - 1
        got = qlike(np.array([0.04]), np.array([0.02]))
        assert np.isclose(got[0], 2 - np.log(2) - 1)

    def test_penalizes_under_prediction_more(self):
        assert qlike(np.array([0.04]), np.array([0.02]))[0] > qlike(
            np.array([0.04]), np.array([0.08])
        )[0]


class TestDMTest:
    def test_zero_diff_p_one(self):
        l1 = np.ones(200)
        stat, p = dm_test(l1, l1.copy(), lag=30)
        assert p == pytest.approx(1.0)

    def test_detects_large_shift(self):
        rng = np.random.default_rng(0)
        base = rng.normal(1.0, 0.1, 500)
        stat, p = dm_test(base, base + 1.0, lag=30)
        assert p < 1e-6 and stat < 0  # first series much smaller loss

    def test_hac_widens_ci_under_autocorrelation(self):
        rng = np.random.default_rng(1)
        e = rng.normal(0, 1, 800)
        ar = np.zeros(800)
        for i in range(1, 800):
            ar[i] = 0.9 * ar[i - 1] + e[i]
        d = ar + 0.05
        stat0, _ = dm_test(d + 1.0, np.ones(800), lag=0)
        stat30, _ = dm_test(d + 1.0, np.ones(800), lag=30)
        assert abs(stat30) < abs(stat0)


class TestExpandingPITOLS:
    def _panel(self, n=900):
        idx = _cal_index("2021-01-01", n)
        rng = np.random.default_rng(2)
        x = pd.Series(rng.uniform(0.2, 1.0, n), index=idx)
        y = 0.5 + 0.8 * x + pd.Series(rng.normal(0, 0.05, n), index=idx)
        return x.to_frame("x"), y

    def test_pit_training_pair_rule(self):
        X, y = self._panel()
        eval_idx = X.index[500:520]
        pred, last_train = expanding_pit_ols_forecast(
            X, y, eval_idx, gap_days=30, min_train=365, return_last_train=True
        )
        for t in eval_idx:
            assert last_train[t] + pd.Timedelta(days=30) <= t  # F3 audit

    def test_min_train_gate(self):
        X, y = self._panel()
        early = X.index[100:102]  # only ~70 completed pairs available
        pred = expanding_pit_ols_forecast(X, y, early, gap_days=30, min_train=365)
        assert pred.isna().all()

    def test_recovers_linear_relation(self):
        X, y = self._panel()
        eval_idx = X.index[700:750]
        pred = expanding_pit_ols_forecast(X, y, eval_idx, gap_days=30, min_train=365)
        err = (pred - y.loc[eval_idx]).abs().mean()
        assert err < 0.1

    def test_forecast_ignores_future_target_values(self):
        X, y = self._panel()
        eval_idx = X.index[700:705]
        base = expanding_pit_ols_forecast(X, y, eval_idx, gap_days=30, min_train=365)
        y2 = y.copy()
        cutoff = eval_idx[0] - pd.Timedelta(days=30)
        y2.loc[y2.index > cutoff] = 999.0  # corrupt everything not legally trainable at first eval day
        alt = expanding_pit_ols_forecast(X, y2, eval_idx[:1], gap_days=30, min_train=365)
        assert np.isclose(base.iloc[0], alt.iloc[0])
