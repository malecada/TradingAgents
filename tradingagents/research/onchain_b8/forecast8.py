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


def needed_columns(cfg, panel=None):
    """`token`, every feature column of every set and every target; with `panel`, the names
    present in it, otherwise the prefix list is resolved by the caller."""
    pre = sorted({p for s in cfg['sets'] for p in set_prefixes(s, cfg)})
    if panel is None:
        return pre
    return sorted(set(['token'] + columns(panel, pre) + list(cfg['targets'])))


def samples(panel, cfg, target=None):
    """Rows with every feature finite; targets are NaN where the horizon runs past the window
    end. With `target`, only rows holding that target are kept and the other targets are
    dropped, in one copy of the rows (the panel is never copied whole)."""
    end = pd.Timestamp(cfg['window']['last_day']) + pd.Timedelta(days=1)
    pre = needed_columns(cfg)
    tcols = list(cfg['targets']) if target is None else [target]
    feat = columns(panel, pre)
    keep = np.ones(len(panel), bool)
    for col in feat:                                           # column by column: no 2-D float copy of the panel
        keep &= np.isfinite(panel[col].to_numpy(np.float32))
    late = {name: (panel.index + pd.Timedelta(hours=t['h']) > end - H) for name, t in cfg['targets'].items() if name in tcols}
    if target is not None:
        keep &= panel[target].notna().to_numpy() & ~late[target]
    df = panel.loc[keep, ['token'] + feat + tcols].copy()
    for name, lt in late.items():
        df.loc[lt[keep], name] = np.nan
    return df


def bundle(d, target, cfg):
    """Arrays for one target from a filtered, hour-sorted frame: one float32 matrix of every
    feature column (sets are column subsets of it), the target, the token and the index."""
    cols = columns(d, needed_columns(cfg))
    return {'X': d[cols].to_numpy(np.float32), 'cols': cols, 'y': d[target].to_numpy(float),
            'token': d['token'].to_numpy(), 'index': pd.DatetimeIndex(d.index)}


def fold_slices(index, test_years, purge_days, min_train):
    """B2's walk-forward folds as slices: on an hour-sorted index the training rows are a
    prefix and the test rows one block, so no fold copies the matrix."""
    out = []
    for yr, tr, te in folds(index, test_years, purge_days):
        n_tr = int(tr.sum())
        if not te.any() or n_tr < min_train:
            continue
        te_pos = np.flatnonzero(te)
        if not tr[:n_tr].all() or te_pos[-1] - te_pos[0] + 1 != len(te_pos):
            raise ValueError('folds are not contiguous: the rows must be sorted by hour')
        out.append((yr, slice(0, n_tr), slice(int(te_pos[0]), int(te_pos[-1]) + 1)))
    return out


def predict_bundle(b, target, cfg, log=None):
    fc = cfg['folds']
    h = cfg['targets'][target]['h']
    X_all, cols, y = b['X'], b['cols'], b['y']
    fl = fold_slices(b['index'], fc['test_years'], h / 24, fc['min_train'])
    tested, const = np.zeros(len(y), bool), np.full(len(y), np.nan)
    for _, tr, te in fl:
        tested[te] = True
        const[te] = y[tr].mean()
    preds, meta = {}, {}
    for fam in cfg['families']:
        for s in cfg['sets']:
            key = f'{fam}:{s}'
            want = [c for c in cols if c.startswith(tuple(set_prefixes(s, cfg)))]
            X = X_all if want == cols else np.ascontiguousarray(X_all[:, [cols.index(c) for c in want]])
            p, meta[key] = np.full(len(y), np.nan), {}
            for yr, tr, te in fl:
                info = {}
                p[te] = fit_predict7(fam, 'regression', X[tr], y[tr], X[te], cfg, info)
                meta[key][int(yr)] = info
                if log is not None:
                    log(event='fit', target=target, fit=key, year=int(yr), n_train=int(tr.stop), **info)
            preds[key] = p
            if X is not X_all:
                del X
    P = pd.DataFrame(preds, index=b['index'])
    P['token'] = b['token']
    P['y'], P['const'], P['tested'] = y, const, tested
    return P, meta


def predict_all(df, target, cfg, log=None):
    ok = df[target].notna()
    d = df if bool(ok.all()) else df[ok]                       # no copy when the caller already filtered
    if not d.index.is_monotonic_increasing:
        d = d.sort_index(kind='stable')
    return predict_bundle(bundle(d, target, cfg), target, cfg, log)


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
