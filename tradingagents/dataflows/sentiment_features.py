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
    +25h offset `daily_index.py` uses, which lands at 01:00 on D+1) must
    still count as visible by end-of-day D+1, one extra day of conservatism
    rather than being visible on its own event day D. `_pit_align` compares
    literal instants, so callers must pre-shift the query instants to
    day-end themselves.
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
        try:
            fng_df = pd.read_parquet(fng_path)
            fng_series = fng_df[["as_of_ts", "value"]].copy()
            fng_series["as_of_ts"] = pd.to_datetime(fng_series["as_of_ts"], utc=True)
            fng_series = fng_series.sort_values("as_of_ts")
            fng_first_day = pd.to_datetime(fng_df["event_ts"], utc=True).min().normalize()
        except Exception:  # malformed file → degrade to NaN cols, never raise
            fng_series = pd.DataFrame(columns=["as_of_ts", "value"])
            fng_first_day = None
        if not fng_series.empty:
            # Window-invariance: the EWM must not restart at each caller's
            # window start — otherwise the same (day, fng_dev) pair differs
            # across walk-forward calls with different lookbacks. Align the
            # level over the FULL daily calendar from fng's own first event
            # day up to the max requested day (mirrors the full_idx pattern
            # in onchain_features.build_pit_onchain_features), run the EWM
            # on that full series, then reindex down to the caller's dates.
            last_day = sorted_idx.max().normalize()
            if fng_first_day <= last_day:
                full_days = pd.date_range(fng_first_day, last_day, freq="D", tz="UTC")
            else:
                full_days = pd.DatetimeIndex(sorted_idx.normalize().unique()).sort_values()
            fng_level_full = _pit_align(
                _end_of_day(full_days), fng_series, "fng_level"
            ).astype("float64")
            fng_level_full.index = full_days
            fng_ema_full = fng_level_full.ewm(halflife=84).mean()
            fng_dev_full = fng_level_full - fng_ema_full

            day_idx = idx_utc.normalize()
            out["fng_level"] = fng_level_full.reindex(day_idx).values
            out["fng_ema_168d"] = fng_ema_full.reindex(day_idx).values
            out["fng_dev"] = fng_dev_full.reindex(day_idx).values

    return out
