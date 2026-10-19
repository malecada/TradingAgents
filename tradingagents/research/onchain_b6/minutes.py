# tradingagents/research/onchain_b6/minutes.py
"""Minute-level event study (spec §6): Binance 1-minute closes, very large deposit and
withdrawal events from the large-transfer records, responses from the next full minute,
placebo minutes matched by year and hour of day."""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from ..onchain_b4.screen4 import interval
from ..onchain_b5.deribit import with_retries

URL = 'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&startTime={ms}&limit=1000'
MIN_MS = 60_000


def fetch(get, symbol, start, end, sleep=time.sleep, pause=0.05, retries=(5, 30, 120)):
    ms, stop = int(pd.Timestamp(start, tz='UTC').timestamp() * 1000), int(pd.Timestamp(end, tz='UTC').timestamp() * 1000)
    vals = {}
    while ms < stop:
        url = URL.format(symbol=symbol, ms=ms)
        rows = json.loads(with_retries(lambda: get(url), list(retries), sleep))
        for k in rows:
            if k[0] < stop:
                vals[int(k[0])] = float(k[4])
        if len(rows) < 1000:
            break
        ms = rows[-1][0] + MIN_MS
        sleep(pause)
    keys = sorted(vals)
    return pd.Series([vals[k] for k in keys], index=pd.to_datetime(keys, unit='ms'), name='close')


def select_events(large, cfg):
    m = cfg['minutes']
    tiers = m['tiers']
    df = large.copy()
    stable = df['token'] > 0
    thr = lambda i: np.where(stable, tiers['stable_usd'][i], tiers['eth'][i])
    df['minute'] = pd.to_datetime(df['ts'], unit='s').dt.floor('min')
    out = []
    for tier in (1, 2):                                            # nested: tier 1 holds every event of tier 2
        sub = df[df['amount'] >= thr(tier - 1)]
        for direction, g in sub.sort_values('ts').groupby('direction'):
            last = None
            for _, r in g.iterrows():
                if last is None or (r['minute'] - last) >= pd.Timedelta(minutes=m['spacing_min']):
                    out.append({'minute': r['minute'], 'direction': int(direction), 'tier': int(tier), 'token': int(r['token'])})
                    last = r['minute']
    return pd.DataFrame(out, columns=['minute', 'direction', 'tier', 'token']).sort_values('minute').reset_index(drop=True)


def _stat(x, block, gate_draws=2000, seed=20261020):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < max(2, block):
        return {'mean': float(x.mean()) if len(x) else np.nan, 'lo': np.nan, 'hi': np.nan}
    lo, hi = interval(x, block, gate_draws, seed, 100)
    return {'mean': float(x.mean()), 'lo': lo, 'hi': hi}


def responses(minutes_idx, closes, m):
    full = closes.reindex(pd.date_range(closes.index.min(), closes.index.max(), freq='min'))
    lc = np.log(full)
    r2 = lc.diff() ** 2
    ev = pd.DatetimeIndex(minutes_idx)
    out = {'n': int(len(ev))}
    pre = r2.rolling(m['pre_vol_min'], min_periods=m['pre_vol_min']).sum().shift(1)      # minutes m-60 .. m-1
    for k in m['k_vol']:
        post = r2.rolling(k, min_periods=k).sum().shift(-k)             # sum over minutes t+1 .. t+k at index t
        with np.errstate(divide='ignore', invalid='ignore'):       # zero pre-event variance -> non-finite, dropped in _stat
            val = np.log(post.reindex(ev).to_numpy() / k) - np.log(pre.reindex(ev).to_numpy() / m['pre_vol_min'])
        out[f'vol{k}'] = _stat(val, m['block'])
    for k in m['k_ret']:
        out[f'ret{k}'] = _stat((lc.shift(-k) - lc).reindex(ev).to_numpy(), m['block'])
    out['pre_ret'] = _stat((lc.shift(1) - lc.shift(1 + m['pre_ret_min'])).reindex(ev).to_numpy(), m['block'])   # ends at m-1
    return out


def placebo(events, closes, m, exclude=None):
    """One random minute per event from the same year and hour of day, at least `placebo_gap_min`
    from every minute in `exclude` (all events of the study, not only this group)."""
    rng = np.random.default_rng(m['seed'])
    ev = pd.DatetimeIndex(events['minute']).sort_values()
    taken = np.sort(pd.DatetimeIndex(exclude if exclude is not None else ev).to_numpy().astype('datetime64[m]').astype(np.int64))
    gap = m['placebo_gap_min']
    mins = closes.index.to_numpy().astype('datetime64[m]').astype(np.int64)
    years, hours = closes.index.year.to_numpy(), closes.index.hour.to_numpy()
    pools = {}
    out = []
    for e in ev:
        key = (e.year, e.hour)
        if key not in pools:
            pool = mins[(years == e.year) & (hours == e.hour)]
            if len(pool) and len(taken):
                j = np.searchsorted(taken, pool)
                left = np.where(j > 0, pool - taken[np.maximum(j - 1, 0)], np.iinfo(np.int64).max)
                right = np.where(j < len(taken), taken[np.minimum(j, len(taken) - 1)] - pool, np.iinfo(np.int64).max)
                pool = pool[np.minimum(left, right) >= gap]
            pools[key] = pool
        ok = pools[key]
        if len(ok):
            out.append(pd.Timestamp(int(rng.choice(ok)), unit='m'))
    return pd.DatetimeIndex(out)
