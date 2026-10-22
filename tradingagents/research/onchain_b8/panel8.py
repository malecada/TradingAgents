# tradingagents/research/onchain_b8/panel8.py
"""Panel rows (spec §4): per token, B7's engineering of the seven series plus price and
intraday features and the V6 / V24 targets; per hour, cross-sectional z-scores and the
relative target XV24. A token enters `entry_days` after its first bar."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b4 import dataset4
from ..onchain_b5.decisions import px_features
from ..onchain_b7.features7 import multiscale
from .hourly8 import SERIES


def token_series(day_frames, hours, token_index):
    parts = [f[f['token'] == token_index].set_index('hour')[SERIES] for f in day_frames]
    s = pd.concat(parts).sort_index() if parts else pd.DataFrame(columns=SERIES)
    return s.reindex(hours)


def token_frame(series, bars, c):
    f = multiscale(series, c['engineering'])
    m = dataset4.price_features(bars).join(px_features(bars))
    t = dataset4.hourly_targets(bars)[['V6', 'V24']]
    df = f.join(m, how='inner').join(t, how='left')
    start = bars.index.min() + pd.Timedelta(days=c['panel']['entry_days'])
    return df[df.index >= start]


def cross_section(panel, c):
    pc = c['panel']
    cols = [col for col in panel.columns if col.startswith('n_') and col.endswith(tuple(pc['xs_series']))] + list(pc['xs_price'])
    g = panel.groupby(level=0)
    mean, std, cnt = g[cols].transform('mean'), g[cols].transform('std'), g[cols].transform('count')
    z = (panel[cols] - mean) / std
    z = z.where((cnt >= pc['min_tokens_hour']) & (std > 0))
    vm, vc = g['V24'].transform('mean'), g['V24'].transform('count')
    out = panel.copy()
    for col in cols:                     # positional assignment: the hour index is not unique, so no join
        out[f'xs_{col}'] = z[col].to_numpy()
    out['XV24'] = (panel['V24'] - vm).where(vc >= pc['min_tokens_hour']).to_numpy()
    return out
