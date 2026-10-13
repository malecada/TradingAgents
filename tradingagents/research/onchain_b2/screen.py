"""Development-window screen (spec §8): expanding walk-forward 2019–2024, fixed linear and
tree models, nested feature-set comparisons, pre-registered gate and holdout selection."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ..onchain_b.evaluate import block_bootstrap
from .dataset import columns

TARGETS = {'T1': ('daily', 'classification'), 'T2': ('weekly', 'classification'),
           'T3': ('weekly', 'regression'), 'T4': ('weekly', 'regression'), 'T5': ('weekly', 'regression')}
COMPARISONS = [('S1', 'S0'), ('S2', 'S1'), ('S3', 'S1'), ('S4', 'S2')]
FAMILIES = ('linear', 'trees')


def folds(dates, test_years, purge_days):
    d = pd.DatetimeIndex(dates)
    out = []
    for y in test_years:
        start, end = pd.Timestamp(f'{y}-01-01'), pd.Timestamp(f'{y + 1}-01-01')
        train = np.asarray(d + pd.Timedelta(days=purge_days) <= start)
        test = np.asarray((d >= start) & (d < end))
        out.append((y, train, test))
    return out


def row_loss(task, y, pred):
    if task == 'classification':
        p = np.clip(pred, 1e-6, 1 - 1e-6)
        return -(y * np.log(p) + (1 - y) * np.log(1 - p))
    return (y - pred) ** 2


def _model(family, task, alpha, cfg):
    if family == 'trees':
        params = cfg['models']['trees']
        return (HistGradientBoostingClassifier if task == 'classification' else HistGradientBoostingRegressor)(**params)
    if task == 'classification':
        return make_pipeline(StandardScaler(), LogisticRegression(C=1.0 / alpha, max_iter=5000))
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def _fit(family, task, alpha, X, y, cfg):
    if task == 'classification' and len(np.unique(y)) < 2:
        return None
    return _model(family, task, alpha, cfg).fit(X, y)


def _predict(model, task, X, fallback):
    if model is None:
        return np.full(len(X), fallback)
    return model.predict_proba(X)[:, 1] if task == 'classification' else model.predict(X)


def fit_predict(family, task, Xtr, ytr, Xte, inner_len, cfg, info=None):
    """Linear models search the registered alpha grid on the last `inner_len` training rows when the
    window holds at least twice that many rows; otherwise the registered fallback alpha is used."""
    alpha = float(cfg['models']['fallback_alpha'])
    if family == 'linear' and len(Xtr) >= 2 * inner_len:
        best = None
        for a in cfg['models']['alphas']:
            m = _fit(family, task, a, Xtr[:-inner_len], ytr[:-inner_len], cfg)
            loss = row_loss(task, ytr[-inner_len:], _predict(m, task, Xtr[-inner_len:], ytr[:-inner_len].mean())).mean()
            if best is None or loss < best[0]:
                best = (loss, a)
        alpha = best[1]
    if info is not None:
        info['alpha'] = alpha if family == 'linear' else None
    model = _fit(family, task, alpha, Xtr, ytr, cfg)
    return _predict(model, task, Xte, ytr.mean())


def run_screen(samples, cfg):
    g, f = cfg['gate'], cfg['folds']
    results = []
    for target, (kind, task) in TARGETS.items():
        df = samples[kind]
        n_missing = int(df[target].isna().sum())
        df = df[df[target].notna()].sort_index()
        y = df[target].to_numpy(float)
        fl = folds(df.index, f['test_years'], f['purge_days'][kind])
        tested = np.zeros(len(df), bool)
        for _, _, te in fl:
            tested |= te
        years = df.index.year.to_numpy()
        for family in FAMILIES:
            preds, alphas = {}, {}
            for s in ('S0', 'S1', 'S2', 'S3', 'S4'):
                X = df[columns(df, s)].to_numpy(float)
                p = np.full(len(df), np.nan)
                alphas[s] = {}
                for yr, tr, te in fl:
                    info = {}
                    p[te] = fit_predict(family, task, X[tr], y[tr], X[te], f['inner_len'][kind], cfg, info)
                    alphas[s][int(yr)] = info['alpha']
                preds[s] = p
            loss = {s: row_loss(task, y[tested], preds[s][tested]) for s in preds}
            for a, b in COMPARISONS:
                diff = loss[a] - loss[b]
                lo, hi = block_bootstrap(diff, block=g['block'][kind], draws=g['draws'], seed=g['seed'])
                yt = years[tested]
                per_year = {int(yr): float(diff[yt == yr].mean()) for yr in f['test_years']}
                years_loss = {int(yr): [float(loss[a][yt == yr].mean()), float(loss[b][yt == yr].mean())]
                              for yr in f['test_years']}
                wins = sum(v < 0 for v in per_year.values())
                extra = {}
                if task == 'classification':
                    extra = {f'accuracy_{s}': float(((preds[s][tested] > 0.5) == (y[tested] > 0.5)).mean()) for s in (a, b)}
                    extra.update({f'brier_{s}': float(((preds[s][tested] - y[tested]) ** 2).mean()) for s in (a, b)})
                else:
                    extra = {f'r2_vs_S0_{s}': float(1 - loss[s].mean() / loss['S0'].mean()) for s in (a, b)}
                results.append({'target': target, 'kind': kind, 'task': task, 'family': family, 'set': a, 'comparator': b,
                                'n': int(len(diff)), 'mean_diff': float(diff.mean()), 'lo': lo, 'hi': hi,
                                'wins': int(wins), 'years': per_year, 'years_loss': years_loss,
                                'alphas': {a: alphas[a], b: alphas[b]}, 'n_missing_target': n_missing,
                                'passed': bool(hi < 0 and wins >= g['min_year_wins']),
                                'loss_set': float(loss[a].mean()), 'loss_comparator': float(loss[b].mean()), 'extra': extra})
    return results


def select(results, cfg):
    passing = [r for r in results if r['passed']]
    # amendment 2026-10-13 (pre-outcome): rank by the upper bound relative to the comparator's loss,
    # so targets with different loss scales are comparable
    passing.sort(key=lambda r: (r['hi'] / r['loss_comparator'], 0 if r['set'] in ('S3', 'S4') else 1))
    return [{'target': r['target'], 'family': r['family'], 'set': r['set'], 'comparator': r['comparator'],
             'dev_mean_diff': r['mean_diff'], 'dev_hi': r['hi']} for r in passing[:cfg['gate']['max_selected']]]


def report(results, selection):
    lines = [f'{len(results)} comparisons are screened, each against a 95 % interval; about '
             f'{0.05 * len(results):.0f} false passes are expected by chance, which is why the sealed holdout exists.', '',
             '| target | family | comparison | n | mean loss diff | 95 % CI | years better | pass | detail |',
             '|---|---|---|---|---|---|---|---|---|']
    for r in results:
        detail = ', '.join(f'{k} {v:.4f}' for k, v in r['extra'].items())
        lines.append(f"| {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['n']} | "
                     f"{r['mean_diff']:+.5f} | [{r['lo']:+.5f}, {r['hi']:+.5f}] | {r['wins']}/6 | "
                     f"{'PASS' if r['passed'] else '—'} | {detail} |")
    lines += ['', '## Selected for the holdout', '']
    lines += [f"- {s['target']} · {s['family']} · {s['set']} vs {s['comparator']} (dev upper bound {s['dev_hi']:+.5f})"
              for s in selection] or ['- none: screen negative, holdout stays unused']
    return '\n'.join(lines)