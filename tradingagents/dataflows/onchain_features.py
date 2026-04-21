"""PIT-correct on-chain feature construction from the bitemporal store.

Reads raw metrics written by ``backfill_onchain.py`` and returns a wide,
date-indexed DataFrame whose every row at date t only contains values that
would have been visible to a caller at as_of_ts <= t. Achieved via
``pandas.merge_asof`` on as_of_ts.

Derived features (rolling) are computed on the PIT-aligned series, so no
look-ahead leaks.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from . import onchain_store

# Coin → CM asset / DefiLlama slug mapping for feature lookup.
COIN_ALIAS = {
    "bitcoin": "btc",
    "btc": "btc",
    "ethereum": "eth",
    "eth": "eth",
    "binancecoin": "bnb",
    "bnb": "bnb",
}

# Raw metrics pulled per coin (what we expect to exist in the store).
RAW_METRICS_BY_COIN = {
    "btc": [
        "AdrActCnt", "TxCnt", "HashRate", "CapMVRVCur", "CapMrktCurUSD",
        "FeeTotNtv", "FlowInExUSD", "FlowOutExUSD", "IssTotUSD", "SplyCur",
        "PriceUSD",
    ],
    "eth": [
        "AdrActCnt", "TxCnt", "CapMVRVCur", "CapMrktCurUSD", "FeeTotNtv",
        "FlowInExUSD", "FlowOutExUSD", "IssTotUSD", "SplyCur", "PriceUSD",
        "tvl_ethereum",
    ],
    "bnb": [
        "tvl_bsc",
    ],
}

GLOBAL_METRICS = ["stablecoin_mcap_total"]


def _load_metric_series(
    coin: str, metric: str, root: Path,
) -> pd.DataFrame:
    """Load raw rows for (coin, metric) sorted by as_of_ts ascending.

    Returns empty DataFrame if nothing present.
    """
    glob = f"{root}/*/*.parquet"
    import duckdb
    con = duckdb.connect(":memory:")
    try:
        try:
            con.execute(f"CREATE VIEW onchain AS SELECT * FROM read_parquet('{glob}')")
        except duckdb.IOException:
            return pd.DataFrame(columns=["event_ts", "as_of_ts", "value"])
        sql = """
        SELECT event_ts, as_of_ts, value
        FROM onchain
        WHERE coin = ? AND metric = ?
        ORDER BY as_of_ts ASC, event_ts ASC
        """
        return con.execute(sql, [coin.lower(), metric]).fetchdf()
    finally:
        con.close()


def _pit_align(
    dates: pd.DatetimeIndex, series: pd.DataFrame, col_name: str,
) -> pd.Series:
    """Align a (event_ts, as_of_ts, value) series to a DatetimeIndex of dates.

    Each output date t gets the value whose as_of_ts is the maximum
    as_of_ts <= t. If no such row exists, NaN.
    """
    if series.empty:
        return pd.Series(index=dates, dtype="float64", name=col_name)
    left = pd.DataFrame({"date": dates})
    # merge_asof needs sorted keys. as_of_ts is already ascending per loader.
    right = series[["as_of_ts", "value"]].copy()
    # Normalize both sides to datetime64[ns, UTC] — Parquet/DuckDB returns
    # microsecond precision which otherwise triggers merge_asof dtype errors.
    right["as_of_ts"] = pd.to_datetime(right["as_of_ts"], utc=True).astype(
        "datetime64[ns, UTC]"
    )
    left["date"] = pd.to_datetime(left["date"], utc=True).astype(
        "datetime64[ns, UTC]"
    )
    merged = pd.merge_asof(
        left.sort_values("date"),
        right.sort_values("as_of_ts"),
        left_on="date", right_on="as_of_ts",
        direction="backward",
    )
    out = pd.Series(merged["value"].values, index=merged["date"], name=col_name)
    out.index = dates
    return out


def build_pit_onchain_features(
    coin: str,
    dates: Iterable[datetime],
    metrics: Optional[Iterable[str]] = None,
    include_global: bool = True,
    include_derived: bool = True,
    root: Path = onchain_store.DEFAULT_ROOT,
) -> pd.DataFrame:
    """Build a wide, date-indexed PIT on-chain feature frame for a coin.

    Each row at date t has only values with as_of_ts <= t (strict PIT).
    Rolling derived features (z-scores, Puell Multiple) are computed on
    the full PIT-aligned series so long windows can stabilize even when
    the caller requests only a short slice of dates.
    """
    alias = COIN_ALIAS.get(coin.lower(), coin.lower())
    if metrics is None:
        metric_list = list(RAW_METRICS_BY_COIN.get(alias, []))
    else:
        metric_list = list(metrics)

    idx = pd.DatetimeIndex(
        [pd.to_datetime(d, utc=True) for d in dates]
    ).sort_values()
    idx.name = "date"

    # Build the full PIT-aligned frame over union(stored event_ts, query dates)
    # so rolling derivations see all history, then reindex to requested dates.
    metric_series: dict[str, pd.DataFrame] = {}
    all_as_of: list[pd.Timestamp] = []
    for m in metric_list:
        s = _load_metric_series(alias, m, root)
        metric_series[f"oc_{m}"] = s
        if not s.empty:
            all_as_of.extend(pd.to_datetime(s["as_of_ts"], utc=True).tolist())
    if include_global:
        for gm in GLOBAL_METRICS:
            s = _load_metric_series("global", gm, root)
            metric_series[f"oc_{gm}"] = s
            if not s.empty:
                all_as_of.extend(pd.to_datetime(s["as_of_ts"], utc=True).tolist())

    if all_as_of:
        as_of_idx = pd.DatetimeIndex(sorted(set(all_as_of)))
    else:
        as_of_idx = pd.DatetimeIndex([], tz="UTC")

    full_idx = idx.union(as_of_idx).sort_values()
    full_idx = full_idx.tz_convert("UTC") if full_idx.tz is not None else full_idx.tz_localize("UTC")
    full_idx = full_idx.astype("datetime64[ns, UTC]")
    full_idx.name = "date"

    wide = pd.DataFrame(index=full_idx)
    for col, series in metric_series.items():
        wide[col] = _pit_align(full_idx, series, col).astype(float)

    if include_derived:
        wide = _add_derived(wide, alias)

    # Return only the dates the caller asked for, but with all columns.
    return wide.reindex(idx)


def _add_derived(df: pd.DataFrame, alias: str) -> pd.DataFrame:
    """Attach rolling / composite features. All derivations use the
    PIT-aligned columns already in `df`, so no leakage introduced here."""
    out = df.copy()

    mvrv_col = "oc_CapMVRVCur"
    if mvrv_col in out.columns:
        roll = out[mvrv_col].rolling(window=365, min_periods=60)
        out["oc_mvrv_z_1y"] = (out[mvrv_col] - roll.mean()) / roll.std()

    fi, fo = "oc_FlowInExUSD", "oc_FlowOutExUSD"
    if fi in out.columns and fo in out.columns:
        out["oc_net_flow_usd"] = out[fi] - out[fo]
        nf_roll = out["oc_net_flow_usd"].rolling(window=30, min_periods=5)
        out["oc_net_flow_z_30d"] = (
            (out["oc_net_flow_usd"] - nf_roll.mean()) / nf_roll.std()
        )

    iss = "oc_IssTotUSD"
    if iss in out.columns:
        iss_ma = out[iss].rolling(window=365, min_periods=60).mean()
        out["oc_puell_multiple"] = out[iss] / iss_ma

    aa = "oc_AdrActCnt"
    if aa in out.columns:
        aa_roll = out[aa].rolling(window=30, min_periods=5)
        out["oc_active_addr_z_30d"] = (
            (out[aa] - aa_roll.mean()) / aa_roll.std()
        )

    # TVL % change (DefiLlama)
    for tvl_col in ("oc_tvl_ethereum", "oc_tvl_bsc"):
        if tvl_col in out.columns:
            out[f"{tvl_col}_chg_7d"] = out[tvl_col].pct_change(7)

    # Stablecoin mcap % change
    sc = "oc_stablecoin_mcap_total"
    if sc in out.columns:
        out[f"{sc}_chg_7d"] = out[sc].pct_change(7)

    return out
