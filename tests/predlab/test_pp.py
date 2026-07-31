"""Phase-P engine pins: weights, costs, funding sign, vol-target, DSR."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tradingagents.predlab import pp


def _mkidx(n, freq="D"):
    return pd.date_range("2024-01-01", periods=n, freq=freq, tz="UTC")


class TestQuintileWeights:
    def test_legs_sum_and_sign(self):
        s = pd.Series(np.arange(100, dtype=float), index=[f"S{i}" for i in range(100)])
        for weighting in ("eq", "rank"):
            w = pp.quintile_weights(s, weighting)
            assert w[w > 0].sum() == pytest.approx(1.0)
            assert w[w < 0].sum() == pytest.approx(-1.0)
            # low signal = long, high signal = short
            assert w["S0"] > 0 and w["S99"] < 0
            assert (w != 0).sum() == 40

    def test_rank_conviction_ordering(self):
        s = pd.Series(np.arange(50, dtype=float), index=[f"S{i}" for i in range(50)])
        w = pp.quintile_weights(s, "rank")
        assert w["S0"] > w["S9"] > 0          # strongest long at lowest signal
        assert w["S49"] < w["S40"] < 0        # strongest short at highest signal

    def test_too_few_names_empty(self):
        s = pd.Series(np.arange(10, dtype=float), index=[f"S{i}" for i in range(10)])
        assert len(pp.quintile_weights(s, "eq")) == 0


class TestS1:
    def _panels(self, n_days=60, n_sym=50, seed=0):
        rng = np.random.default_rng(seed)
        idx = _mkidx(n_days)
        syms = [f"S{i}" for i in range(n_sym)]
        sig = pd.DataFrame(rng.normal(size=(n_days, n_sym)), index=idx, columns=syms)
        ret = pd.DataFrame(rng.normal(0, 0.02, size=(n_days, n_sym)), index=idx, columns=syms)
        uni = pd.DataFrame(True, index=idx, columns=syms)
        return sig, ret, uni

    def test_cost_reduces_net(self):
        sig, ret, uni = self._panels()
        r = pp.run_s1(sig, ret, uni, None, "eq", 1, "2024-01-01", "2024-12-31")
        assert (r["rets"]["net"] <= r["rets"]["gross"] + 1e-12).all()
        assert r["avg_turnover"] > 0

    def test_funding_sign(self):
        # all-long-leg symbols pay positive funding -> carry negative for longs
        sig, ret, uni = self._panels()
        fund = pd.DataFrame(0.001, index=sig.index, columns=sig.columns)
        r0 = pp.run_s1(sig, ret, uni, None, "eq", 1, "2024-01-01", "2024-12-31")
        r1 = pp.run_s1(sig, ret, uni, fund, "eq", 1, "2024-01-01", "2024-12-31")
        # symmetric LS book: long pays, short receives equally -> carry ~ 0
        assert abs(r1["rets"]["carry"].sum()) < 1e-10
        long_only_fund = fund.where(sig.rank(axis=1, pct=True) < 0.5, 0.0)
        r2 = pp.run_s1(sig, ret, uni, long_only_fund, "eq", 1,
                       "2024-01-01", "2024-12-31")
        assert r2["rets"]["carry"].sum() < 0  # only longs charged

    def test_smoothing_lowers_turnover(self):
        sig, ret, uni = self._panels()
        t1 = pp.run_s1(sig, ret, uni, None, "eq", 1, "2024-01-01", "2024-12-31")
        t5 = pp.run_s1(sig, ret, uni, None, "eq", 5, "2024-01-01", "2024-12-31")
        assert t5["avg_turnover"] < t1["avg_turnover"]

    def test_planted_alpha_recovered(self):
        # returns = -signal (negative IC by construction) -> LS book profits
        rng = np.random.default_rng(1)
        idx = _mkidx(120)
        syms = [f"S{i}" for i in range(60)]
        sig = pd.DataFrame(rng.normal(size=(120, 60)), index=idx, columns=syms)
        ret = -0.01 * sig + rng.normal(0, 0.001, size=(120, 60))
        uni = pd.DataFrame(True, index=idx, columns=syms)
        r = pp.run_s1(sig, pd.DataFrame(ret, index=idx, columns=syms), uni,
                      None, "eq", 1, "2024-01-01", "2024-12-31")
        assert r["sr_net"] > 3.0


class TestS2:
    def test_position_cap_and_te(self):
        idx = _mkidx(300)
        # tiny variance forecast would imply huge leverage -> cap binds
        var = pd.Series(1e-8, index=idx)
        ret = pd.Series(np.random.default_rng(0).normal(0, 0.01, 300), index=idx)
        r = pp.run_s2(var, ret)
        assert r["avg_pos"] == pytest.approx(3.0)

    def test_perfect_forecast_hits_target(self):
        rng = np.random.default_rng(2)
        idx = _mkidx(600)
        true_sig_d = 0.30 / np.sqrt(pp.ANN_DAYS)  # constant 30% ann vol
        ret = pd.Series(rng.normal(0, true_sig_d, 600), index=idx)
        var = pd.Series(true_sig_d ** 2, index=idx)
        r = pp.run_s2(var, ret, target_ann=0.20)
        realized = float(r["rets"].std() * np.sqrt(pp.ANN_DAYS))
        assert abs(realized - 0.20) < 0.03
        assert r["tracking_err"] < 0.06


class TestS3:
    def test_flat_when_below_threshold(self):
        idx = _mkidx(200, freq="h")
        prob = pd.Series(0.4, index=idx)
        ret = pd.Series(0.01, index=idx)
        r = pp.run_s3(prob, ret, 0.5, 1)
        assert r["time_in_mkt"] == 0.0
        assert abs(r["rets"].sum()) < 1e-12

    def test_flip_costs_charged(self):
        idx = _mkidx(4, freq="h")
        prob = pd.Series([0.9, 0.1, 0.9, 0.1], index=idx)
        ret = pd.Series(0.0, index=idx)
        r = pp.run_s3(prob, ret, 0.5, 1)
        # entry from flat + 3 flips = 4 position changes charged
        assert r["rets"].sum() == pytest.approx(-4 * pp.TAKER_BP / 1e4)


class TestStats:
    def test_placebo_pvalue_ranks(self):
        assert pp.placebo_pvalue(2.0, [0.0] * 99) == pytest.approx(1 / 100)
        assert pp.placebo_pvalue(-1.0, [0.0] * 99) == pytest.approx(1.0)

    def test_dsr_orders_sensibly(self):
        rng = np.random.default_rng(3)
        rets = rng.normal(0.001, 0.01, 800)
        strong = pp.dsr(3.0, [3.0, 0.2, -0.1, 0.5], 800, rets)
        weak = pp.dsr(0.3, [0.3, 0.2, -0.1, 0.5], 800, rets)
        assert strong > 0.9 > weak
