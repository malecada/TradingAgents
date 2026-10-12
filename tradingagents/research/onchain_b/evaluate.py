"""Metrics (paper Eqs. 12–19, binary-up convention), moving-block bootstrap, result table."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def direction_metrics(pred, target):
    p, t = np.asarray(pred, int), np.asarray(target, int)
    tp = int(((p == 1) & (t == 1)).sum())
    fp = int(((p == 1) & (t == 0)).sum())
    fn = int(((p == 0) & (t == 1)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {'accuracy': float((p == t).mean()), 'precision': precision, 'recall': recall, 'f1': f1,
            'n': int(len(t)), 'majority_rate': float(max(t.mean(), 1 - t.mean()))}


def regression_metrics(pred, target):
    p, t = np.asarray(pred, float), np.asarray(target, float)
    err = p - t
    return {'mae': float(np.abs(err).mean()), 'mse': float((err ** 2).mean()),
            'rmse': float(np.sqrt((err ** 2).mean())), 'mape': float(np.abs(err / t).mean() * 100)}


def _blocks(n, block, draws, seed):
    rng = np.random.Generator(np.random.PCG64(seed))
    k = int(np.ceil(n / block))
    starts = rng.integers(0, max(n - block + 1, 1), size=(draws, k))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(draws, -1)[:, :n]
    return np.minimum(idx, n - 1)


def block_bootstrap(values, block=14, draws=2000, seed=20260924):
    """95 % percentile interval of the mean under a moving-block bootstrap (deterministic)."""
    x = np.asarray(values, float)
    idx = _blocks(len(x), block, draws, seed)
    means = x[idx].mean(1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def paired_block_bootstrap(a, b, block=14, draws=2000, seed=20260924):
    return block_bootstrap(np.asarray(a, float) - np.asarray(b, float), block, draws, seed)


def _load(fit_dir):
    rec = json.loads((Path(fit_dir) / 'predictions.json').read_text())
    return [r['pred'] for r in rec], [r['target'] for r in rec]


def report(fits_dir, paper_direction=0.804):
    """Markdown table over fits/<task>/<arm>/seed*/predictions.json; every fit is one-shot."""
    fits_dir = Path(fits_dir)
    lines = ['| task | arm | seeds | accuracy / MAE mean | range | vs paper | vs LSTM (95 % CI) |',
             '|---|---|---|---|---|---|---|']
    for task in ('classification', 'regression'):
        tdir = fits_dir / task
        if not tdir.exists():
            continue
        per_arm = {}
        for arm_dir in sorted(p for p in tdir.iterdir() if p.is_dir()):
            vals, hits = [], []
            for seed_dir in sorted(arm_dir.glob('seed*')):
                if not (seed_dir / 'predictions.json').exists():
                    continue
                p, t = _load(seed_dir)
                if task == 'classification':
                    vals.append(direction_metrics(p, t)['accuracy'])
                    hits.append(np.asarray(p, int) == np.asarray(t, int))
                else:
                    vals.append(regression_metrics(p, t)['mae'])
            if vals:
                per_arm[arm_dir.name] = (vals, hits)
        for arm, (vals, hits) in per_arm.items():
            mean = float(np.mean(vals))
            vs_paper = f'{(mean - paper_direction) * 100:+.1f} pp' if task == 'classification' else '—'
            vs_lstm = '—'
            if task == 'classification' and arm != 'lstm' and 'lstm' in per_arm and hits and per_arm['lstm'][1]:
                a = np.mean(hits, 0)
                b = np.mean(per_arm['lstm'][1], 0)
                lo, hi = paired_block_bootstrap(a, b)
                vs_lstm = f'{(a.mean() - b.mean()) * 100:+.1f} pp [{lo * 100:+.1f}, {hi * 100:+.1f}]'
            lines.append(f'| {task} | {arm} | {len(vals)} | {mean:.4f} | {min(vals):.4f}–{max(vals):.4f} | {vs_paper} | {vs_lstm} |')
    return '\n'.join(lines)
