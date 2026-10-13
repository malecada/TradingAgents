"""Metrics (paper Eqs. 12–19, binary-up convention), circular moving-block bootstrap, gate report.

The report reads fits/<task>/<arm>/seed*/{result.json,predictions.json}. A cell
enters the tables only when result.json shows the frozen epoch count (SVM has
none); every other cell is listed as excluded, never silently dropped.
"""
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


def _bootstrap_means(values, block=14, draws=2000, seed=20260924):
    """Means of circular moving-block resamples: every day has equal inclusion probability."""
    x = np.asarray(values, float)
    n = len(x)
    if n < block:
        raise ValueError(f'series of {n} days is shorter than the {block}-day block')
    rng = np.random.Generator(np.random.PCG64(seed))
    k = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=(draws, k))
    idx = ((starts[:, :, None] + np.arange(block)[None, None, :]) % n).reshape(draws, -1)[:, :n]
    return x[idx].mean(1)


def block_bootstrap(values, block=14, draws=2000, seed=20260924):
    """95 % percentile interval of the mean (deterministic, circular 14-day blocks)."""
    means = _bootstrap_means(values, block, draws, seed)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def paired_block_bootstrap(a, b, block=14, draws=2000, seed=20260924):
    return block_bootstrap(np.asarray(a, float) - np.asarray(b, float), block, draws, seed)


def _load(fit_dir):
    rec = json.loads((Path(fit_dir) / 'predictions.json').read_text())
    return [r['pred'] for r in rec], [r['target'] for r in rec]


def _cells(fits_dir, task, expected_epochs, excluded):
    """{arm: [(seed, preds, targets)]} for complete cells; incomplete ones appended to `excluded`."""
    out = {}
    tdir = Path(fits_dir) / task
    if not tdir.exists():
        return out
    for arm_dir in sorted(p for p in tdir.iterdir() if p.is_dir()):
        for seed_dir in sorted(arm_dir.glob('seed*')):
            name = f'{task}/{arm_dir.name}/{seed_dir.name}'
            if not (seed_dir / 'predictions.json').exists() or not (seed_dir / 'result.json').exists():
                excluded.append(f'{name}: missing predictions/result')
                continue
            result = json.loads((seed_dir / 'result.json').read_text())
            if result.get('arm') != 'svm' and result.get('epochs_done') != expected_epochs:
                excluded.append(f"{name}: epochs_done={result.get('epochs_done')} (expected {expected_epochs})")
                continue
            p, t = _load(seed_dir)
            out.setdefault(arm_dir.name, []).append((seed_dir.name, p, t))
    return out


def report(fits_dir, gates=None, expected_epochs=None):
    """Markdown gate report for the registered M2 endpoints (gates.json)."""
    if gates is None or expected_epochs is None:
        from . import config
        gates = gates or json.loads((config.STUDY / 'gates.json').read_text())
        expected_epochs = expected_epochs or config.load('training')['epochs']
    primary = gates['primary']
    paper, close = primary['paper_value'], primary['close_if_abs_diff_le']
    bs = primary['bootstrap']
    boot = dict(block=bs['block_days'], draws=bs['draws'], seed=bs['seed'])
    excluded = []
    cls = _cells(fits_dir, 'classification', expected_epochs, excluded)
    reg = _cells(fits_dir, 'regression', expected_epochs, excluded)
    lines = []

    hits = {arm: np.mean([np.asarray(p, int) == np.asarray(t, int) for _, p, t in cells], 0) for arm, cells in cls.items()}
    if 'full' in hits:
        acc = float(hits['full'].mean())
        lo, hi = block_bootstrap(hits['full'], **boot)
        diff = acc - paper
        label = 'numerically close' if abs(diff) <= close else 'not numerically close'
        lines += ['## Primary endpoint', '',
                  f"Full-model 2024 direction accuracy, mean over {len(cls['full'])} seed(s): {acc:.4f} "
                  f"(95 % CI [{lo:.4f}, {hi:.4f}], circular {bs['block_days']}-day blocks); "
                  f"paper {paper:.3f}; difference {diff * 100:+.1f} pp → {label} (threshold ±{close * 100:.0f} pp).",
                  'The interval resamples days with the trained models held fixed; seed variability appears only in the range column.', '']

    lines += ['## Direction (classification)', '',
              '| task | arm | seeds | accuracy mean | range | 95 % CI | precision | recall | f1 | vs paper | vs LSTM (95 % CI) |',
              '|---|---|---|---|---|---|---|---|---|---|---|']
    for arm, cells in cls.items():
        m = [direction_metrics(p, t) for _, p, t in cells]
        accs = [x['accuracy'] for x in m]
        lo, hi = block_bootstrap(hits[arm], **boot)
        vs_lstm = '—'
        if arm != 'lstm' and 'lstm' in hits:
            dlo, dhi = paired_block_bootstrap(hits[arm], hits['lstm'], **boot)
            vs_lstm = f"{(hits[arm].mean() - hits['lstm'].mean()) * 100:+.1f} pp [{dlo * 100:+.1f}, {dhi * 100:+.1f}]"
        lines.append(f"| classification | {arm} | {len(cells)} | {np.mean(accs):.4f} | {min(accs):.4f}–{max(accs):.4f} | "
                     f"[{lo:.4f}, {hi:.4f}] | {np.mean([x['precision'] for x in m]):.4f} | {np.mean([x['recall'] for x in m]):.4f} | "
                     f"{np.mean([x['f1'] for x in m]):.4f} | {(np.mean(accs) - paper) * 100:+.1f} pp | {vs_lstm} |")

    perm = [arm for arm in cls if arm.endswith('-label_permutation')]
    if perm:
        lines += ['', '## Chance control', '']
        for arm in perm:
            majority = direction_metrics(cls[arm][0][1], cls[arm][0][2])['majority_rate']
            lo, hi = block_bootstrap(hits[arm], **boot)
            verdict = 'within' if lo <= majority <= hi else 'OUTSIDE'
            lines.append(f'- {arm}: accuracy {hits[arm].mean():.4f}, 95 % CI [{lo:.4f}, {hi:.4f}]; '
                         f'majority-class rate {majority:.4f} is {verdict} the interval.')

    lines += ['', '## Price level (regression, USD)', '',
              '| task | arm | seeds | MAE | RMSE | MAPE % | MAE range |', '|---|---|---|---|---|---|---|']
    for arm, cells in reg.items():
        m = [regression_metrics(p, t) for _, p, t in cells]
        maes = [x['mae'] for x in m]
        lines.append(f"| regression | {arm} | {len(cells)} | {np.mean(maes):.4f} | {np.mean([x['rmse'] for x in m]):.4f} | "
                     f"{np.mean([x['mape'] for x in m]):.4f} | {min(maes):.4f}–{max(maes):.4f} |")

    lines += ['', '## Excluded cells', '']
    lines += [f'- {e}' for e in excluded] if excluded else ['- none']
    return '\n'.join(lines)
