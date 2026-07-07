"""Tests for scripts/validate_sentiment_feature.py — the sentiment-feature A/B
validation harness (Task 10 of the sentiment-index-feature plan).

Covers:
  1. `gate_verdict` — pure function, 3 pre-registered acceptance cases.
  2. Synthetic end-to-end per-coin A/B (small n_boot) with an injected
     positive drift in the "sent" arm's predictions — asserts delta_sr > 0
     and the metrics dict has the full required-key contract.
  3. Alignment: two arms with offset date ranges intersect cleanly with no
     NaNs in the resulting aligned return series.
  4. Guards: insufficient overlapping dates raises; NaN days are dropped
     pairwise (counted in the metrics); excessive NaN fraction raises.

No network access and no real prediction data are required — OHLCV loading
is monkeypatched at `scripts.baseline_v5_mix._load_crypto_ohlcv` (the same
loader `run_coin` calls), and prediction CSVs are tiny synthetic fixtures
written to `tmp_path`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts import validate_sentiment_feature as vsf


# ── Synthetic fixture builders ───────────────────────────────────────


def _write_pred_csvs(
    dir_path, coin: str, dates: pd.DatetimeIndex,
    pred_h7: np.ndarray, pred_h14: np.ndarray, ref_price: np.ndarray,
) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    df7 = pd.DataFrame({
        "date": dates, "coin_id": coin, "prediction": pred_h7,
        "actual": ref_price, "ref_price": ref_price,
    })
    df14 = pd.DataFrame({
        "date": dates, "coin_id": coin, "prediction": pred_h14,
        "actual": ref_price, "ref_price": ref_price,
    })
    df7.to_csv(dir_path / "preds_lgb_h7.csv", index=False)
    df14.to_csv(dir_path / "preds_lgb_h14.csv", index=False)


def _make_uptrend_price(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    daily_ret = 0.004 + rng.normal(0.0, 0.003, n)
    return 100.0 * np.cumprod(1.0 + daily_ret)


def _make_ohlcv(dates: pd.DatetimeIndex, price: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({
        "Date": dates, "Open": price, "High": price * 1.001,
        "Low": price * 0.999, "Close": price, "Volume": 1000.0,
    })


# ── 1. gate_verdict — pure function ─────────────────────────────────


class TestGateVerdict:
    def test_clear_ship(self):
        # High confidence sentiment beats base, drawdown equal.
        assert vsf.gate_verdict(p_pos=0.95, maxdd_base=0.05, maxdd_sent=0.05) == "SHIP"

    def test_clear_no(self):
        # Coin-flip confidence — well below the 0.90 threshold.
        assert vsf.gate_verdict(p_pos=0.50, maxdd_base=0.05, maxdd_sent=0.05) == "NO"

    def test_dd_fail_despite_sr_pass(self):
        # p_pos clears the bar, but drawdown got 2pp worse (> 1pp tolerance).
        assert vsf.gate_verdict(p_pos=0.95, maxdd_base=0.05, maxdd_sent=0.07) == "NO"

    def test_dd_exactly_at_tolerance_ships(self):
        # Boundary: exactly 1pp worse still ships (<=, not <).
        assert vsf.gate_verdict(p_pos=0.95, maxdd_base=0.05, maxdd_sent=0.06) == "SHIP"

    def test_dd_improves_still_ships(self):
        assert vsf.gate_verdict(p_pos=0.90, maxdd_base=0.05, maxdd_sent=0.02) == "SHIP"


# ── 2. Synthetic end-to-end per-coin A/B ────────────────────────────


class TestSyntheticEndToEnd:
    def test_positive_drift_yields_positive_delta_sr(self, tmp_path, monkeypatch):
        n = 140
        dates = pd.date_range("2024-01-01", periods=n, freq="D")
        price = _make_uptrend_price(n, seed=123)

        rng = np.random.default_rng(456)
        noise = rng.uniform(-0.02, 0.02, n)
        base_pred = price * (1.0 + noise)
        # Sent arm: base + small positive drift injected into predictions,
        # per the task spec. Both horizons get the identical nudge so they
        # stay in full agreement (isolates the drift's effect on sizing).
        drift_add = 0.01
        sent_pred = price * (1.0 + noise + drift_add)

        base_dir = tmp_path / "base_78f"
        sent_dir = tmp_path / "sent_llm_78f"
        _write_pred_csvs(base_dir, "bitcoin", dates, base_pred, base_pred, price)
        _write_pred_csvs(sent_dir, "bitcoin", dates, sent_pred, sent_pred, price)

        ohlcv = _make_ohlcv(dates, price)
        monkeypatch.setattr(vsf.bm, "_load_crypto_ohlcv", lambda coin, end: ohlcv.copy())

        metrics, base_ret, sent_ret = vsf.run_coin_ab(
            "bitcoin", base_dir, sent_dir, n_boot=100, seed=7,
        )

        required_keys = {
            "n_bars", "sr_base", "sr_sent", "delta_sr", "ci_low", "ci_high",
            "p_pos", "maxdd_base", "maxdd_sent", "verdict",
            "n_days", "n_dropped_nan",
        }
        assert required_keys <= metrics.keys()
        assert metrics["n_days"] == metrics["n_bars"] == len(base_ret)
        assert metrics["n_dropped_nan"] == 0
        assert metrics["verdict"] in {"SHIP", "NO"}
        assert metrics["delta_sr"] > 0
        assert metrics["delta_sr"] == pytest.approx(metrics["sr_sent"] - metrics["sr_base"])

        assert len(base_ret) == len(sent_ret) == metrics["n_bars"]
        assert not base_ret.isna().any()
        assert not sent_ret.isna().any()

    def test_full_run_validation_json_structure(self, tmp_path, monkeypatch):
        """End-to-end via run_validation() (both coins + portfolio + DSR) —
        the full contract main() writes to --out."""
        n = 140
        dates = pd.date_range("2024-01-01", periods=n, freq="D")

        pred_root = tmp_path / "eval_ab"
        ohlcv_by_coin = {}
        rng = np.random.default_rng(99)
        for coin, arms in [
            ("bitcoin", {"base": "base_78f", "sent": "sent_llm_78f"}),
            ("ethereum", {"base": "base_193f", "sent": "sent_llm_193f"}),
        ]:
            price = _make_uptrend_price(n, seed=hash(coin) % 1000)
            noise = rng.uniform(-0.02, 0.02, n)
            base_pred = price * (1.0 + noise)
            sent_pred = price * (1.0 + noise + 0.01)
            _write_pred_csvs(pred_root / arms["base"], coin, dates, base_pred, base_pred, price)
            _write_pred_csvs(pred_root / arms["sent"], coin, dates, sent_pred, sent_pred, price)
            ohlcv_by_coin[coin] = _make_ohlcv(dates, price)

        monkeypatch.setattr(
            vsf.bm, "_load_crypto_ohlcv",
            lambda coin, end: ohlcv_by_coin[coin].copy(),
        )

        summary = vsf.run_validation(pred_root, "llm", n_boot=50, seed=3)

        assert set(summary.keys()) == {"config", "per_coin", "portfolio", "dsr"}
        assert set(summary["per_coin"].keys()) == {"bitcoin", "ethereum"}
        per_coin_keys = {
            "n_bars", "sr_base", "sr_sent", "delta_sr", "ci_low", "ci_high",
            "p_pos", "maxdd_base", "maxdd_sent", "verdict",
            "n_days", "n_dropped_nan",
        }
        for coin_metrics in summary["per_coin"].values():
            assert per_coin_keys <= coin_metrics.keys()
        # Portfolio row carries the base A/B contract (per-coin NaN-drop
        # accounting lives on the per-coin rows).
        portfolio_keys = per_coin_keys - {"n_days", "n_dropped_nan"}
        assert portfolio_keys <= summary["portfolio"].keys()
        assert summary["dsr"]["n_trials"] == vsf.DSR_N_TRIALS == 8
        assert summary["config"]["engine"] == "llm"
        assert summary["config"]["git_sha"]  # non-empty string ("unknown" fallback OK)

        # JSON-serializable end to end (the actual on-disk contract).
        import json
        json.dumps(summary, default=str)


# ── 3. Alignment: offset date ranges intersect cleanly ──────────────


class TestAlignment:
    def test_offset_arms_intersect_with_no_nans(self, tmp_path, monkeypatch):
        full_dates = pd.date_range("2023-12-01", periods=250, freq="D")
        price = _make_uptrend_price(250, seed=55)

        dates_base = full_dates[0:180]      # 180 days
        dates_sent = full_dates[30:210]     # offset by 30 days, 180 days
        price_base = price[0:180]
        price_sent = price[30:210]

        rng = np.random.default_rng(7)
        noise_base = rng.uniform(-0.02, 0.02, len(dates_base))
        noise_sent = rng.uniform(-0.02, 0.02, len(dates_sent))
        base_pred = price_base * (1.0 + noise_base)
        sent_pred = price_sent * (1.0 + noise_sent)

        base_dir = tmp_path / "base_78f"
        sent_dir = tmp_path / "sent_llm_78f"
        _write_pred_csvs(base_dir, "bitcoin", dates_base, base_pred, base_pred, price_base)
        _write_pred_csvs(sent_dir, "bitcoin", dates_sent, sent_pred, sent_pred, price_sent)

        ohlcv = _make_ohlcv(full_dates, price)
        monkeypatch.setattr(vsf.bm, "_load_crypto_ohlcv", lambda coin, end: ohlcv.copy())

        metrics, base_ret, sent_ret = vsf.run_coin_ab(
            "bitcoin", base_dir, sent_dir, n_boot=50, seed=1,
        )

        assert len(base_ret) == len(sent_ret) > 0
        assert base_ret.index.equals(sent_ret.index)

        overlap_start = max(dates_base.min(), dates_sent.min())
        overlap_end = min(dates_base.max(), dates_sent.max())
        assert base_ret.index.min() >= overlap_start
        assert base_ret.index.max() <= overlap_end

        assert not base_ret.isna().any()
        assert not sent_ret.isna().any()
        assert metrics["n_bars"] == len(base_ret)


# ── 4. Guards: overlap minimum + pairwise NaN handling ──────────────


def _series(dates: pd.DatetimeIndex, seed: int) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(0.001, 0.01, len(dates)), index=dates)


class TestAlignmentGuards:
    def test_insufficient_overlap_raises(self):
        dates_a = pd.date_range("2024-01-01", periods=120, freq="D")
        dates_b = pd.date_range("2024-03-15", periods=120, freq="D")  # ~46-day overlap
        base = _series(dates_a, seed=1)
        sent = _series(dates_b, seed=2)
        with pytest.raises(ValueError, match="insufficient overlapping dates.*bitcoin"):
            vsf.align_arm_returns(base, sent, "bitcoin")

    def test_zero_overlap_raises_not_crashes(self):
        # Fully disjoint ranges must raise the clear guard message, not
        # crash deep inside the bootstrap with rng.integers(0, 0).
        base = _series(pd.date_range("2023-01-01", periods=150, freq="D"), seed=1)
        sent = _series(pd.date_range("2025-01-01", periods=150, freq="D"), seed=2)
        with pytest.raises(ValueError, match="insufficient overlapping dates"):
            vsf.align_arm_returns(base, sent, "ethereum")

    def test_window_filter_can_trigger_overlap_guard(self):
        dates = pd.date_range("2024-01-01", periods=200, freq="D")
        base = _series(dates, seed=3)
        sent = _series(dates, seed=4)
        with pytest.raises(ValueError, match="insufficient overlapping dates"):
            vsf.align_arm_returns(base, sent, "bitcoin",
                                  start="2024-06-01", end="2024-06-20")

    def test_nan_days_dropped_pairwise_and_counted(self):
        dates = pd.date_range("2024-01-01", periods=200, freq="D")
        base = _series(dates, seed=5)
        sent = _series(dates, seed=6)
        sent.iloc[50] = np.nan  # NaN in one arm only

        b, s, n_dropped = vsf.align_arm_returns(base, sent, "bitcoin")

        assert n_dropped == 1
        # The NaN day is removed from BOTH arms (pairwise).
        assert dates[50] not in b.index
        assert dates[50] not in s.index
        assert b.index.equals(s.index)
        assert len(b) == 199
        assert not b.isna().any()
        assert not s.isna().any()

    def test_excessive_nan_fraction_raises(self):
        dates = pd.date_range("2024-01-01", periods=200, freq="D")
        base = _series(dates, seed=7)
        sent = _series(dates, seed=8)
        sent.iloc[10:15] = np.nan  # 5/200 = 2.5% > 1% tolerance
        with pytest.raises(ValueError, match="NaN returns.*broken"):
            vsf.align_arm_returns(base, sent, "bitcoin")

    def test_nan_count_reaches_json_metrics(self, tmp_path, monkeypatch):
        """A single NaN injected into one arm's return series flows through
        run_coin_ab: dropped pairwise, counted in n_dropped_nan, and never
        reaches sharpe()/p_pos silently."""
        n = 140
        dates = pd.date_range("2024-01-01", periods=n, freq="D")
        price = _make_uptrend_price(n, seed=11)
        rng = np.random.default_rng(12)
        noise = rng.uniform(-0.02, 0.02, n)
        base_pred = price * (1.0 + noise)
        sent_pred = price * (1.0 + noise + 0.01)

        base_dir = tmp_path / "base_78f"
        sent_dir = tmp_path / "sent_llm_78f"
        _write_pred_csvs(base_dir, "bitcoin", dates, base_pred, base_pred, price)
        _write_pred_csvs(sent_dir, "bitcoin", dates, sent_pred, sent_pred, price)

        ohlcv = _make_ohlcv(dates, price)
        monkeypatch.setattr(vsf.bm, "_load_crypto_ohlcv", lambda coin, end: ohlcv.copy())

        # Wrap run_coin to inject a NaN into the sentiment arm's returns.
        real_run_coin = vsf.bm.run_coin

        def run_coin_with_nan(coin, pred_dir, *args, **kwargs):
            r = real_run_coin(coin, pred_dir, *args, **kwargs)
            if pred_dir == sent_dir:
                r.iloc[40] = np.nan
            return r

        monkeypatch.setattr(vsf.bm, "run_coin", run_coin_with_nan)

        metrics, base_ret, sent_ret = vsf.run_coin_ab(
            "bitcoin", base_dir, sent_dir, n_boot=50, seed=9,
        )

        assert metrics["n_dropped_nan"] == 1
        assert metrics["n_days"] == len(base_ret) == len(sent_ret)
        assert not base_ret.isna().any()
        assert not sent_ret.isna().any()
        assert not np.isnan(metrics["sr_sent"])
        assert not np.isnan(metrics["p_pos"])
