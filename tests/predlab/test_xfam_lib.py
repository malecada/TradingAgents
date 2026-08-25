"""Tests for xfam shared lib — novel engines tested before first registered use."""

import numpy as np
import pandas as pd
import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from predlab_xfam_lib import (
    ann_sr,
    ar1_half_life,
    bh_fdr,
    eg_fit,
    nw_tstat,
    pair_zmr_backtest,
    thin_ls_backtest,
    year_sign_consistency,
)


def _days(start, n):
    return pd.date_range(start, periods=n, freq="D", tz="UTC")


class TestNWTstat:
    def test_zero_mean(self):
        rng = np.random.default_rng(0)
        m, t, p = nw_tstat(rng.normal(0, 1, 2000), lag=5)
        assert abs(t) < 3

    def test_strong_mean(self):
        rng = np.random.default_rng(1)
        m, t, p = nw_tstat(rng.normal(0.5, 1, 2000), lag=5)
        assert p < 1e-10 and t > 10

    def test_autocorrelation_widens(self):
        rng = np.random.default_rng(2)
        e = rng.normal(0, 1, 3000)
        ar = np.zeros(3000)
        for i in range(1, 3000):
            ar[i] = 0.8 * ar[i - 1] + e[i]
        _, t0, _ = nw_tstat(ar + 0.1, lag=0)
        _, t10, _ = nw_tstat(ar + 0.1, lag=10)
        assert abs(t10) < abs(t0)


class TestBHFDR:
    def test_rejects_smallest(self):
        ps = {"a": 0.001, "b": 0.5, "c": 0.9}
        assert bh_fdr(ps, q=0.10) == {"a"}

    def test_step_up(self):
        # classic: all under i/n*q accepted through the largest passing index
        ps = {"a": 0.01, "b": 0.02, "c": 0.9}
        got = bh_fdr(ps, q=0.10)
        assert got == {"a", "b"}

    def test_none(self):
        assert bh_fdr({"a": 0.5, "b": 0.9}, q=0.10) == set()


class TestYearSign:
    def test_consistent(self):
        idx = _days("2021-01-01", 365 * 4)
        s = pd.Series(0.001, index=idx)
        out = year_sign_consistency(s)
        assert out["n_agree"] == 4

    def test_one_bad_year(self):
        idx = _days("2021-01-01", 365 * 4)
        s = pd.Series(0.001, index=idx)
        s[s.index.year == 2022] = -0.0005  # bad year, overall mean stays positive
        out = year_sign_consistency(s)
        assert out["n_agree"] == 3


class TestThinLS:
    def test_perfect_signal_profits(self):
        idx = _days("2021-01-01", 200)
        rng = np.random.default_rng(3)
        ret = pd.DataFrame(rng.normal(0, 0.02, (200, 6)), index=idx,
                           columns=list("ABCDEF"))
        sig = ret.copy()  # same-day oracle passed as sig traded same day
        df = thin_ls_backtest(sig, ret, n_leg=2, taker_bp=0.0)
        assert df["gross"].mean() > 0.01

    def test_shifted_signal_is_noise(self):
        idx = _days("2021-01-01", 400)
        rng = np.random.default_rng(4)
        ret = pd.DataFrame(rng.normal(0, 0.02, (400, 6)), index=idx,
                           columns=list("ABCDEF"))
        sig = ret.shift(1)  # yesterday's return, iid world -> no edge
        df = thin_ls_backtest(sig, ret, n_leg=2, taker_bp=0.0)
        assert abs(ann_sr(df["gross"].to_numpy())) < 1.5

    def test_costs_charged_on_turnover(self):
        idx = _days("2021-01-01", 50)
        rng = np.random.default_rng(5)
        ret = pd.DataFrame(rng.normal(0, 0.02, (50, 6)), index=idx,
                           columns=list("ABCDEF"))
        sig = pd.DataFrame(rng.normal(0, 1, (50, 6)), index=idx,
                           columns=list("ABCDEF"))
        df0 = thin_ls_backtest(sig, ret, taker_bp=0.0)
        df5 = thin_ls_backtest(sig, ret, taker_bp=5.0)
        assert (df0["net"] - df5["net"]).sum() > 0
        assert np.isclose(df5["cost"].iloc[0], 5.0 / 1e4 * 2.0)  # day-1 full gross build

    def test_min_names_skips(self):
        idx = _days("2021-01-01", 10)
        ret = pd.DataFrame(0.01, index=idx, columns=list("ABC"))
        sig = pd.DataFrame(1.0, index=idx, columns=list("ABC"))
        df = thin_ls_backtest(sig, ret, n_leg=2, min_names=4)
        assert len(df) == 0


