# tradingagents/research/onchain_b7/targets7.py
"""Range features from 1-minute closes (spec §4.3) and the jump and largest-move targets
(§5). Hour h is the bar [h, h+1); the close of minute h:59 is the decision-time price, and
the next k hours are the minutes h+1:00 … h+k:59."""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN = pd.Timedelta(minutes=1)
H = pd.Timedelta(hours=1)


def _minutes(closes):
    s = closes.sort_index()
    start, end = s.index.min().floor('h'), (s.index.max() + MIN).ceil('h') - MIN
    return s.reindex(pd.date_range(start, end, freq='min'))


def range_features(closes, index, c):
    m = _minutes(closes)
    g = m.groupby(m.index.floor('h'))
    rng = np.log(g.max() / g.min()).where(g.count() >= c['min_minutes'])
    r = rng.reindex(index)
    f = pd.DataFrame(index=index)
    f['rg_range1'] = r
    f['rg_range24'] = r.rolling(c['window24'], min_periods=c['window24']).mean()
    return f.replace([np.inf, -np.inf], np.nan)


def jump_targets(bars, c):
    b = bars.reindex(pd.date_range(bars.index.min(), bars.index.max(), freq='h'))
    lc = np.log(b['close'])
    r = lc.diff()
    sigma = np.sqrt((r ** 2).rolling(c['sigma_window'], min_periods=c['sigma_min']).mean())
    t = pd.DataFrame(index=b.index)
    for k in (6, 24):
        move = (lc.shift(-k) - lc).abs()
        thr = c['mult'] * sigma * np.sqrt(k)
        t[f'J{k}'] = (move > thr).astype(float).where(move.notna() & thr.notna())
    return t


def mmax_targets(closes, index, c):
    """log of the largest absolute `spacing_min`-minute log return with both ends at or after
    the decision-time close (minute h:59) and inside the next k hours: returns at minutes
    h+1:(spacing−1) … h+k:59, a window of 60k − spacing + 1 values ending at minute h+k:59;
    NaN unless at least `min_share` of the window's returns exist."""
    m = _minutes(closes)
    lc = np.log(m)
    sp = c['spacing_min']
    r = (lc - lc.shift(sp)).abs()
    out = pd.DataFrame(index=index)
    for k in (6, 24):
        w = 60 * k - sp + 1
        mx = r.rolling(w, min_periods=int(np.ceil(c['min_share'] * w))).max()
        val = mx.reindex(pd.DatetimeIndex(index) + (k + 1) * H - MIN).to_numpy(float)
        out[f'M{k}'] = np.log(np.maximum(val, c['floor']))
    return out
