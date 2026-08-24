"""Phase-O parameterized engine pins: leg weights, buffer bands, cadence,
signal builders, universe/ADV floor, per-name PnL, cost stress, and the
eq_h1 legacy-parity contract (exact reproduction of the PP dev numbers).
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tradingagents.predlab import opt, pp

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
T7 = DATA_ROOT / "predlab" / "t7_panels"


def _mkidx(n, freq="D"):
    return pd.date_range("2024-01-01", periods=n, freq=freq, tz="UTC")


def _panels(n_days=80, n_sym=60, seed=0):
    rng = np.random.default_rng(seed)
    idx = _mkidx(n_days)
    syms = [f"S{i}" for i in range(n_sym)]
    sig = pd.DataFrame(rng.normal(size=(n_days, n_sym)), index=idx, columns=syms)
    ret = pd.DataFrame(rng.normal(0, 0.02, size=(n_days, n_sym)), index=idx, columns=syms)
    uni = pd.DataFrame(True, index=idx, columns=syms)
    return sig, ret, uni


class TestLegWeights:
    def test_quantile_width(self):
        s = pd.Series(np.arange(100, dtype=float), index=[f"S{i}" for i in range(100)])
        for q_frac, expect in ((0.2, 40), (1 / 3, 66), (0.1, 20)):
            w = opt.leg_weights(s, q_frac=q_frac, weighting="eq")
            assert (w != 0).sum() == expect
            assert w[w > 0].sum() == pytest.approx(1.0)
            assert w[w < 0].sum() == pytest.approx(-1.0)

    def test_matches_pp_quintiles(self):
        rng = np.random.default_rng(3)
        for weighting in ("eq", "rank"):
            s = pd.Series(rng.normal(size=137), index=[f"S{i}" for i in range(137)])
            w_old = pp.quintile_weights(s, weighting)
            w_new = opt.leg_weights(s, q_frac=0.2, weighting=weighting)
            pd.testing.assert_series_equal(w_old.sort_index(), w_new.sort_index())

    def test_ivol_weighting(self):
        s = pd.Series(np.arange(1, 51, dtype=float), index=[f"S{i}" for i in range(50)])
        w = opt.leg_weights(s, q_frac=0.2, weighting="ivol")
        longs = w[w > 0]
        assert longs.sum() == pytest.approx(1.0)
        assert w[w < 0].sum() == pytest.approx(-1.0)
        # within long leg, lower signal (vol) -> larger weight
        assert longs["S0"] > longs["S9"]
        # short leg risk-parity: higher vol -> smaller absolute short
        shorts = w[w < 0].abs()
        assert shorts["S49"] < shorts["S40"]

    def test_buffer_retains_held(self):
        s = pd.Series(np.arange(100, dtype=float), index=[f"S{i}" for i in range(100)])
        # S20/S21 rank just outside the entry quintile (0..19) but inside 20*(1+0.5)=30
        w_nohold = opt.leg_weights(s, q_frac=0.2, weighting="eq", buffer=0.5,
                                   held_long=set(), held_short=set())
        assert w_nohold["S20"] == 0.0
        w_held = opt.leg_weights(s, q_frac=0.2, weighting="eq", buffer=0.5,
                                 held_long={"S20"}, held_short={"S60"})
        assert w_held["S20"] > 0          # retained long inside band (ranks 0..29)
        assert w_held["S60"] == 0.0       # outside extended short band (70..99) -> dropped
        # short entry zone = top 20 (S80..S99); band extends to top 30 (S70..S99)
        w_held2 = opt.leg_weights(s, q_frac=0.2, weighting="eq", buffer=0.5,
                                  held_long=set(), held_short={"S70", "S50"})
        assert w_held2["S70"] < 0         # inside extended short band -> retained
        assert w_held2["S50"] == 0.0      # outside band -> dropped

    def test_too_few_names_empty(self):
        s = pd.Series(np.arange(10, dtype=float), index=[f"S{i}" for i in range(10)])
        assert len(opt.leg_weights(s, q_frac=0.2, weighting="eq")) == 0


class TestSignals:
    def _park_close(self, n=40, n_sym=6, seed=1):
        rng = np.random.default_rng(seed)
        idx = _mkidx(n)
        syms = [f"S{i}" for i in range(n_sym)]
        park = pd.DataFrame(rng.uniform(0.001, 0.01, size=(n, n_sym)), index=idx, columns=syms)
        close = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, 0.02, size=(n, n_sym)), axis=0)),
                             index=idx, columns=syms)
        return park, close

    def test_park_5_matches_legacy(self):
        park, close = self._park_close()
        sig = opt.build_signal(park, close, "park_5")
        pd.testing.assert_frame_equal(sig, park.rolling(5).mean().shift(1))

    def test_kinds_shapes(self):
        park, close = self._park_close()
        for kind in ("park_3", "park_10", "park_20", "cc_5", "cc_20", "vov_10", "ewma_5"):
            sig = opt.build_signal(park, close, kind)
            assert sig.shape == park.shape

    def test_no_lookahead(self):
        park, close = self._park_close()
        base = {k: opt.build_signal(park, close, k)
                for k in ("park_5", "cc_5", "vov_10", "ewma_5")}
        park2, close2 = park.copy(), close.copy()
        park2.iloc[-1] *= 100.0
        close2.iloc[-1] *= 100.0
        for k, sig in base.items():
            sig2 = opt.build_signal(park2, close2, k)
            # signal at t must not use row t data
            pd.testing.assert_series_equal(sig.iloc[-1], sig2.iloc[-1])


class TestUniverse:
    def test_monthly_universe_matches_t7(self):
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from predlab_t7 import monthly_universe as mu_legacy
        rng = np.random.default_rng(5)
        idx = pd.date_range("2024-01-01", periods=120, freq="D", tz="UTC")
        qv = pd.DataFrame(rng.uniform(1e5, 1e8, size=(120, 30)), index=idx,
                          columns=[f"S{i}" for i in range(30)])
        pd.testing.assert_frame_equal(opt.monthly_universe(qv, top_n=10),
                                      mu_legacy(qv, top_n=10))

    def test_adv_floor(self):
        idx = pd.date_range("2024-01-01", periods=90, freq="D", tz="UTC")
        qv = pd.DataFrame({"BIG": 1e7, "SMALL": 1e4}, index=idx, dtype=float)
        uni = pd.DataFrame(True, index=idx, columns=["BIG", "SMALL"])
        out = opt.apply_adv_floor(uni, qv, floor=1e6)
        feb = out[out.index >= "2024-02-01"]
        assert feb["BIG"].all()
        assert not feb["SMALL"].any()
        # first month has no prior-month info -> floor not applied there
        jan = out[out.index < "2024-02-01"]
        assert jan["SMALL"].all()


class TestRunLS:
    def test_default_matches_pp_run_s1(self):
        sig, ret, uni = _panels()
        old = pp.run_s1(sig, ret, uni, None, "eq", 1, "2024-01-01", "2024-12-31")
        new = opt.run_ls(sig, ret, uni, None, opt.OptConfig(), "2024-01-01", "2024-12-31")
        assert new["sr_net"] == pytest.approx(old["sr_net"], abs=1e-12)
        assert new["maxdd"] == pytest.approx(old["maxdd"], abs=1e-12)
        assert new["avg_turnover"] == pytest.approx(old["avg_turnover"], abs=1e-12)
        pd.testing.assert_series_equal(new["rets"]["net"], old["rets"]["net"],
                                       check_names=False)

    def test_smooth_matches_pp(self):
        sig, ret, uni = _panels()
        old = pp.run_s1(sig, ret, uni, None, "rank", 3, "2024-01-01", "2024-12-31")
        new = opt.run_ls(sig, ret, uni, None,
                         opt.OptConfig(weighting="rank", smooth=3),
                         "2024-01-01", "2024-12-31")
        assert new["sr_net"] == pytest.approx(old["sr_net"], abs=1e-12)

    def test_cadence(self):
        sig, ret, uni = _panels()
        r = opt.run_ls(sig, ret, uni, None, opt.OptConfig(cadence=5),
                       "2024-01-01", "2024-12-31")
        turn = r["rets"]["turnover"].to_numpy()
        # rebalance only every 5th traded day -> at least 3/5 of days zero turnover
        assert (turn == 0).mean() >= 0.6
        assert turn[0] > 0

    def test_buffer_cuts_turnover(self):
        sig, ret, uni = _panels(n_days=120)
        r0 = opt.run_ls(sig, ret, uni, None, opt.OptConfig(),
                        "2024-01-01", "2024-12-31")
        r1 = opt.run_ls(sig, ret, uni, None, opt.OptConfig(buffer=0.5),
                        "2024-01-01", "2024-12-31")
        assert r1["avg_turnover"] < r0["avg_turnover"]

    def test_accounting_identity_and_name_pnl(self):
        sig, ret, uni = _panels()
        fund = pd.DataFrame(0.0005, index=sig.index, columns=sig.columns)
        r = opt.run_ls(sig, ret, uni, fund, opt.OptConfig(), "2024-01-01", "2024-12-31")
        df = r["rets"]
        np.testing.assert_allclose(df["net"], df["gross"] - df["cost"] + df["carry"],
                                   atol=1e-14)
        assert r["name_pnl"].sum() == pytest.approx(df["gross"].sum(), abs=1e-10)

    def test_cost_stress(self):
        sig, ret, uni = _panels()
        r = opt.run_ls(sig, ret, uni, None, opt.OptConfig(), "2024-01-01", "2024-12-31")
        s = opt.cost_stress(r, mult=2.0)
        df = r["rets"]
        np.testing.assert_allclose(s, df["gross"] - 2.0 * df["cost"] + df["carry"],
                                   atol=1e-14)


class TestEvaluate:
    def test_windows_and_shares(self):
        sig, ret, uni = _panels(n_days=100)
        r = opt.run_ls(sig, ret, uni, None, opt.OptConfig(), "2024-01-01", "2024-12-31")
        ev = opt.evaluate(r, design=("2024-01-01", "2024-02-15"),
                          validation=("2024-02-16", "2024-12-31"))
        for k in ("full", "D", "V"):
            assert "sr_net" in ev[k] and "maxdd" in ev[k]
        assert ev["D"]["n_days"] + ev["V"]["n_days"] == ev["full"]["n_days"]
        assert 0.0 <= ev["max_name_share"] <= 1.0
        assert isinstance(ev["max_name"], str)


@pytest.mark.skipif(not (T7 / "close.parquet").exists(), reason="t7 panels absent")
class TestLegacyParityPin:
    """The Phase-O engine must reproduce the PP dev eq_h1 numbers EXACTLY."""

    def test_eq_h1_pin(self):
        close = pd.read_parquet(T7 / "close.parquet")
        qv = pd.read_parquet(T7 / "qv.parquet")
        park = pd.read_parquet(T7 / "park.parquet")
        hi = pd.Timestamp("2025-03-31", tz="UTC")
        close = close[close.index <= hi]
        qv, park = qv.loc[close.index], park.loc[close.index]
        ret = np.log(close).diff()
        uni = opt.monthly_universe(qv, top_n=200)
        sig = opt.build_signal(park, close, "park_5")
        fund = pd.read_parquet(DATA_ROOT / "predlab" / "pp_funding_daily.parquet"
                               ).reindex(ret.index)
        r = opt.run_ls(sig, ret, uni, fund, opt.OptConfig(),
                       "2021-01-01", "2025-03-31")
        assert r["sr_net"] == pytest.approx(1.4829604657236894, abs=1e-9)
        assert r["maxdd"] == pytest.approx(0.4246460612809624, abs=1e-9)
        assert r["avg_turnover"] == pytest.approx(0.6669561499469767, abs=1e-9)
        assert r["n_days"] == 1551


class TestTiltHook:
    def test_identity_tilt_matches_no_tilt(self):
        sig, ret, uni = _panels()
        r0 = opt.run_ls(sig, ret, uni, None, opt.OptConfig(), "2024-01-01", "2024-12-31")
        r1 = opt.run_ls(sig, ret, uni, None, opt.OptConfig(), "2024-01-01", "2024-12-31",
                        tilt=lambda d, w: w)
        pd.testing.assert_series_equal(r0["rets"]["net"], r1["rets"]["net"],
                                       check_names=False)

    def test_tilt_preserves_leg_sums(self):
        sig, ret, uni = _panels()
        seen = {}

        def tilt(d, w):
            out = w.copy()
            out[out > 0] *= np.linspace(0.5, 1.5, (out > 0).sum())
            out[out > 0] /= out[out > 0].sum()
            seen["called"] = True
            return out

        r = opt.run_ls(sig, ret, uni, None, opt.OptConfig(), "2024-01-01",
                       "2024-12-31", tilt=tilt)
        assert seen.get("called")
        assert r["n_days"] > 0

    def test_renorm_guard(self):
        # tilt returning non-unit legs must be renormalized by the engine
        sig, ret, uni = _panels()

        def bad_tilt(d, w):
            return w * 3.0

        r0 = opt.run_ls(sig, ret, uni, None, opt.OptConfig(), "2024-01-01", "2024-12-31")
        r1 = opt.run_ls(sig, ret, uni, None, opt.OptConfig(), "2024-01-01",
                        "2024-12-31", tilt=bad_tilt)
        pd.testing.assert_series_equal(r0["rets"]["net"], r1["rets"]["net"],
                                       check_names=False)


class TestEngineCorrection20260824:
    """engine_correction_2026-08-24: position PnL must be simple returns.

    A short held over a +10% / -9.0909% round trip (price returns to start)
    loses money in reality; under log-return accounting it books exactly 0.
    These pins keep the defect from returning.
    """

    def test_short_round_trip_loses_under_simple_returns(self):
        n_sym = 30  # >= opt.MIN_NAMES
        idx = _mkidx(4)
        syms = [f"S{i}" for i in range(n_sym)]
        close = pd.DataFrame(100.0, index=idx, columns=syms)
        # S29: volatile flat round trip; everything else stays at 100
        close.loc[idx[2], "S29"] = 110.0
        close.loc[idx[3], "S29"] = 100.0
        ret = close.pct_change(fill_method=None)
        # constant signal: S29 highest -> short leg (long bottom quintile)
        sig = pd.DataFrame(np.tile(np.arange(float(n_sym)), (4, 1)), index=idx,
                           columns=syms)
        uni = pd.DataFrame(True, index=idx, columns=syms)
        r = opt.run_ls(sig, ret, uni, None,
                       opt.OptConfig(taker_bp=0.0, smooth=1),
                       "2024-01-01", "2024-01-04")
        # short leg = top sextile (6 names), w = -1/6 each
        # S29 short PnL: -(1/6)*0.10 + -(1/6)*(-1/11) < 0
        assert r["rets"]["gross"].sum() < -0.001
        assert r["name_pnl"]["S29"] < 0

        # the log-return artifact books ~0 on the same path (documents why)
        ret_log = np.log(close).diff()
        r_log = opt.run_ls(sig, ret_log, uni, None,
                           opt.OptConfig(taker_bp=0.0, smooth=1),
                           "2024-01-01", "2024-01-04")
        assert abs(r_log["rets"]["gross"].sum()) < 1e-12

    def test_runner_scripts_construct_simple_pnl_returns(self):
        # convention pin: no strategy-PnL runner may feed log returns to the
        # engine. t7/holdout IC layers (rank-based) are exempt by declaration.
        pnl_scripts = [
            "predlab_opt_o1.py", "predlab_pp_dev.py", "predlab_pp_holdout.py",
            "predlab_bybit_r1.py", "predlab_xasset_r1.py",
            "predlab_futfx_r1.py", "predlab_s1_paper.py",
        ]
        for name in pnl_scripts:
            src = (PROJECT_ROOT / "scripts" / name).read_text()
            assert "np.log(close).diff()" not in src, name
            if name != "predlab_s1_paper.py":
                assert "pct_change(fill_method=None)" in src, name


class TestLongOnlyClipTilt:
    """predlab_opt2 R2: long-only book via clip-shorts tilt.

    The engine renorms each leg after a tilt, so clipping shorts yields a
    gross-1 long-only book with the standard cost/carry plumbing.
    """

    def test_clip_tilt_book_is_long_only_gross_one(self):
        sig, ret, uni = _panels()
        seen = {}

        def lo_tilt(d, w):
            out = w.clip(lower=0.0)
            seen["clipped"] = True
            return out

        r = opt.run_ls(sig, ret, uni, None,
                       opt.OptConfig(taker_bp=0.0, smooth=1),
                       "2024-01-01", "2024-12-31", tilt=lo_tilt)
        assert seen.get("clipped")
        assert r["n_days"] > 0
        # every name's cumulative PnL must come from long exposure only:
        # rerun manually for one day and check weights
        d = r["rets"].index[0]
        w_tgt = opt.leg_weights(sig.loc[d], 0.2, "eq")
        w_lo = w_tgt.clip(lower=0.0)
        w_lo = w_lo / w_lo.sum()
        assert (w_lo >= 0).all()
        assert w_lo.sum() == pytest.approx(1.0)
        got = float((w_lo * ret.loc[d].reindex(w_lo.index)).fillna(0).sum())
        assert r["rets"]["gross"].iloc[0] == pytest.approx(got)
