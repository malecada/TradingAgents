"""Positioning stress index — pre-registered spec docs/superpowers/specs/2026-07-14-stress-ews-prereg.md."""
from pathlib import Path

import numpy as np
import pandas as pd

COMPONENTS = ["z_fund", "z_oi", "z_liq", "z_fg"]


def zscore_365(s: pd.Series) -> pd.Series:
    mean = s.rolling(365, min_periods=180).mean()
    std = s.rolling(365, min_periods=180).std()
    std = std.replace(0.0, np.nan)
    return (s - mean) / std


def _coin_components(deriv_path: Path) -> pd.DataFrame:
    df = pd.read_parquet(deriv_path).sort_index()
    lag = df.shift(1)  # causal: value dated D uses data <= D-1
    out = pd.DataFrame(index=df.index)
    out["z_fund"] = zscore_365(lag["funding_rate_ma7"])
    out["z_oi"] = zscore_365(lag["oi_close"] / lag["oi_close"].shift(30) - 1.0)
    out["z_liq"] = zscore_365(lag["liq_total_usd"] / lag["oi_close"])
    return out


def _fng_component(fng_path: Path) -> pd.Series:
    fng = pd.read_parquet(fng_path)
    s = (
        fng.assign(d=pd.to_datetime(fng["event_ts"], utc=True).dt.normalize())
        .set_index("d")["value"]
        .astype(float)
        .sort_index()
    )
    s = s[~s.index.duplicated(keep="last")].shift(1)
    return zscore_365((s - 50.0).abs())


def build_components(coins: list[str], deriv_dir: Path, fng_path: Path) -> pd.DataFrame:
    per_coin = [_coin_components(Path(deriv_dir) / f"{c}.parquet") for c in coins]
    idx = per_coin[0].index
    for p in per_coin[1:]:
        idx = idx.union(p.index)
    ew = sum(p.reindex(idx) for p in per_coin) / len(per_coin)
    ew["z_fg"] = _fng_component(fng_path).reindex(idx)
    return ew


def composite_warn(components: pd.DataFrame, component_set: list[str], k: float) -> pd.DataFrame:
    sub = components[component_set]
    composite = sub.mean(axis=1).where(~sub.isna().any(axis=1))
    warn = np.zeros(len(composite), dtype=bool)
    active = False
    vals = composite.to_numpy()
    for i, v in enumerate(vals):
        if np.isnan(v):
            active = False
        elif active:
            active = v >= k - 0.25
        else:
            active = v >= k
        warn[i] = active
    return pd.DataFrame({"composite": composite, "warn": warn}, index=components.index)
