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


# ── stress_ews2 (charter 2026-09-04): funding from the 799-symbol settlement store ──

def daily_funding_from_store(store: pd.DataFrame) -> pd.Series:
    """Daily MEAN of the 8-hour funding settlements (UTC day of the settlement stamp).

    Coinglass's daily `funding_rate` equals this mean (parity checked 2026-09-04:
    corr 1.0, store daily sum = 3 x Coinglass on the 2021-11..2026-05 overlap)."""
    s = store["fundingRate"].astype(float)
    return s.groupby(s.index.tz_convert("UTC").normalize()).mean().sort_index()


def _coin_components_store(deriv_path: Path, funding_store_path: Path) -> pd.DataFrame:
    df = pd.read_parquet(deriv_path).sort_index()
    fr = daily_funding_from_store(pd.read_parquet(funding_store_path))
    idx = df.index.union(fr.index)
    df = df.reindex(idx)
    fr = fr.reindex(idx)
    ma7 = fr.rolling(7, min_periods=7).mean()
    lag = df.shift(1)
    out = pd.DataFrame(index=idx)
    out["z_fund"] = zscore_365(ma7.shift(1))
    out["z_oi"] = zscore_365(lag["oi_close"] / lag["oi_close"].shift(30) - 1.0)
    out["z_liq"] = zscore_365(lag["liq_total_usd"] / lag["oi_close"])
    out["funding_rate_ma7_store"] = ma7
    out["funding_rate_ma7_parent"] = df["funding_rate_ma7"]
    return out


def build_components_store(coins: list[str], symbols: list[str], deriv_dir: Path,
                           funding_dir: Path, fng_path: Path) -> pd.DataFrame:
    """As build_components, with z_fund from the settlement store (coins and
    symbols aligned pairwise, e.g. ['bitcoin','ethereum'] / ['BTCUSDT','ETHUSDT'])."""
    per_coin = [_coin_components_store(Path(deriv_dir) / f"{c}.parquet", Path(funding_dir) / f"{s}.parquet")
                for c, s in zip(coins, symbols)]
    idx = per_coin[0].index
    for p in per_coin[1:]:
        idx = idx.union(p.index)
    ew = sum(p.reindex(idx) for p in per_coin) / len(per_coin)
    ew["z_fg"] = _fng_component(fng_path).reindex(idx)
    return ew
