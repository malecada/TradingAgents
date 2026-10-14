"""B3 transforms and weekly samples (B2 rules plus F4/F5 value rules and T6/T7)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b2 import periods
from ..onchain_b2 import targets as T
from . import targets3 as T3

SIGNED = {'f3a_ex_net_value', 'f3a_whale_net_to_ex'}
F4_LOG = {'f4_components', 'f4_pair_components'}


def value3(name, x):
    if name in SIGNED:
        return np.sign(x) * np.log1p(np.abs(x))
    if name.startswith('f4_'):
        return np.log1p(x) if name in F4_LOG else x
    if name.startswith('f5_') or name.endswith('_share') or name == 'f1_mean_degree':
        return x
    return np.log1p(x)


def transform3(raw, z_window=8, z_min=6, z_clip=10.0):
    out = {}
    for name in raw.columns:
        x = value3(name, raw[name].astype(float))
        prev = x.shift(1)
        mean = prev.rolling(z_window, min_periods=z_min).mean()
        std = prev.rolling(z_window, min_periods=z_min).std(ddof=0)
        z = (x - mean) / std
        z[(std == 0) & x.notna()] = 0.0
        out[f'{name}__z8'] = z.clip(-z_clip, z_clip)
        out[f'{name}__d1'] = x - prev
    return pd.DataFrame(out, index=raw.index)


def columns3(df, set_name, cfg):
    return sorted(c for c in df.columns if c.startswith(tuple(cfg['sets'][set_name])))


def weekly_samples3(trans, prices, volumes, window):
    rows, excluded = {}, []
    available = set(trans.index[trans.notna().any(axis=1)])
    for w in trans.index:
        m = periods.week_end(w)
        if periods.weekly_window(m) != window:
            continue
        if w not in available:
            excluded.append((m.isoformat(), 'week_unavailable'))
            continue
        feats = trans.loc[w]
        if feats.isna().any():
            excluded.append((m.isoformat(), 'features_incomplete'))
            continue
        f0 = T.f0(prices, volumes, m)
        if f0 is None:
            excluded.append((m.isoformat(), 'f0_unavailable'))
            continue
        rows[pd.Timestamp(m)] = {**feats.to_dict(), **f0, 'week': w,
                                 'T2': T.t2(prices, m), 'T3': T.t3(prices, m), 'T4': T.t4(prices, m),
                                 'T5': T.t5(volumes, m), 'T6': T3.t6(prices, m), 'T7': T3.t7(prices, m)}
    df = pd.DataFrame.from_dict(rows, orient='index').sort_index()
    return df.astype({c: float for c in df.columns if c != 'week'}), excluded