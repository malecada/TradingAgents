# tradingagents/research/onchain_b5/forecast.py
"""Walk-forward forecasts of log realised volatility to expiry and the pre-declared comparisons
(spec §5): M1 vs M0, M2 vs M1, M2 vs IV, per family and group."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b2.screen import fit_predict, folds
from ..onchain_b4.screen4 import interval


def columns(df, set_name, cfg):
    return sorted(c for c in df.columns if c.startswith(tuple(cfg['sets'][set_name])))


def run(df, cfg):
    df = df.sort_index()
    y = df['y'].to_numpy(float)
    fc, g = cfg['folds'], cfg['gate']
    fl = folds(df.index, fc['test_years'], float(df['tau_h'].iloc[0]) / 24)
    tested = np.zeros(len(df), bool)
    for _, _, te in fl:
        tested |= te
    preds = {}
    for fam in cfg['families']:
        for s in cfg['sets']:
            X = df[columns(df, s, cfg)].to_numpy(float)
            p = np.full(len(df), np.nan)
            for _, tr, te in fl:
                if te.any() and tr.sum() >= fc['min_train']:
                    p[te] = fit_predict(fam, 'regression', X[tr], y[tr], X[te], fc['inner_len'], cfg)
            preds[f'{fam}:{s}'] = p
    P = pd.DataFrame(preds, index=df.index)
    years = df.index.year.to_numpy()
    results = []
    for fam in cfg['families']:
        for a, b in cfg['comparisons']:
            la = (y - P[f'{fam}:{a}'].to_numpy()) ** 2
            lb = (y - P[f'{fam}:{b}'].to_numpy()) ** 2
            for name, yrs in cfg['groups'].items():
                m = tested & np.isin(years, yrs) & np.isfinite(la) & np.isfinite(lb)
                d = (la - lb)[m]
                lo, hi = interval(d, g['block'], g['draws'], g['seed'], g['chunk']) if len(d) >= g['block'] else (np.nan, np.nan)
                per_year = {int(yr): float(d[years[m] == yr].mean()) for yr in yrs if (years[m] == yr).any()}
                results.append({'family': fam, 'set': a, 'comparator': b, 'group': name, 'n': int(len(d)),
                                'mean_diff': float(d.mean()) if len(d) else np.nan, 'lo': lo, 'hi': hi,
                                'wins': int(sum(v < 0 for v in per_year.values())), 'years': per_year,
                                'loss_set': float(la[m].mean()) if len(d) else np.nan,
                                'loss_comparator': float(lb[m].mean()) if len(d) else np.nan})
    return P, results
