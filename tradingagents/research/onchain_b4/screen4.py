# tradingagents/research/onchain_b4/screen4.py
"""B4 screen and holdout evaluation (spec §6): B2 model primitives, targets of two kinds from
config, a constant-forecast reference for every row, and a chunked circular block bootstrap that
draws exactly the resamples of the B branch reference."""
from __future__ import annotations

import numpy as np

from ..onchain_b2.holdout import holm
from ..onchain_b2.screen import fit_predict, folds, row_loss

_CONST = ('r2c_', 'llgain_')


def bootstrap_means(values, block, draws, seed, chunk=100):
    x = np.asarray(values, float)
    n = len(x)
    if n < block:
        raise ValueError(f'series of {n} rows is shorter than the {block}-row block')
    rng = np.random.Generator(np.random.PCG64(seed))
    k = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=(draws, k))
    out = np.empty(draws)
    for i in range(0, draws, chunk):
        s = starts[i:i + chunk]
        idx = ((s[:, :, None] + np.arange(block)[None, None, :]) % n).reshape(len(s), -1)[:, :n]
        out[i:i + chunk] = x[idx].mean(1)
    return out


def interval(values, block, draws, seed, chunk=100):
    m = bootstrap_means(values, block, draws, seed, chunk)
    return float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def columns4(df, set_name, cfg):
    return sorted(c for c in df.columns if c.startswith(tuple(cfg['sets'][set_name])))


def folds_for(index, target, cfg):
    return folds(index, cfg['folds']['test_years'], cfg['targets'][target]['horizon_hours'] / 24)


def run_screen4(samples, cfg):
    g, fc = cfg['gate'], cfg['folds']
    results = []
    for target, tc in cfg['targets'].items():
        kind, task = tc['kind'], tc['task']
        comps = cfg['comparisons'][kind]
        sets = sorted({s for pair in comps for s in pair})
        df = samples[kind]
        n_missing = int(df[target].isna().sum())
        df = df[df[target].notna()].sort_index()
        y = df[target].to_numpy(float)
        fl = folds_for(df.index, target, cfg)
        tested, const = np.zeros(len(df), bool), np.full(len(df), np.nan)
        for _, tr, te in fl:
            tested |= te
            const[te] = y[tr].mean()
        yt = df.index.year.to_numpy()[tested]
        closs = float(row_loss(task, y[tested], const[tested]).mean())
        for family in cfg['families']:
            preds, alphas = {}, {}
            for s in sets:
                X = df[columns4(df, s, cfg)].to_numpy(float)
                p = np.full(len(df), np.nan)
                alphas[s] = {}
                for yr, tr, te in fl:
                    info = {}
                    p[te] = fit_predict(family, task, X[tr], y[tr], X[te], fc['inner_len'][kind], cfg, info)
                    alphas[s][int(yr)] = info['alpha']
                preds[s] = p
            loss = {s: row_loss(task, y[tested], preds[s][tested]) for s in sets}
            for a, b in comps:
                diff = loss[a] - loss[b]
                lo, hi = interval(diff, tc['block'], g['draws'], g['seed'], g['chunk'])
                per_year = {int(yr): float(diff[yt == yr].mean()) for yr in fc['test_years']}
                wins = sum(v < 0 for v in per_year.values())
                if task == 'classification':
                    extra = {f'llgain_{s}': closs - float(loss[s].mean()) for s in (a, b)}
                    extra.update({f'accuracy_{s}': float(((preds[s][tested] > 0.5) == (y[tested] > 0.5)).mean())
                                  for s in (a, b)})
                else:
                    extra = {f'r2c_{s}': 1 - float(loss[s].mean()) / closs for s in (a, b)}
                results.append({'target': target, 'kind': kind, 'task': task, 'family': family, 'set': a,
                                'comparator': b, 'n': int(len(diff)), 'mean_diff': float(diff.mean()), 'lo': lo,
                                'hi': hi, 'wins': int(wins), 'years': per_year,
                                'alphas': {a: alphas[a], b: alphas[b]}, 'n_missing_target': n_missing,
                                'passed': bool(hi < 0 and wins >= g['min_year_wins']),
                                'loss_set': float(loss[a].mean()), 'loss_comparator': float(loss[b].mean()),
                                'loss_constant': closs, 'extra': extra})
    return results


def select4(results, cfg):
    passing = [r for r in results if r['passed']]
    passing.sort(key=lambda r: (r['hi'] / r['loss_comparator'], cfg['onchain_rank'][r['set']]))
    return [{'target': r['target'], 'family': r['family'], 'set': r['set'], 'comparator': r['comparator'],
             'dev_mean_diff': r['mean_diff'], 'dev_hi': r['hi']} for r in passing[:cfg['gate']['max_selected']]]


def evaluate4(dev, hold, selection, cfg):
    g, fc = cfg['gate'], cfg['folds']
    out = []
    for s in selection['selected']:
        tc = cfg['targets'][s['target']]
        kind, task = tc['kind'], tc['task']
        d = dev[kind][dev[kind][s['target']].notna()].sort_index()
        h = hold[kind][hold[kind][s['target']].notna()].sort_index()
        yd, yh = d[s['target']].to_numpy(float), h[s['target']].to_numpy(float)
        loss = {}
        for name in (s['set'], s['comparator']):
            cols = columns4(d, name, cfg)
            pred = fit_predict(s['family'], task, d[cols].to_numpy(float), yd, h[cols].to_numpy(float),
                               fc['inner_len'][kind], cfg)
            loss[name] = row_loss(task, yh, pred)
        diff = loss[s['set']] - loss[s['comparator']]
        means = bootstrap_means(diff, tc['block'], g['draws'], g['seed'], g['chunk'])
        out.append({**{k: s[k] for k in ('target', 'family', 'set', 'comparator')}, 'n': int(len(diff)),
                    'mean_diff': float(diff.mean()), 'p': float((means >= 0).mean())})
    for r, adj in zip(out, holm([r['p'] for r in out]) if out else []):
        r['p_holm'] = adj
        r['passed'] = bool(adj < g['alpha'] and r['mean_diff'] < 0)
    return out


def report4(results, selection):
    lines = [f'{len(results)} comparisons are screened, each against a 95 % interval; about '
             f'{0.05 * len(results):.0f} false passes are expected by chance, which is why the sealed holdout exists.', '',
             '| target | family | comparison | n | mean loss diff | 95 % CI | years better | pass | vs constant | detail |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for r in results:
        const = ', '.join(f'{k} {v:+.4f}' for k, v in r['extra'].items() if k.startswith(_CONST))
        detail = ', '.join(f'{k} {v:.4f}' for k, v in r['extra'].items() if not k.startswith(_CONST))
        lines.append(f"| {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['n']} | "
                     f"{r['mean_diff']:+.6f} | [{r['lo']:+.6f}, {r['hi']:+.6f}] | {r['wins']}/6 | "
                     f"{'PASS' if r['passed'] else '—'} | {const} | {detail} |")
    lines += ['', '## Selected for the holdout', '']
    lines += [f"- {s['target']} · {s['family']} · {s['set']} vs {s['comparator']} (dev upper bound {s['dev_hi']:+.6f})"
              for s in selection] or ['- none: screen negative, holdout stays unused']
    return '\n'.join(lines)
