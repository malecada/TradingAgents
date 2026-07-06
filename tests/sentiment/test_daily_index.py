"""Tests for tradingagents.sentiment.daily_index.aggregate (Task 7).

Synthetic multi-day per-article frames only — no real corpora, no network.
"""
from __future__ import annotations

import glob

import pandas as pd
import pytest

from tradingagents.dataflows import onchain_store
from tradingagents.sentiment import daily_index as di

BASE_DAY = pd.Timestamp("2024-01-01", tz="UTC")


def _make_scores(n_days=40, skip_days=(), coin="btc", start=BASE_DAY,
                  values=(0.4, 0.8), engine="llm"):
    """One synthetic day per index 0..n_days-1 (skipping `skip_days`), each
    with len(values) articles carrying the given constant score_norm values.
    Deterministic by construction (no RNG) so aggregate() outputs are exact.
    """
    rows = []
    for d in range(n_days):
        if d in skip_days:
            continue
        day = start + pd.Timedelta(days=d)
        for i, v in enumerate(values):
            rows.append({
                "event_ts": day + pd.Timedelta(hours=i),
                "as_of_ts": day + pd.Timedelta(hours=i + 1),
                "coin": coin,
                "engine": engine,
                "score_norm": v,
                "relevant": True,
                "content_sha": f"{coin}-{d}-{i}",
            })
    return pd.DataFrame(rows)


def _make_varied_scores(n_days=40, skip_days=(), coin="btc", start=BASE_DAY, engine="llm"):
    """Article count varies day to day (2, 3, 4 repeating), unlike
    `_make_scores`'s constant count — needed for z-score tests, since a
    constant daily count has zero rolling variance and the z-score formula
    (deviation / std) is 0/0 = NaN forever in that degenerate case."""
    rows = []
    for d in range(n_days):
        if d in skip_days:
            continue
        day = start + pd.Timedelta(days=d)
        n_articles = (d % 3) + 2  # 2, 3, 4, 2, 3, 4, ...
        for i in range(n_articles):
            score = 0.5 if i % 2 == 0 else -0.3
            rows.append({
                "event_ts": day + pd.Timedelta(hours=i),
                "as_of_ts": day + pd.Timedelta(hours=i + 1),
                "coin": coin,
                "engine": engine,
                "score_norm": score,
                "relevant": True,
                "content_sha": f"{coin}-v-{d}-{i}",
            })
    return pd.DataFrame(rows)


def _metric(out: pd.DataFrame, coin: str, metric: str) -> pd.DataFrame:
    return out[(out.coin == coin) & (out.metric == metric)].sort_values("event_ts")


# ---------------------------------------------------------------------------
# No-news days
# ---------------------------------------------------------------------------

class TestNoNewsDay:
    def test_cnt_and_mean_are_zero_on_no_news_day(self):
        scores = _make_scores(n_days=40, skip_days=(20,))
        out = di.aggregate(scores)
        day20 = BASE_DAY + pd.Timedelta(days=20)
        mean_row = _metric(out, "btc", "snt_idx_mean")
        val = mean_row.loc[mean_row.event_ts == day20, "value"].iloc[0]
        assert val == 0.0

    def test_ewma_is_carried_not_reset_on_no_news_day(self):
        scores = _make_scores(n_days=40, skip_days=(20,))
        out = di.aggregate(scores)
        ewm = _metric(out, "btc", "snt_idx_ewm3")
        day19 = BASE_DAY + pd.Timedelta(days=19)
        day20 = BASE_DAY + pd.Timedelta(days=20)
        ewm19 = ewm.loc[ewm.event_ts == day19, "value"].iloc[0]
        ewm20 = ewm.loc[ewm.event_ts == day20, "value"].iloc[0]
        # Constant 0.6 mean every day before the gap -> ewm settles at 0.6.
        assert ewm19 == pytest.approx(0.6, abs=1e-9)
        # The no-news day pulls the EWMA down toward (but not to) 0 — it is
        # "carried", not reset to the raw (zero) daily value.
        assert 0.0 < ewm20 < ewm19

    def test_no_news_day_present_in_output_calendar(self):
        # The day itself must appear (with cnt/mean 0), not be dropped.
        scores = _make_scores(n_days=40, skip_days=(20,))
        out = di.aggregate(scores)
        day20 = BASE_DAY + pd.Timedelta(days=20)
        assert (_metric(out, "btc", "snt_idx_mean").event_ts == day20).any()


# ---------------------------------------------------------------------------
# Warm-up / NaN suppression
# ---------------------------------------------------------------------------

