"""B3 screen and holdout evaluation: B2 primitives with targets, purges, blocks, sets and
comparisons read from config/b3.json."""
from __future__ import annotations

import numpy as np

from ..onchain_b.evaluate import _bootstrap_means, block_bootstrap
from ..onchain_b2.holdout import holm
from ..onchain_b2.screen import folds, fit_predict, row_loss
from .dataset3 import columns3


def folds_for(dates, target, cfg):
    return folds(dates, cfg['folds']['test_years'], cfg['targets'][target]['horizon'])


def run_screen3(samples, cfg):
    g, fcfg = cfg['gate'], cfg['folds']
    sets = sorted({s for pair in cfg['comparisons'] for s in pair})
    results = []
    for target, tc in cfg['targets'].items():
        kind, task = tc['kind'], tc['task']
        df = samples[kind]
        n_missing = int(df[target].isna().sum())
        df = df[df[target].notna()].sort_index()
        y = df[target].to_numpy(float)
        fl = folds_for(df.index, target, cfg)
        tested = np.zeros(len(df), bool)
        for _, _, te in fl:
            tested |= te
        yt = df.index.year.to_numpy()[tested]
        for family in cfg['families']:
            preds, alphas = {}, {}
            for s in sets:
                X = df[columns3(df, s, cfg)].to_numpy(float)
                p = np.full(len(df), np.nan)
                alphas[s] = {}
                for yr, tr, te in fl:
                    info = {}
                    p[te] = fit_predict(family, task, X[tr], y[tr], X[te], fcfg['inner_len'][kind], cfg, info)
                    alphas[s][int(yr)] = info['alpha']
                preds[s] = p
            loss = {s: row_loss(task, y[tested], preds[s][tested]) for s in sets}
            for a, b in cfg['comparisons']:
                diff = loss[a] - loss[b]
                lo, hi = block_bootstrap(diff, block=tc['block'], draws=g['draws'], seed=g['seed'])
                per_year = {int(yr): float(diff[yt == yr].mean()) for yr in fcfg['test_years']}
                years_loss = {int(yr): [float(loss[a][yt == yr].mean()), float(loss[b][yt == yr].mean())]
                              for yr in fcfg['test_years']}
                wins = sum(v < 0 for v in per_year.values())
                if task == 'classification':
                    extra = {f'accuracy_{s}': float(((preds[s][tested] > 0.5) == (y[tested] > 0.5)).mean()) for s in (a, b)}
                    extra.update({f'brier_{s}': float(((preds[s][tested] - y[tested]) ** 2).mean()) for s in (a, b)})
                else:
                    extra = {f'r2_vs_S0_{s}': float(1 - loss[s].mean() / loss['S0'].mean()) if 'S0' in loss else float('nan')
                             for s in (a, b)}
                results.append({'target': target, 'kind': kind, 'task': task, 'family': family, 'set': a, 'comparator': b,
                                'n': int(len(diff)), 'mean_diff': float(diff.mean()), 'lo': lo, 'hi': hi, 'wins': int(wins),
                                'years': per_year, 'years_loss': years_loss, 'alphas': {a: alphas[a], b: alphas[b]},
                                'n_missing_target': n_missing,
                                'passed': bool(hi < 0 and wins >= g['min_year_wins']),
                                'loss_set': float(loss[a].mean()), 'loss_comparator': float(loss[b].mean()), 'extra': extra})
    return results


def select3(results, cfg):
    passing = [r for r in results if r['passed']]
    passing.sort(key=lambda r: (r['hi'] / r['loss_comparator'], 0 if r['set'] in cfg['graph_sets'] else 1))
    return [{'target': r['target'], 'family': r['family'], 'set': r['set'], 'comparator': r['comparator'],
             'dev_mean_diff': r['mean_diff'], 'dev_hi': r['hi']} for r in passing[:cfg['gate']['max_selected']]]


def evaluate3(dev, hold, selection, cfg):
    g, fcfg = cfg['gate'], cfg['folds']
    out = []
    for s in selection['selected']:
        tc = cfg['targets'][s['target']]
        kind, task = tc['kind'], tc['task']
        d = dev[kind][dev[kind][s['target']].notna()].sort_index()
        h = hold[kind][hold[kind][s['target']].notna()].sort_index()
        yd, yh = d[s['target']].to_numpy(float), h[s['target']].to_numpy(float)
        loss = {}
        for name in (s['set'], s['comparator']):
            cols = columns3(d, name, cfg)
            pred = fit_predict(s['family'], task, d[cols].to_numpy(float), yd, h[cols].to_numpy(float),
                               fcfg['inner_len'][kind], cfg)
            loss[name] = row_loss(task, yh, pred)
        diff = loss[s['set']] - loss[s['comparator']]
        means = _bootstrap_means(diff, block=tc['block'], draws=g['draws'], seed=g['seed'])
        out.append({**{k: s[k] for k in ('target', 'family', 'set', 'comparator')}, 'n': int(len(diff)),
                    'mean_diff': float(diff.mean()), 'p': float((means >= 0).mean())})
    for r, adj in zip(out, holm([r['p'] for r in out]) if out else []):
        r['p_holm'] = adj
        r['passed'] = bool(adj < g['alpha'] and r['mean_diff'] < 0)
    return out