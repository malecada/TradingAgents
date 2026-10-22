# tradingagents/research/onchain_b8/forecast8.py
"""Pooled walk-forward comparisons on the token panel (spec §5): one model across tokens per
fold, per-row losses averaged per hour, a block bootstrap over hours, a per-year criterion."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b2.screen import folds, row_loss
from ..onchain_b4.screen4 import interval
from ..onchain_b7.forecast7 import columns
from ..onchain_b7.models7 import fit_predict7

H = pd.Timedelta(hours=1)


def set_prefixes(name, cfg):
    out = list(cfg['blocks']['base'])
    for b in cfg['sets'][name]:
        out += cfg['blocks'][b]
    return out


def samples(panel, cfg):
    end = pd.Timestamp(cfg['window']['last_day']) + pd.Timedelta(days=1)
    pre = sorted({p for s in cfg['sets'] for p in set_prefixes(s, cfg)})
    tcols = list(cfg['targets'])
    feat = columns(panel, pre)
    df = panel[['token'] + feat + tcols]
    df = df[np.isfinite(df[feat].to_numpy(np.float32)).all(axis=1)].copy()
    for name, t in cfg['targets'].items():
        df.loc[df.index + pd.Timedelta(hours=t['h']) > end - H, name] = np.nan
    return df


def predict_all(df, target, cfg, log=None):
    fc = cfg['folds']
    h = cfg['targets'][target]['h']
    d = df[df[target].notna()].sort_index(kind='stable')
    y = d[target].to_numpy(float)
    fl = [(yr, tr, te) for yr, tr, te in folds(d.index, fc['test_years'], h / 24) if te.any() and tr.sum() >= fc['min_train']]
    tested, const = np.zeros(len(d), bool), np.full(len(d), np.nan)
    for _, tr, te in fl:
        tested |= te
        const[te] = y[tr].mean()
    preds, meta = {}, {}
    for fam in cfg['families']:
        for s in cfg['sets']:
            key = f'{fam}:{s}'
            X = d[columns(d, set_prefixes(s, cfg))].to_numpy(np.float32)
            p, meta[key] = np.full(len(d), np.nan), {}
            for yr, tr, te in fl:
                info = {}
                p[te] = fit_predict7(fam, 'regression', X[tr], y[tr], X[te], cfg, info)
                meta[key][int(yr)] = info
                if log is not None:
                    log(event='fit', target=target, fit=key, year=int(yr), n_train=int(tr.sum()), **info)
            preds[key] = p
    P = pd.DataFrame(preds, index=d.index)
    P['token'] = d['token'].to_numpy()
    P['y'], P['const'], P['tested'] = y, const, tested
    return P, meta


def _gain(loss, const):
    return float(1 - loss / const) if np.isfinite(loss) and np.isfinite(const) and const > 0 else np.nan


def compare(P, target, cfg):
    g, fc = cfg['gate'], cfg['folds']
    y, const, tested = P['y'].to_numpy(float), P['const'].to_numpy(float), P['tested'].to_numpy(bool)
    results = []
    for a, b in cfg['comparisons']:
        for fam in cfg['families']:
            la = row_loss('regression', y, P[f'{fam}:{a}'].to_numpy(float))
            lb = row_loss('regression', y, P[f'{fam}:{b}'].to_numpy(float))
            m = tested & np.isfinite(la) & np.isfinite(lb)
            per_hour = pd.Series((la - lb)[m], index=P.index[m]).groupby(level=0).mean()
            yrs = per_hour.index.year.to_numpy()
            v = per_hour.to_numpy()
            lo, hi = interval(v, g['block'], g['draws'], g['seed'], g['chunk']) if len(v) >= g['block'] else (np.nan, np.nan)
            per_year = {int(yr): float(v[yrs == yr].mean()) for yr in fc['test_years'] if (yrs == yr).any()}
            wins = int(sum(x < 0 for x in per_year.values()))
            lc = float(row_loss('regression', y[m], const[m]).mean()) if m.any() else np.nan
            ls, lcomp = (float(la[m].mean()), float(lb[m].mean())) if m.any() else (np.nan, np.nan)
            results.append({'target': target, 'family': fam, 'set': a, 'comparator': b, 'n_rows': int(m.sum()), 'n_hours': int(len(v)),
                            'mean_diff': float(v.mean()) if len(v) else np.nan, 'lo': lo, 'hi': hi, 'wins': wins, 'years': per_year,
                            'loss_set': ls, 'loss_comparator': lcomp, 'loss_constant': lc,
                            'gain_set': _gain(ls, lc), 'gain_comparator': _gain(lcomp, lc),
                            'passed': bool(hi < 0 and wins >= fc['min_year_wins']), 'criterion': 'interval+years'})
    return results


def per_token(P, target, cfg):
    y, tested = P['y'].to_numpy(float), P['tested'].to_numpy(bool)
    rows = []
    for a, b in cfg['comparisons']:
        for fam in cfg['families']:
            la = row_loss('regression', y, P[f'{fam}:{a}'].to_numpy(float))
            lb = row_loss('regression', y, P[f'{fam}:{b}'].to_numpy(float))
            m = tested & np.isfinite(la) & np.isfinite(lb)
            d = pd.DataFrame({'token': P['token'].to_numpy()[m], 'diff': (la - lb)[m]}).groupby('token')['diff'].agg(['count', 'mean'])
            for tok, r in d.iterrows():
                rows.append({'target': target, 'family': fam, 'set': a, 'comparator': b, 'token': int(tok), 'n': int(r['count']), 'mean_diff': float(r['mean'])})
    return pd.DataFrame(rows, columns=['target', 'family', 'set', 'comparator', 'token', 'n', 'mean_diff'])


def report(results):
    lines = ['| target | family | comparison | rows | hours | mean diff | 95 % CI | years better | pass | gain vs constant (set / comparator) |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for r in results:
        lines.append(f"| {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['n_rows']} | {r['n_hours']} | "
                     f"{r['mean_diff']:+.5f} | [{r['lo']:+.5f}, {r['hi']:+.5f}] | {r['wins']}/{len(r['years'])} | "
                     f"{'PASS' if r['passed'] else '—'} | {r['gain_set']:+.4f} / {r['gain_comparator']:+.4f} |")
    return '\n'.join(lines)