class TestWarmup:
    def test_z_score_absent_before_min_periods_10(self):
        # Varied daily counts (see _make_varied_scores) so the rolling std
        # is non-degenerate once min_periods=10 is reached.
        scores = _make_varied_scores(n_days=40, skip_days=())
        out = di.aggregate(scores)
        z = _metric(out, "btc", "snt_cnt_z30")
        earliest = z.event_ts.min()
        assert earliest == BASE_DAY + pd.Timedelta(days=9)
        for d in range(9):
            day = BASE_DAY + pd.Timedelta(days=d)
            assert not (z.event_ts == day).any(), f"day {d} should be absent (NaN warm-up)"

    def test_disp_and_neg_share_absent_before_min_periods_3(self):
        scores = _make_scores(n_days=40, skip_days=())
        out = di.aggregate(scores)
        disp = _metric(out, "btc", "snt_disp_7d")
        neg = _metric(out, "btc", "snt_neg_share_7d")
        assert disp.event_ts.min() == BASE_DAY + pd.Timedelta(days=2)
        assert neg.event_ts.min() == BASE_DAY + pd.Timedelta(days=2)

    def test_disp_and_neg_share_values_once_warm(self):
        scores = _make_scores(n_days=40, skip_days=())
        out = di.aggregate(scores)
        disp = _metric(out, "btc", "snt_disp_7d")
        neg = _metric(out, "btc", "snt_neg_share_7d")
        # values=(0.4, 0.8): sample std (ddof=1) = sqrt(0.08) ~= 0.28284271
        assert disp["value"].iloc[0] == pytest.approx(0.282842712, abs=1e-6)
        # both values positive -> neg share is 0 every day
        assert (neg["value"] == 0.0).all()

    def test_only_non_nan_rows_emitted(self):
        scores = _make_scores(n_days=40, skip_days=(20,))
        out = di.aggregate(scores)
        assert out["value"].notna().all()
        assert not out.isna().any().any()

    def test_all_ones_article_per_day_never_emits_disp(self):
        # std of a single-article day is NaN by construction (ddof=1) -> the
        # rolling(7, min_periods=3) input is all-NaN for every window, so
        # snt_disp_7d should never appear at all in this scenario.
        scores = _make_scores(n_days=40, skip_days=(), values=(0.5,))
        out = di.aggregate(scores)
        assert _metric(out, "btc", "snt_disp_7d").empty


# ---------------------------------------------------------------------------
# as_of_ts convention
# ---------------------------------------------------------------------------

class TestAsOfTs:
    def test_as_of_ts_is_event_ts_plus_25h(self):
        scores = _make_scores(n_days=40, skip_days=(20,))
        out = di.aggregate(scores)
        delta = out["as_of_ts"] - out["event_ts"]
        assert (delta == pd.Timedelta(hours=25)).all()

    def test_event_ts_is_calendar_midnight_utc(self):
        scores = _make_scores(n_days=40, skip_days=(20,))
        out = di.aggregate(scores)
        assert (out["event_ts"].dt.hour == 0).all()
        assert (out["event_ts"].dt.minute == 0).all()


# ---------------------------------------------------------------------------
# Metric/coin coverage
# ---------------------------------------------------------------------------

class TestCoverage:
    def test_all_five_metrics_present(self):
        scores = _make_varied_scores(n_days=40, skip_days=())
        out = di.aggregate(scores)
        assert set(out["metric"].unique()) == set(di.METRICS)

    def test_source_and_status_columns(self):
        scores = _make_scores(n_days=40, skip_days=())
        out = di.aggregate(scores)
        assert (out["source"] == "sentiment_index").all()
        assert (out["status"] == "final").all()

    def test_global_coin_gets_independent_calendar(self):
        btc = _make_scores(n_days=20, skip_days=(5,), coin="btc", start=BASE_DAY)
        glb_start = BASE_DAY + pd.Timedelta(days=10)
        glb = _make_scores(n_days=15, skip_days=(), coin="global", start=glb_start)
        out = di.aggregate(pd.concat([btc, glb], ignore_index=True))

        assert set(out["coin"].unique()) == {"btc", "global"}

        btc_mean = _metric(out, "btc", "snt_idx_mean")
        assert btc_mean.event_ts.min() == BASE_DAY
        assert btc_mean.event_ts.max() == BASE_DAY + pd.Timedelta(days=19)

        glb_mean = _metric(out, "global", "snt_idx_mean")
        assert glb_mean.event_ts.min() == glb_start
        assert glb_mean.event_ts.max() == glb_start + pd.Timedelta(days=14)

    def test_empty_input_returns_empty_schema_frame(self):
        empty = pd.DataFrame(columns=[
            "event_ts", "as_of_ts", "coin", "engine", "score_norm",
            "relevant", "content_sha",
        ])
        out = di.aggregate(empty)
        assert out.empty
        assert list(out.columns) == onchain_store.SCHEMA_COLS


# ---------------------------------------------------------------------------
# Round-trip through the store
# ---------------------------------------------------------------------------

class TestStoreRoundTrip:
    def test_aggregate_output_upserts_cleanly(self, tmp_path):
        scores = _make_scores(n_days=40, skip_days=(20,))
        out = di.aggregate(scores)

        written = onchain_store.upsert_rows(out, root=tmp_path)
        assert written == len(out)

        files = glob.glob(str(tmp_path / "*" / "*.parquet"))
        assert files
        reloaded = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
        assert len(reloaded) == len(out)
        assert set(reloaded.columns) == set(onchain_store.SCHEMA_COLS)
        assert reloaded["value"].notna().all()

    def test_upsert_via_sentiment_index_store(self, tmp_path, monkeypatch):
        from tradingagents.dataflows import sentiment_index_store as sis

        monkeypatch.setattr(sis, "BASE_ROOT", tmp_path)
        scores = _make_scores(n_days=40, skip_days=(20,))
        out = di.aggregate(scores)

        sis.upsert_index_rows(out, engine="llm")
        loaded = sis.load_index(
            "llm", coins=["btc"], start="2024-01-01", end="2024-03-01",
        )
        assert len(loaded) == len(out)
        assert set(loaded["metric"]) == set(di.METRICS)
