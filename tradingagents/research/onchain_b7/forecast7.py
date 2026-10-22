# tradingagents/research/onchain_b7/forecast7.py
"""Samples per track, walk-forward predictions for every (family, set), the pre-declared
comparisons with block-bootstrap intervals and criteria (spec §7), and the tables."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b2.screen import folds, row_loss
from ..onchain_b4.screen4 import interval
from .models7 import fit_predict7

H = pd.Timedelta(hours=1)


def set_prefixes(name, track, cfg):
    out = list(cfg['blocks']['base']) + list(cfg['tracks'][track]['base_extra'])
    for b in cfg['sets'][name]:
        out += cfg['blocks'][b]
    return out


def columns(df, prefixes):
    return sorted(c for c in df.columns if c.startswith(tuple(prefixes)))


def fits(cfg):
    return [(f, s) for f in cfg['families'] for s in cfg['sets']] + [tuple(x) for x in cfg['extra_fits']]


def comparisons(cfg):
    out = [((f, a), (f, b)) for f in cfg['families'] for a, b in cfg['set_comparisons']]
    return out + [(tuple(a), tuple(b)) for a, b in cfg['cross_comparisons']]


def samples(track, table, targets, cfg):
    """Rows of the track window whose features (union of every set of the track) are finite;
    a target is NaN when its horizon runs past the window end."""
    tc = cfg['tracks'][track]
    start, end = pd.Timestamp(tc['start']), pd.Timestamp(tc['end']) + pd.Timedelta(days=1)
    pre = sorted({p for s in cfg['sets'] for p in set_prefixes(s, track, cfg)})
    df = table[columns(table, pre)].join(targets, how='left')
    df = df[(df.index >= start) & (df.index < end)]
    feat = [c for c in df.columns if c not in targets.columns]
    df = df[np.isfinite(df[feat].to_numpy(float)).all(axis=1)].copy()
    for name, t in cfg['targets'].items():
        if name in df.columns:
            df.loc[df.index + pd.Timedelta(hours=t['h']) > end - H, name] = np.nan
    return df


def predict_all(df, target, track, cfg, log=None):
    tc, fc = cfg['tracks'][track], cfg['folds']
    task, h = cfg['targets'][target]['task'], cfg['targets'][target]['h']
    d = df[df[target].notna()].sort_index()
    y = d[target].to_numpy(float)
    fl = [(yr, tr, te) for yr, tr, te in folds(d.index, tc['test_years'], h / 24) if te.any() and tr.sum() >= fc['min_train']]
    tested, const = np.zeros(len(d), bool), np.full(len(d), np.nan)
    for _, tr, te in fl:
        tested |= te
        const[te] = y[tr].mean()
    preds, meta = {}, {}
    for fam, s in fits(cfg):
        key = f'{fam}:{s}'
        X = d[columns(d, set_prefixes(s, track, cfg))].to_numpy(float)
        p, meta[key] = np.full(len(d), np.nan), {}
        for yr, tr, te in fl:
            info = {}
            p[te] = fit_predict7(fam, task, X[tr], y[tr], X[te], cfg, info)
            meta[key][int(yr)] = info
            if log is not None:
                log(event='fit', track=track, target=target, fit=key, year=int(yr), n_train=int(tr.sum()), **info)
        preds[key] = p
    P = pd.DataFrame(preds, index=d.index)
    P['y'], P['const'], P['tested'] = y, const, tested
    return P, meta


def _passed(r, tc, rows):
    if tc['criterion'] == 'years':
        return bool(r['hi'] < 0 and r['wins'] >= tc['min_year_wins']), 'interval+years'
    first, second = list(tc['groups'])
    if r['group'] == first:
        other = rows.get(second)
        return bool(r['hi'] < 0 and other is not None and other['mean_diff'] < 0), 'interval+sign'
    return bool(r['mean_diff'] < 0), 'sign'


def _gain(loss, const):
    return float(1 - loss / const) if np.isfinite(loss) and np.isfinite(const) and const > 0 else np.nan


def compare(P, target, track, cfg):
    tc, g = cfg['tracks'][track], cfg['gate']
    task = cfg['targets'][target]['task']
    y, const, tested = P['y'].to_numpy(float), P['const'].to_numpy(float), P['tested'].to_numpy(bool)
    years = P.index.year.to_numpy()
    results = []
    for (fa, sa), (fb, sb) in comparisons(cfg):
        la = row_loss(task, y, P[f'{fa}:{sa}'].to_numpy(float))
        lb = row_loss(task, y, P[f'{fb}:{sb}'].to_numpy(float))
        rows = {}
        for gname, yrs in tc['groups'].items():
            m = tested & np.isin(years, yrs) & np.isfinite(la) & np.isfinite(lb)
            d = (la - lb)[m]
            lo, hi = interval(d, g['block'], g['draws'], g['seed'], g['chunk']) if len(d) >= g['block'] else (np.nan, np.nan)
            per_year = {int(yr): float(d[years[m] == yr].mean()) for yr in yrs if (years[m] == yr).any()}
            lc = float(row_loss(task, y[m], const[m]).mean()) if m.any() else np.nan
            ls, lcomp = (float(la[m].mean()), float(lb[m].mean())) if m.any() else (np.nan, np.nan)
            rows[gname] = {'track': track, 'target': target, 'family': fa if fa == fb else f'{fa}|{fb}', 'set': sa,
                           'comparator': sb, 'group': gname, 'n': int(m.sum()), 'mean_diff': float(d.mean()) if len(d) else np.nan,
                           'lo': lo, 'hi': hi, 'wins': int(sum(v < 0 for v in per_year.values())), 'years': per_year,
                           'loss_set': ls, 'loss_comparator': lcomp, 'loss_constant': lc,
                           'gain_set': _gain(ls, lc), 'gain_comparator': _gain(lcomp, lc)}
        for r in rows.values():
            r['passed'], r['criterion'] = _passed(r, tc, rows)
            results.append(r)
    return results


def report(results):
    lines = ['| track | target | family | comparison | group | n | mean diff | 95 % CI | years better | criterion | pass | gain vs constant (set / comparator) |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in results:
        lines.append(f"| {r['track']} | {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['group']} | {r['n']} | "
                     f"{r['mean_diff']:+.5f} | [{r['lo']:+.5f}, {r['hi']:+.5f}] | {r['wins']}/{len(r['years'])} | {r['criterion']} | "
                     f"{'PASS' if r['passed'] else '—'} | {r['gain_set']:+.4f} / {r['gain_comparator']:+.4f} |")
    return '\n'.join(lines)


def detail_report(meta_by_unit):
    lines = ['| unit | fit | per-year alpha or iterations |', '|---|---|---|']
    for unit, meta in sorted(meta_by_unit.items()):
        for key, years in meta.items():
            vals = []
            for yr, info in sorted(years.items(), key=lambda kv: int(kv[0])):
                v = info.get('n_iter') if info.get('n_iter') is not None else info.get('alpha')
                sup = f" (tail +{info['tail_pos']}/{info['tail_n']})" if 'tail_pos' in info else ''
                vals.append(f'{yr} {v if v is not None else "—"}{sup}')
            lines.append(f"| {unit} | {key} | {', '.join(vals)} |")
    return '\n'.join(lines)
