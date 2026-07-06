"""Unit tests for tradingagents.dataflows.sentiment_features PIT alignment."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from tradingagents.dataflows import sentiment_features, sentiment_index_store


def _idx_row(
    event_ts: datetime, coin: str, metric: str, value: float,
    as_of_ts: datetime | None = None,
) -> dict:
    return {
        "event_ts": event_ts,
        "as_of_ts": as_of_ts if as_of_ts is not None else event_ts,
        "coin": coin,
        "metric": metric,
        "value": float(value),
        "source": "sentiment_index",
        "status": "final",
    }


def _write_index(tmp_path, monkeypatch, rows: list[dict], engine: str = "llm"):
    monkeypatch.setattr(sentiment_index_store, "BASE_ROOT", tmp_path / "index")
    sentiment_index_store.upsert_index_rows(pd.DataFrame(rows), engine=engine)


def _write_fng(tmp_path, monkeypatch, rows: list[dict]):
    data_root = tmp_path / "data_root"
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(data_root))
    fng_path = data_root / "sentiment" / "fng"
    fng_path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows)[["event_ts", "as_of_ts", "value", "classification"]].to_parquet(
        fng_path / "fng.parquet", index=False
    )
    return data_root


def test_as_of_gating_row_visible_on_day_of_not_before(tmp_path, monkeypatch):
    """A row with as_of_ts = day D 01:00 must appear on day D, not D-1."""
    day = datetime(2025, 6, 10, tzinfo=timezone.utc)
    _write_index(tmp_path, monkeypatch, [
        _idx_row(day, "btc", "snt_idx_mean", 0.42, as_of_ts=day + timedelta(hours=1)),
    ])
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path / "nonexistent_root"))

    dates = pd.DatetimeIndex([day - timedelta(days=1), day])
    out = sentiment_features.build_sentiment_features("bitcoin", dates, engine="llm")

    assert pd.isna(out["snt_idx_mean"].iloc[0]), "value must not leak to D-1"
    assert out["snt_idx_mean"].iloc[1] == pytest.approx(0.42)


def test_coin_with_no_per_coin_rows_still_gets_global_and_fng(tmp_path, monkeypatch):
    day = datetime(2025, 6, 10, tzinfo=timezone.utc)
    _write_index(tmp_path, monkeypatch, [
        _idx_row(day, "global", "snt_idx_ewm3", 0.1, as_of_ts=day + timedelta(hours=1)),
        _idx_row(day, "global", "snt_cnt_z30", 1.5, as_of_ts=day + timedelta(hours=1)),
    ])
    data_root = _write_fng(tmp_path, monkeypatch, [
        {"event_ts": day, "as_of_ts": day + timedelta(hours=1), "value": 50, "classification": "Neutral"},
    ])

    dates = pd.DatetimeIndex([day])
    out = sentiment_features.build_sentiment_features("solana", dates, engine="llm")

    # No per-coin rows for solana/sol -> all NaN.
    for col in sentiment_features.PER_COIN_METRICS:
        assert pd.isna(out[col].iloc[0])
    # Global + fng still populated.
    assert out["snt_g_idx_ewm3"].iloc[0] == pytest.approx(0.1)
    assert out["snt_g_cnt_z30"].iloc[0] == pytest.approx(1.5)
    assert out["fng_level"].iloc[0] == pytest.approx(50)


def test_empty_store_and_missing_fng_all_nan(tmp_path, monkeypatch):
    monkeypatch.setattr(sentiment_index_store, "BASE_ROOT", tmp_path / "index_empty")
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path / "no_data_root"))

    dates = pd.DatetimeIndex([datetime(2025, 6, 10, tzinfo=timezone.utc)])
    out = sentiment_features.build_sentiment_features("bitcoin", dates, engine="llm")

    assert list(out.columns) == sentiment_features.FEATURE_COLS
    assert len(out) == 1
    for col in out.columns:
        assert out[col].isna().all()


def test_fng_dev_hand_computed(tmp_path, monkeypatch):
    monkeypatch.setattr(sentiment_index_store, "BASE_ROOT", tmp_path / "index_empty2")
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    rows = []
    values = [10, 20, 30, 40, 50]
    for i, v in enumerate(values):
        d = base + timedelta(days=i)
        rows.append({
            "event_ts": d, "as_of_ts": d + timedelta(hours=1),
            "value": v, "classification": "x",
        })
    _write_fng(tmp_path, monkeypatch, rows)

    dates = pd.DatetimeIndex([base + timedelta(days=i) for i in range(len(values))])
    out = sentiment_features.build_sentiment_features("bitcoin", dates, engine="llm")

    expected_level = pd.Series(values, dtype="float64")
    expected_ema = expected_level.ewm(halflife=84).mean()
    expected_dev = expected_level - expected_ema

    pd.testing.assert_series_equal(
        out["fng_level"].reset_index(drop=True), expected_level, check_names=False,
    )
    pd.testing.assert_series_equal(
        out["fng_ema_168d"].reset_index(drop=True), expected_ema, check_names=False,
    )
    pd.testing.assert_series_equal(
        out["fng_dev"].reset_index(drop=True), expected_dev, check_names=False,
    )


def test_fng_ema_window_invariant(tmp_path, monkeypatch):
    """fng_ema_168d/fng_dev on a given calendar day must not depend on the
    caller's query-window start: the EWM runs over the full available fng
    history, not the window-restricted slice, so walk-forward calls with
    different lookbacks agree on the same (coin, date) values."""
    monkeypatch.setattr(sentiment_index_store, "BASE_ROOT", tmp_path / "index_wi")
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    n = 40
    rows = []
    for i in range(n):
        d = base + timedelta(days=i)
        rows.append({
            "event_ts": d, "as_of_ts": d + timedelta(hours=1),
            "value": 10 + (i * 7) % 60, "classification": "x",
        })
    _write_fng(tmp_path, monkeypatch, rows)

    # Long window: full history. Short window: strict subset (last 5 days).
    long_dates = pd.DatetimeIndex([base + timedelta(days=i) for i in range(n)])
    short_dates = pd.DatetimeIndex([base + timedelta(days=i) for i in range(n - 5, n)])

    long_out = sentiment_features.build_sentiment_features("bitcoin", long_dates)
    short_out = sentiment_features.build_sentiment_features("bitcoin", short_dates)

    for col in ["fng_level", "fng_ema_168d", "fng_dev"]:
        pd.testing.assert_series_equal(
            short_out[col],
            long_out[col].loc[short_dates],
            check_names=False,
        )


def test_fng_malformed_parquet_degrades_to_nan(tmp_path, monkeypatch):
    """A malformed fng.parquet (wrong columns) must yield NaN fng cols, not raise."""
    monkeypatch.setattr(sentiment_index_store, "BASE_ROOT", tmp_path / "index_mal")
    data_root = tmp_path / "data_root_mal"
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(data_root))
    fng_dir = data_root / "sentiment" / "fng"
    fng_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"bogus": [1, 2]}).to_parquet(fng_dir / "fng.parquet", index=False)

    dates = pd.DatetimeIndex([datetime(2025, 6, 10, tzinfo=timezone.utc)])
    out = sentiment_features.build_sentiment_features("bitcoin", dates)

    for col in ["fng_level", "fng_ema_168d", "fng_dev"]:
        assert out[col].isna().all()


def test_column_set_exactly_ten_in_order(tmp_path, monkeypatch):
    monkeypatch.setattr(sentiment_index_store, "BASE_ROOT", tmp_path / "index_empty3")
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path / "no_root"))

    dates = pd.DatetimeIndex([datetime(2025, 6, 10, tzinfo=timezone.utc)])
    out = sentiment_features.build_sentiment_features("bitcoin", dates, engine="llm")

    assert list(out.columns) == [
        "snt_idx_mean", "snt_idx_ewm3", "snt_cnt_z30", "snt_neg_share_7d", "snt_disp_7d",
        "snt_g_idx_ewm3", "snt_g_cnt_z30",
        "fng_level", "fng_ema_168d", "fng_dev",
    ]
    assert len(out.columns) == 10
