"""PIT-correct sentiment feature construction for the pooled model dataset.

Reads two bitemporal stores and produces a wide, date-indexed frame whose
every row at date D only contains values that would have been visible to a
caller at ``as_of_ts <= end of day D`` (same discipline as
``onchain_features.build_pit_onchain_features``):

- ``sentiment_index_store.load_index`` — long-format rows
  ``[event_ts, as_of_ts, coin, metric, value, source, status]`` produced by
  ``tradingagents.sentiment.daily_index.aggregate`` (per-coin metrics plus a
  synthetic ``coin="global"`` slice).
- ``{TRADINGAGENTS_DATA_ROOT}/sentiment/fng/fng.parquet`` — the daily
  alternative.me Fear & Greed index (``fng_store`` schema).

PIT alignment reuses ``onchain_features._pit_align`` (merge_asof, direction
="backward", on ``as_of_ts``) rather than duplicating that logic.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from tradingagents.dataflows import sentiment_index_store
from tradingagents.dataflows.onchain_features import COIN_ALIAS, _pit_align

# Per-coin metrics pulled straight from the index store (column name == metric name).
PER_COIN_METRICS = [
    "snt_idx_mean",
    "snt_idx_ewm3",
    "snt_cnt_z30",
    "snt_neg_share_7d",
    "snt_disp_7d",
]

# Global-coin metrics (coin="global" rows), metric -> output column name.
GLOBAL_METRIC_TO_COL = {
    "snt_idx_ewm3": "snt_g_idx_ewm3",
    "snt_cnt_z30": "snt_g_cnt_z30",
}

FNG_COLS = ["fng_level", "fng_ema_168d", "fng_dev"]

# Exact, ordered column set the function guarantees.
FEATURE_COLS = (
    PER_COIN_METRICS + list(GLOBAL_METRIC_TO_COL.values()) + FNG_COLS
)


def _end_of_day(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Map each calendar day to its end-of-day instant (23:59:59.999999).

    The PIT rule is "usable on day D iff as_of_ts <= end of day D", not
    "<= midnight of D" — a row scored a few hours after midnight (e.g. the
    +25h offset `daily_index.py` uses) must still count as visible on its
    own event day. `_pit_align` compares literal instants, so callers must
    pre-shift the query instants to day-end themselves.
    """
    return idx.normalize() + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)


def _align_and_reindex(
    sorted_idx: pd.DatetimeIndex,
    orig_idx: pd.DatetimeIndex,
    series: pd.DataFrame,
    col_name: str,
) -> pd.Series:
    """PIT-align `series` onto `sorted_idx` (chronological, as `_pit_align`
    requires) using end-of-day cutoffs, then remap onto `orig_idx`'s
    original row order with the calendar-day labels restored."""
    cutoff_idx = _end_of_day(sorted_idx)
    aligned = _pit_align(cutoff_idx, series, col_name).astype("float64")
    aligned.index = sorted_idx
    return aligned.reindex(orig_idx)


def build_sentiment_features(
    coin: str,
    dates: pd.DatetimeIndex,
    engine: str = "llm",
) -> pd.DataFrame:
    """Build a PIT-safe sentiment feature frame for `coin` over `dates`.

    Returns a DataFrame indexed by exactly `dates` (same order, same tz-ness
    as given) with the 10 columns in `FEATURE_COLS`. Never raises for empty
    stores or a missing F&G file — those simply yield all-NaN columns.
    """
    orig_idx = pd.DatetimeIndex(dates)
    out = pd.DataFrame(index=orig_idx, columns=FEATURE_COLS, dtype="float64")
    if len(orig_idx) == 0:
        return out

    idx_utc = pd.to_datetime(orig_idx, utc=True)
    sorted_idx = idx_utc.sort_values()

    alias = COIN_ALIAS.get(coin.lower(), coin.lower())
    start = "1970-01-01"
    end = (idx_utc.max() + pd.Timedelta(days=3)).strftime("%Y-%m-%d")

    try:
        rows = sentiment_index_store.load_index(engine, [alias, "global"], start, end)
    except Exception:
        rows = pd.DataFrame(columns=["event_ts", "as_of_ts", "coin", "metric", "value", "source", "status"])

    if not rows.empty:
        for metric in PER_COIN_METRICS:
            series = rows.loc[
                (rows["coin"] == alias) & (rows["metric"] == metric),
                ["as_of_ts", "value"],
            ]
            out[metric] = _align_and_reindex(sorted_idx, idx_utc, series, metric).values
        for metric, col in GLOBAL_METRIC_TO_COL.items():
            series = rows.loc[
                (rows["coin"] == "global") & (rows["metric"] == metric),
                ["as_of_ts", "value"],
            ]
            out[col] = _align_and_reindex(sorted_idx, idx_utc, series, col).values

    data_root = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", "data"))
    fng_path = data_root / "sentiment" / "fng" / "fng.parquet"
    if fng_path.exists():
        fng_df = pd.read_parquet(fng_path)
        fng_series = fng_df[["as_of_ts", "value"]]
        cutoff_idx = _end_of_day(sorted_idx)
        fng_level_sorted = _pit_align(cutoff_idx, fng_series, "fng_level").astype("float64")
        fng_level_sorted.index = sorted_idx
        fng_ema_sorted = fng_level_sorted.ewm(halflife=84).mean()
        fng_dev_sorted = fng_level_sorted - fng_ema_sorted

        out["fng_level"] = fng_level_sorted.reindex(idx_utc).values
        out["fng_ema_168d"] = fng_ema_sorted.reindex(idx_utc).values
        out["fng_dev"] = fng_dev_sorted.reindex(idx_utc).values

    return out
