"""Weekly raw features → causal transforms → weekly and daily samples (spec §5.4, §6, §7)."""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import periods
from . import targets as T

SIGNED = {'f3a_ex_net_value', 'f3a_whale_net_to_ex'}
FEATURE_SETS = {'S0': ('f0_',), 'S1': ('f0_', 'f1_'), 'S2': ('f0_', 'f1_', 'f3a_'),
                'S3': ('f0_', 'f1_', 'f2_'), 'S4': ('f0_', 'f1_', 'f3a_', 'f2_', 'f3b_')}


def _value(name, x):
    if name in SIGNED:
        return np.sign(x) * np.log1p(np.abs(x))
    unchanged = (name.endswith('_share') or name == 'f1_mean_degree' or name.startswith('f2_')
                 or (name.startswith('f3b_') and not name.endswith('_n')))
    return x if unchanged else np.log1p(x)


def raw_table(rows):
    weeks = periods.all_weeks() if not rows or set(rows) <= set(periods.all_weeks()) else sorted(rows)
    data = {w: (rows.get(w) or {}) for w in weeks}
    return pd.DataFrame.from_dict(data, orient='index').reindex(weeks)


def transform(raw, z_window=8, z_min=6):
    out = {}
    for name in raw.columns:
        x = _value(name, raw[name].astype(float))
        prev = x.shift(1)
        mean = prev.rolling(z_window, min_periods=z_min).mean()
        std = prev.rolling(z_window, min_periods=z_min).std(ddof=0)
        z = (x - mean) / std
        z[(std == 0) & x.notna()] = 0.0
        out[f'{name}__z8'] = z
        out[f'{name}__d1'] = x - prev
    return pd.DataFrame(out, index=raw.index)


def columns(df, set_name):
    return sorted(c for c in df.columns if c.startswith(FEATURE_SETS[set_name]))


def _row(trans, week, f0, extra):
    feats = trans.loc[week]
    if feats.isna().any():
        return None, 'features_incomplete'
    if f0 is None:
        return None, 'f0_unavailable'
    return {**feats.to_dict(), **f0, **extra}, None


def weekly_samples(trans, prices, volumes, window):
    rows, excluded = {}, []
    available = set(trans.index[trans.notna().any(axis=1)])
    for w in trans.index:
        m = periods.week_end(w)
        if periods.weekly_window(m) != window:
            continue
        if w not in available:
            excluded.append((m.isoformat(), 'week_unavailable'))
            continue
        row, why = _row(trans, w, T.f0(prices, volumes, m),
                        {'week': w, 'T2': T.t2(prices, m), 'T3': T.t3(prices, m), 'T4': T.t4(prices, m),
                         'T5': T.t5(volumes, m)})
        if why:
            excluded.append((m.isoformat(), why))
        else:
            rows[pd.Timestamp(m)] = row
    df = pd.DataFrame.from_dict(rows, orient='index').sort_index()
    return df.astype({c: float for c in df.columns if c != 'week'}), excluded


def daily_samples(trans, prices, volumes, window):
    weeks = list(trans.index)
    available = set(trans.index[trans.notna().any(axis=1)])
    rows, excluded = {}, []
    start = periods.DEV_START if window == 'dev' else periods.HOLD_START
    end = periods.DEV_END if window == 'dev' else periods.HOLD_END
    d = start
    while d <= end:
        if periods.daily_window(d) == window:
            w = periods.latest_week_for(d, weeks)
            if w is None or w not in available:
                excluded.append((d.isoformat(), 'week_unavailable'))
            else:
                row, why = _row(trans, w, T.f0(prices, volumes, d), {'week': w, 'T1': T.t1(prices, d)})
                if why:
                    excluded.append((d.isoformat(), why))
                else:
                    rows[pd.Timestamp(d)] = row
        d += timedelta(days=1)
    df = pd.DataFrame.from_dict(rows, orient='index').sort_index()
    return df.astype({c: float for c in df.columns if c != 'week'}), excluded