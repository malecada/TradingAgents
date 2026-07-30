"""Cross-sectional crypto value signal (value_xs_t1).

Ratios are market cap per unit of network activity. Low ratio = cheap = long.
CapMrktCurUSD embeds price, so a cheap-looking coin is often just a coin that
fell -- the C2 reversal control in the dev runner exists to separate those.

Signal timing: features as of t-2 (CoinMetrics publication lag), positions
effective t+1 via run_ls_portfolio's own one-bar shift. Registered in
gates.json under value_xs_t1.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

METRIC_NUM = "CapMrktCurUSD"
METRIC_DEN = {"nvt_proxy": "TxCnt", "metcalfe_proxy": "AdrActCnt"}


def load_fundamentals(fund_dir: Path, asset_to_symbol: dict) -> dict[str, pd.DataFrame]:
    """Fundamentals keyed by perp symbol (not CoinMetrics asset id)."""
    out = {}
    for asset, symbol in asset_to_symbol.items():
        p = Path(fund_dir) / f"{asset}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        if df.index.tz is None:
            df.index = pd.to_datetime(df.index).tz_localize("UTC")
        out[symbol] = df.sort_index()
    return out


def value_ratio(fund: dict, metric: str, all_days: pd.DatetimeIndex,
                window: int = 30) -> pd.DataFrame:
    """Market cap over a ``window``-day mean of the activity denominator."""
    if metric not in METRIC_DEN:
        raise ValueError(f"unknown metric {metric!r}")
    den_col = METRIC_DEN[metric]
    cols = {}
    for sym, df in fund.items():
        d = df.reindex(all_days)
        den = d[den_col].rolling(window, min_periods=window).mean()
        num = d[METRIC_NUM]
        r = num / den.where(den > 0)
        cols[sym] = r
    return pd.DataFrame(cols, index=all_days).sort_index(axis=1)


def zscore_signal(ratio: pd.DataFrame, lag_days: int = 2) -> pd.DataFrame:
    """log -> per-row cross-sectional z-score -> lag by ``lag_days`` bars."""
    lg = np.log(ratio.where(ratio > 0))
    mu = lg.mean(axis=1)
    sd = lg.std(axis=1, ddof=1)
    z = lg.sub(mu, axis=0).div(sd.where(sd > 0), axis=0)
    return z.shift(lag_days) if lag_days else z


def membership_mask(all_days: pd.DatetimeIndex, columns,
                    universe: dict) -> pd.DataFrame:
    """True where a symbol is in that month's PIT universe."""
    M = pd.DataFrame(False, index=all_days, columns=list(columns))
    months = sorted(universe)
    for i, m in enumerate(months):
        lo = pd.Timestamp(m, tz="UTC")
        hi = pd.Timestamp(months[i + 1], tz="UTC") if i + 1 < len(months) else None
        seg = M.loc[lo:] if hi is None else M.loc[lo:hi - pd.Timedelta(days=1)]
        cols = [c for c in universe[m] if c in M.columns]
        if len(seg) and cols:
            M.loc[seg.index, cols] = True
    return M


def simple_returns(klines: dict, all_days: pd.DatetimeIndex, columns) -> pd.DataFrame:
    """Simple close-to-close returns (cross-sectional convention, not log)."""
    cols = {}
    for sym in columns:
        df = klines.get(sym)
        if df is None:
            cols[sym] = pd.Series(np.nan, index=all_days)
            continue
        cols[sym] = df["close"].reindex(all_days).pct_change(fill_method=None)
    return pd.DataFrame(cols, index=all_days)


def control_signal(klines: dict, all_days: pd.DatetimeIndex, columns,
                   kind: str, window: int = 30, lag_days: int = 2) -> pd.DataFrame:
    """Control signals, oriented so HIGH value = short leg.

    ``vol``      : trailing realized volatility (short the volatile names).
    ``reversal`` : trailing return (short the recent winners).
    """
    R = simple_returns(klines, all_days, columns)
    if kind == "vol":
        raw = R.rolling(window, min_periods=window).std(ddof=1)
    elif kind == "reversal":
        raw = R.rolling(window, min_periods=window).sum()
    else:
        raise ValueError(f"unknown control {kind!r}")
    mu = raw.mean(axis=1)
    sd = raw.std(axis=1, ddof=1)
    z = raw.sub(mu, axis=0).div(sd.where(sd > 0), axis=0)
    return z.shift(lag_days) if lag_days else z
