# tradingagents/research/onchain_b7/features7.py
"""Multi-scale, deseasonalised features of hourly on-chain series (spec §4.1), event-time
features from the large-transfer records (§4.2) and explicit interactions (§4.2). Every value
at hour h uses data up to the end of hour h only."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b4.dataset4 import zscore

WEEK = 168
HOUR_NS = 3_600_000_000_000


def _regular_hourly(index):
    idx = pd.DatetimeIndex(index)
    if len(idx) > 1 and not (np.diff(idx.asi8) == HOUR_NS).all():
        raise ValueError('a complete hourly index is required')
    return idx


def seasonal_excess(x, weeks, min_occ):
    """log1p(x) − log1p(median of the same weekday-hour slot over the previous `weeks` weeks).
    Slots recur every 168 rows of a complete hourly index, so the profile is the median over
    the values 168, 336, …, 168·weeks rows earlier; NaN until `min_occ` of them exist."""
    _regular_hourly(x.index)
    v = x.clip(lower=0).to_numpy(float)
    n = len(v)
    prev = np.full((weeks, n), np.nan)
    for w in range(1, weeks + 1):
        if w * WEEK < n:
            prev[w - 1, w * WEEK:] = v[:n - w * WEEK]
    ok = np.isfinite(prev).sum(axis=0) >= max(1, min_occ)
    prof = np.full(n, np.nan)
    prof[ok] = np.nanmedian(prev[:, ok], axis=0)
    out = np.log1p(v) - np.log1p(prof)
    out[~ok] = np.nan
    return pd.Series(out, index=x.index)


def multiscale(raw, c):
    """Six features per series: excess over the weekly profile, z-score against the previous
    week, z-scores of the 6-, 24- and 168-hour sums against longer windows, and the burst
    against the previous 24 hours. Windows end at hour h, the hour's own value included."""
    out = {}
    for name in raw.columns:
        x = raw[name].clip(lower=0)
        lx = np.log1p(x)
        out[f'n_{name}__ex1'] = seasonal_excess(x, c['profile_weeks'], c['profile_min']).clip(-c['clip'], c['clip'])
        out[f'n_{name}__z1'] = zscore(lx, c['z1_window'], c['z1_min'], c['clip'])
        for k, key in ((6, 's6'), (24, 's24'), (168, 's168')):
            s = np.log1p(x.rolling(k, min_periods=k).sum())
            out[f'n_{name}__{key}z'] = zscore(s, c[f'{key}_window'], c[f'{key}_min'], c['clip'])
        prev = x.shift(1).rolling(c['burst_window'], min_periods=c['burst_window']).mean()
        out[f'n_{name}__burst'] = (lx - np.log1p(prev)).clip(-c['clip'], c['clip'])
    return pd.DataFrame(out, index=raw.index)


def event_hours(large, index, thresholds, cap):
    """log1p(hours since the last stablecoin exchange deposit of at least the threshold), capped
    at `cap`; an event inside hour h counts at the end of hour h (zero hours since); before the
    first event the value is the cap."""
    idx = _regular_hourly(index)
    dep = large[(large['token'] > 0) & (large['direction'] == 1)]
    pos = np.arange(len(idx), dtype=float)
    out = {}
    for name, thr in thresholds.items():
        hours = pd.to_datetime(dep.loc[dep['amount'] >= thr, 'ts'].to_numpy(), unit='s').floor('h')
        hit = idx.isin(hours)
        last = pd.Series(np.where(hit, pos, np.nan)).ffill().to_numpy()
        since = np.where(np.isnan(last), cap, np.minimum(pos - last, cap))
        out[f'ev_since_{name}'] = np.log1p(since)
    return pd.DataFrame(out, index=idx)


def interactions(table, spec):
    return pd.DataFrame({name: table[a] * table[b] for name, a, b in spec}, index=table.index)
