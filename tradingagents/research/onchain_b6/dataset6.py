# tradingagents/research/onchain_b6/dataset6.py
"""B6 features and samples (spec §5): causal transforms of the hourly blocks, an hourly
near-expiry implied-volatility series, market features, and per-track samples."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b4 import dataset4
from ..onchain_b5 import implied
from ..onchain_b5.decisions import px_features

H = pd.Timedelta(hours=1)


def transform_raw(raw, c):
    out = {}
    for name in raw.columns:
        x = np.log1p(raw[name].clip(lower=0))
        out[f'{name}__h1z'] = dataset4.zscore(x, c['h1_window'], c['h1_min'], c['clip'])
        s24 = raw[name].rolling(24, min_periods=24).sum()
        out[f'{name}__d24z'] = dataset4.zscore(np.log1p(s24.clip(lower=0)), c['d24_window'], c['d24_min'], c['clip'])
    return pd.DataFrame(out, index=raw.index)


def iv_hourly(trades_for_day, days, min_trades, ffill_hours, implied_cfg):
    vals = {}
    for day in days:
        tr = trades_for_day(day)
        if tr is None or not len(tr):
            continue
        tr = tr[np.isfinite(tr['iv']) & (tr['iv'] > 0)].assign(bin=lambda x: x['ts'].dt.floor('h'))
        tr = tr[tr['expiry'] >= tr['bin'] + H + pd.Timedelta(hours=implied_cfg['iv_min_ahead_h'])]
        tr = tr[np.abs(np.log(tr['strike'] / tr['index_price'])) <= implied_cfg['moneyness']]
        for b, g in tr.groupby('bin'):
            g = g[g['expiry'] == g['expiry'].min()]
            if len(g) >= min_trades:
                vals[b] = np.log(implied.wmedian(g['iv'], g['amount']) / 100.0)
    s = pd.Series(vals, dtype=float).sort_index()
    if not len(s):
        return s
    full = s.reindex(pd.date_range(s.index.min(), pd.Timestamp(days[-1]) + 23 * H, freq='h'))
    return full.ffill(limit=ffill_hours)


def market_hourly(bars, dvol, iv):
    f = dataset4.price_features(bars).join(px_features(bars))
    if dvol is not None:
        d = dvol.reindex(f.index)
        f['mk_dvol'] = np.log(d)
        f['mk_dvol_chg24'] = np.log(d) - np.log(d.shift(24))
    if iv is not None:
        f['mk_iv'] = iv.reindex(f.index)
    return f.replace([np.inf, -np.inf], np.nan)


def samples(track, feats, bars, cfg):
    tc = cfg['tracks'][track]
    market = dataset4.price_features(bars).join(px_features(bars))
    df = feats.join(market, how='inner').join(dataset4.hourly_targets(bars)[['V6', 'V24']], how='left')
    start, end = pd.Timestamp(tc['start']), pd.Timestamp(tc['end']) + pd.Timedelta(days=1)
    df = df[(df.index >= start) & (df.index < end)]
    need = [c for c in df.columns if c not in ('V6', 'V24')]
    df = df[np.isfinite(df[need].to_numpy(float)).all(axis=1)].copy()
    for name, h in cfg['targets'].items():
        df.loc[df.index + pd.Timedelta(hours=h) > end - H, name] = np.nan
    return df
