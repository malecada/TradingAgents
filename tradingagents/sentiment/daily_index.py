"""Daily aggregation of per-article sentiment scores into index-store rows.

Consumes the per-article score rows produced by
`scripts/score_sentiment_corpus.py` (Task 6) — one row per (article, coin)
with columns `[event_ts, as_of_ts, coin, engine, score_norm, relevant,
content_sha]` — and rolls them up into a daily long-format frame ready for
`tradingagents.dataflows.sentiment_index_store.upsert_index_rows` (the
`onchain_store` bitemporal schema: `[event_ts, as_of_ts, coin, metric,
value, source, status]`).

Per coin (including the synthetic "global" coin), five metrics are computed
for every calendar day in that coin's data span:

- `snt_idx_mean`      daily mean of `score_norm` (0.0 on no-news days).
- `snt_idx_ewm3`      EWMA of `snt_idx_mean`, halflife=3 days.
- `snt_cnt_z30`       z-score of the daily article count vs a trailing
                      30-day rolling window (min_periods=10; NaN before
                      warm-up).
- `snt_neg_share_7d`  trailing 7-day mean of the daily share of articles
                      with `score_norm < 0` (min_periods=3; the daily share
                      itself is NaN on no-news days, which rolling `.mean()`
                      skips).
- `snt_disp_7d`       trailing 7-day mean of the daily std-dev of
                      `score_norm` (min_periods=3; the daily std is NaN on
                      days with fewer than 2 articles, same NaN-skip).

A day with zero matching articles gets `snt_idx_mean=0` and `snt_cnt=0` (an
explicit "no news, neutral" signal) rather than being dropped — this is
required so the EWMA and rolling windows see a continuous daily calendar.
Warm-up rows for the rolling/EWM-derived metrics that are still NaN are
never emitted (the index store must never hold NaN values).
"""
from __future__ import annotations

import pandas as pd

from tradingagents.dataflows import onchain_store

METRICS = [
    "snt_idx_mean",
    "snt_idx_ewm3",
    "snt_cnt_z30",
    "snt_neg_share_7d",
    "snt_disp_7d",
]

SOURCE = "sentiment_index"
STATUS = "final"
AS_OF_OFFSET = pd.Timedelta(hours=25)  # end-of-day (24h) + 1h


def _neg_share(s: pd.Series) -> float:
    return float((s < 0).mean())


def _aggregate_one_coin(coin: str, g: pd.DataFrame) -> pd.DataFrame:
    """`g` is indexed by day (tz-aware, UTC) for a single coin, already
    holding the raw daily aggregates for the days that had >=1 article.
    Reindexes to the full daily calendar spanning this coin's data and
    computes the derived (EWM/rolling) metrics."""
    g = g.sort_index()
    full_idx = pd.date_range(g.index.min(), g.index.max(), freq="D")
    g = g.reindex(full_idx)

    # No-news days: explicit neutral signal. snt_disp_7d_raw / snt_neg stay
    # NaN (undefined for zero articles) so the rolling means below skip them.
    g["snt_idx_mean"] = g["snt_idx_mean"].fillna(0.0)
    g["snt_cnt"] = g["snt_cnt"].fillna(0)

    g["snt_idx_ewm3"] = g["snt_idx_mean"].ewm(halflife=3).mean()

    roll_cnt = g["snt_cnt"].rolling(30, min_periods=10)
    g["snt_cnt_z30"] = (g["snt_cnt"] - roll_cnt.mean()) / roll_cnt.std()

    g["snt_neg_share_7d"] = g["snt_neg"].rolling(7, min_periods=3).mean()
    g["snt_disp_7d"] = g["snt_disp_7d_raw"].rolling(7, min_periods=3).mean()

    g["coin"] = coin
    return g


def aggregate(scores: pd.DataFrame) -> pd.DataFrame:
    """Roll up per-article `scores` into daily long-format index-store rows.

    Input columns: `event_ts, as_of_ts, coin, engine, score_norm, relevant,
    content_sha` (as_of_ts/engine/content_sha are not needed downstream and
    are ignored). Output columns match `onchain_store.SCHEMA_COLS`:
    `event_ts, as_of_ts, coin, metric, value, source, status`.

    Only non-NaN metric values are emitted (warm-up days for the z-score /
    rolling metrics are dropped, never upserted).
    """
    if scores.empty:
        return pd.DataFrame(columns=onchain_store.SCHEMA_COLS)

    df = scores.copy()
    df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
    if "relevant" in df.columns:
        # Defensive no-op under current invariants: score parquets never
        # persist non-relevant rows (see score_sentiment_corpus.py), but
        # guard here too in case that invariant ever changes upstream.
        df = df[df["relevant"].astype(bool)]
    if df.empty:
        return pd.DataFrame(columns=onchain_store.SCHEMA_COLS)

    df["_day"] = df["event_ts"].dt.floor("D")

    base = df.groupby(["coin", "_day"]).agg(
        snt_idx_mean=("score_norm", "mean"),
        snt_cnt=("score_norm", "size"),
        snt_disp_7d_raw=("score_norm", "std"),
        snt_neg=("score_norm", _neg_share),
    )

    per_coin_frames = []
    for coin, g in base.groupby(level="coin"):
        g = g.droplevel("coin")
        per_coin_frames.append(_aggregate_one_coin(coin, g))
    per_coin = pd.concat(per_coin_frames)

    long_rows = []
    for metric in METRICS:
        sub = per_coin[["coin", metric]].dropna(subset=[metric])
        if sub.empty:
            continue
        sub = sub.rename(columns={metric: "value"}).reset_index(names="event_ts")
        sub["metric"] = metric
        long_rows.append(sub)

    if not long_rows:
        return pd.DataFrame(columns=onchain_store.SCHEMA_COLS)

    out = pd.concat(long_rows, ignore_index=True)
    out["as_of_ts"] = out["event_ts"] + AS_OF_OFFSET
    out["source"] = SOURCE
    out["status"] = STATUS
    return out[onchain_store.SCHEMA_COLS].reset_index(drop=True)
