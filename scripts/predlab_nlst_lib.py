"""Shared library for the nlst new-listing / low-cap discovery cycle.

Charter: docs/superpowers/specs/2026-08-26-newlist-charter.md
Gates key: predlab_nlst (registered 2026-08-26, pre-result, user-approved).

All position PnL uses simple returns (house rule). Event-study conventions:
bar 0 = first daily bar in store (possibly partial day), entry at close of
bar 1, horizon-H cum return spans bars 2..1+H. Funding-adjusted for a LONG
holder: daily net r = pct_change - funding_daily (longs pay positive funding);
cum = prod(1 + r) - 1. Unit-tested in tests/predlab/test_nlst_lib.py before
first registered use.
"""

from __future__ import annotations

from math import comb
from pathlib import Path

import numpy as np
import pandas as pd

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predlab_xfam_lib import (  # noqa: E402  (reused house stats/bookkeeping)
    ann_sr,
    bh_fdr,
    ledger_append,
    nw_tstat,
    year_sign_consistency,
)

OUT_DIR = ROOT / "data" / "predlab" / "nlst"
DEV = ("2021-01-01", "2025-03-31")
HOLDOUT = ("2025-04-01", "2026-07-01")
HORIZONS_PERP = (5, 10, 20)
HORIZONS_X = (5, 10)
HORIZONS_DEX = (3, 7, 14)
UNI_FEE = 0.003

__all__ = [
    "ann_sr", "bh_fdr", "ledger_append", "nw_tstat", "year_sign_consistency",
    "OUT_DIR", "DEV", "HOLDOUT", "HORIZONS_PERP", "HORIZONS_X", "HORIZONS_DEX",
    "listing_events", "daily_funding", "event_cum_returns", "sign_test_p",
    "concentration", "p0_stats", "write_result", "v2_buy", "v2_sell",
]


# ------------------------------------------------------------------ events


def listing_events(klines_dir: Path, dev: tuple[str, str] = DEV,
                   max_h: int = 20) -> pd.DataFrame:
    """Enumerate listing events: first daily bar per symbol in [dev0, dev1],
    clipped so bar 1 + max_h completes on or before dev1 (needs bar count
    1 + 1 + max_h from listing). Returns frame indexed by symbol with
    list_date, n_bars."""
    lo, hi = pd.Timestamp(dev[0], tz="UTC"), pd.Timestamp(dev[1], tz="UTC")
    rows = {}
    for p in sorted(klines_dir.glob("*.parquet")):
        idx = pd.read_parquet(p, columns=["close"]).index
        first = idx.min()
        if not (lo <= first <= hi):
            continue
        n_dev = int((idx <= hi).sum())
        if n_dev < 2 + max_h:  # bar0, bar1(entry), bars 2..1+max_h
            continue
        rows[p.stem] = {"list_date": first, "n_bars_dev": n_dev}
    return pd.DataFrame.from_dict(rows, orient="index").sort_values("list_date")


def daily_funding(funding_dir: Path, sym: str) -> pd.Series:
    """Daily sum of settlement funding rates (UTC-day bucket). Empty series
    if no file."""
    p = funding_dir / f"{sym}.parquet"
    if not p.exists():
        return pd.Series(dtype=np.float64)
    f = pd.read_parquet(p)["fundingRate"].astype(np.float64)
    return f.groupby(f.index.floor("D")).sum()