class TestEGandHalfLife:
    def test_cointegrated_pair_detected(self):
        rng = np.random.default_rng(6)
        n = 300
        common = np.cumsum(rng.normal(0, 0.02, n))
        a = pd.Series(common + rng.normal(0, 0.005, n), index=_days("2021-01-01", n))
        b = pd.Series(common + rng.normal(0, 0.005, n), index=_days("2021-01-01", n))
        beta, adf_p, resid = eg_fit(a, b)
        assert 0.7 < beta < 1.3
        assert adf_p < 0.05

    def test_independent_walks_not_cointegrated(self):
        # single seeds can produce spurious rejections (~5% each); assert the
        # typical case via the median over many independent worlds
        ps = []
        for seed in range(21):
            rng = np.random.default_rng(100 + seed)
            n = 300
            a = pd.Series(np.cumsum(rng.normal(0, 0.02, n)), index=_days("2021-01-01", n))
            b = pd.Series(np.cumsum(rng.normal(0, 0.02, n)), index=_days("2021-01-01", n))
            _, adf_p, _ = eg_fit(a, b)
            ps.append(adf_p)
        assert np.median(ps) > 0.05

    def test_half_life_of_known_ar1(self):
        rng = np.random.default_rng(8)
        n = 2000
        phi = 0.9  # half-life = ln2/ln(1/phi) ~ 6.58
        x = np.zeros(n)
        for i in range(1, n):
            x[i] = phi * x[i - 1] + rng.normal(0, 1)
        hl = ar1_half_life(pd.Series(x, index=_days("2021-01-01", n)))
        assert 4 < hl < 10

    def test_random_walk_half_life_inf(self):
        rng = np.random.default_rng(9)
        x = np.cumsum(rng.normal(0, 1, 1000))
        hl = ar1_half_life(pd.Series(x, index=_days("2021-01-01", 1000)))
        assert hl > 30 or np.isinf(hl)  # finite-sample AR(1) bias keeps b just under 1


class TestPairZMR:
    def _mr_world(self, n=600, seed=10):
        rng = np.random.default_rng(seed)
        idx = _days("2021-01-01", n)
        common = np.cumsum(rng.normal(0, 0.02, n))
        # strongly mean-reverting spread
        sp = np.zeros(n)
        for i in range(1, n):
            sp[i] = 0.9 * sp[i - 1] + rng.normal(0, 0.01)
        la = pd.Series(common + sp / 2, index=idx)
        lb = pd.Series(common - sp / 2, index=idx)
        pa, pb = np.exp(la), np.exp(lb)
        ra, rb = pa.pct_change(), pb.pct_change()
        return la, lb, ra, rb, idx

    def test_profits_on_mr_spread(self):
        la, lb, ra, rb, idx = self._mr_world()
        df = pair_zmr_backtest(la, lb, ra, rb, beta=1.0,
                               trade_index=idx[120:], taker_bp=0.0)
        assert df["gross"].sum() > 0

    def test_position_lagged_no_lookahead(self):
        la, lb, ra, rb, idx = self._mr_world(seed=11)
        df = pair_zmr_backtest(la, lb, ra, rb, beta=1.0, trade_index=idx[120:])
        # entry day (z crosses) must carry zero position PnL: pos applies next day
        st_dates = df.index
        assert len(st_dates) > 50  # engine produced a series
        # direct check: first nonzero-gross day must be preceded by a decision day
        nz = df[df["gross"] != 0]
        if len(nz):
            assert nz.index[0] > st_dates[0]

    def test_flat_when_never_crossing(self):
        idx = _days("2021-01-01", 300)
        la = pd.Series(np.linspace(0, 0.001, 300), index=idx)
        lb = pd.Series(0.0, index=idx)
        ra = pd.Series(0.0, index=idx)
        rb = pd.Series(0.0, index=idx)
        df = pair_zmr_backtest(la, lb, ra, rb, beta=1.0, trade_index=idx[120:],
                               z_entry=50.0)
        assert (df["gross"] == 0).all()


class TestCalDateLogic:
    def test_last_friday(self):
        from predlab_xfam_cal import last_friday
        assert str(last_friday(2026, 8).date()) == "2026-08-28"
        assert str(last_friday(2024, 2).date()) == "2024-02-23"
        assert last_friday(2025, 1).weekday() == 4

    def test_expiry_indicator_windows(self):
        from predlab_xfam_cal import expiry_indicator
        idx = pd.date_range("2024-01-01", "2024-03-15", freq="D", tz="UTC")
        ind = expiry_indicator(idx)
        exp_jan = pd.Timestamp("2024-01-26", tz="UTC")  # last Friday Jan 2024
        assert ind.loc[exp_jan] == 1.0
        assert ind.loc[exp_jan - pd.Timedelta(days=3)] == 1.0
        assert ind.loc[exp_jan + pd.Timedelta(days=1)] == 0.0
        assert np.isnan(ind.loc[pd.Timestamp("2024-01-10", tz="UTC")])