def event_cum_returns(close: pd.Series, fund_daily: pd.Series,
                      horizons=HORIZONS_PERP, entry_bar: int = 1) -> dict:
    """Funding-adjusted cum simple returns from close of bar `entry_bar`.

    Daily net (long) return of bar k (k > entry_bar):
        r_k = close[k]/close[k-1] - 1 - funding_daily[day_k]
    cum_H = prod_{k=entry+1..entry+H}(1 + r_k) - 1. Also returns price-only
    cum and funding-only sum per horizon. NaN if not enough bars.
    """
    c = close.dropna()
    out = {}
    for h in horizons:
        need = entry_bar + h + 1  # bars 0..entry+h inclusive
        if len(c) < need:
            out[f"ret{h}"] = np.nan
            out[f"px{h}"] = np.nan
            out[f"fund{h}"] = np.nan
            continue
        seg = c.iloc[entry_bar : entry_bar + h + 1]
        r = seg.pct_change().dropna()
        f = fund_daily.reindex(r.index.floor("D")).fillna(0.0).to_numpy()
        out[f"ret{h}"] = float(np.prod(1.0 + (r.to_numpy() - f)) - 1.0)
        out[f"px{h}"] = float(np.prod(1.0 + r.to_numpy()) - 1.0)
        out[f"fund{h}"] = float(f.sum())
    return out


# ------------------------------------------------------------------ stats


def sign_test_p(x: np.ndarray) -> float:
    """Two-sided exact binomial sign test vs p=0.5 (zeros dropped)."""
    x = np.asarray(x, dtype=np.float64)
    x = x[~np.isnan(x)]
    x = x[x != 0]
    n = len(x)
    if n == 0:
        return np.nan
    k = int((x > 0).sum())
    lo = min(k, n - k)
    p = sum(comb(n, i) for i in range(0, lo + 1)) / 2.0 ** n * 2.0
    return float(min(1.0, p))


def concentration(x: pd.Series) -> dict:
    """Top-1 |value| share of sum|values| + mean with/without the top event."""
    v = x.dropna()
    if len(v) == 0:
        return {"top_share": np.nan, "top_event": None,
                "mean": np.nan, "mean_ex_top": np.nan}
    top = v.abs().idxmax()
    denom = float(v.abs().sum())
    return {
        "top_share": float(abs(v.loc[top]) / denom) if denom > 0 else np.nan,
        "top_event": str(top),
        "mean": float(v.mean()),
        "mean_ex_top": float(v.drop(top).mean()) if len(v) > 1 else np.nan,
    }


def p0_stats(events: pd.DataFrame, col: str, date_col: str = "list_date",
             lag: int = 5) -> dict:
    """Full P0 stat block for one horizon column: NW t (events ordered by
    listing date), sign test, year consistency, concentration."""
    df = events.dropna(subset=[col]).sort_values(date_col)
    x = df[col].to_numpy()
    mean, t, p = nw_tstat(x, lag=lag)
    ser = pd.Series(df[col].to_numpy(), index=pd.DatetimeIndex(df[date_col]))
    return {
        "n": int(len(df)),
        "mean": mean, "nw_t": t, "nw_p": p,
        "median": float(np.median(x)) if len(x) else np.nan,
        "sign_p": sign_test_p(x),
        "years": year_sign_consistency(ser),
        "concentration": concentration(ser),
    }


# ------------------------------------------------------------------ dex math


def v2_buy(weth_in: float, r_weth: float, r_tok: float,
           fee: float = UNI_FEE) -> float:
    """Tokens received spending weth_in against reserves (constant product)."""
    eff = weth_in * (1.0 - fee)
    return eff * r_tok / (r_weth + eff)


def v2_sell(tok_in: float, r_weth: float, r_tok: float,
            fee: float = UNI_FEE) -> float:
    """WETH received selling tok_in against reserves (constant product)."""
    eff = tok_in * (1.0 - fee)
    return eff * r_weth / (r_tok + eff)


# ------------------------------------------------------------------ output


def write_result(cell: str, payload: dict) -> Path:
    from datetime import datetime, timezone

    from predlab_xfam_lib import git_commit_short

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / f"{cell}_result.json"
    import json

    payload = {"ts_utc": datetime.now(timezone.utc).isoformat(),
               "git_commit": git_commit_short(), **payload}
    p.write_text(json.dumps(payload, indent=1, default=str))
    return p
