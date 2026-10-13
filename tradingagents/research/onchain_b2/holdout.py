"""Sealed-window confirmation (spec §9): runs only for a committed, unmodified selection;
each configuration is refitted once on all development samples and scored once."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

from ..onchain_b.evaluate import _bootstrap_means
from .dataset import columns
from .screen import TARGETS, fit_predict, row_loss


def committed_selection(path, repo):
    path, repo = Path(path), Path(repo)
    rel = str(path.resolve().relative_to(repo.resolve()))
    if subprocess.run(['git', '-C', str(repo), 'ls-files', '--error-unmatch', rel], capture_output=True).returncode:
        raise PermissionError('selection.json is not committed')
    if subprocess.run(['git', '-C', str(repo), 'diff', '--quiet', 'HEAD', '--', rel]).returncode:
        raise PermissionError('selection.json has uncommitted changes')
    return json.loads(path.read_text())


def selection_identity(path, repo):
    """The commit and blob of the committed selection that a holdout read is bound to."""
    path, repo = Path(path), Path(repo)
    rel = str(path.resolve().relative_to(repo.resolve()))
    git = lambda *a: subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True, check=True).stdout.strip()
    return {'head': git('rev-parse', 'HEAD'), 'blob': git('rev-parse', f'HEAD:{rel}')}


def holm(pvalues):
    p = np.asarray(pvalues, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        adj[i] = running
    return adj.tolist()


def evaluate(dev, hold, selection, cfg):
    g, f = cfg['gate'], cfg['folds']
    out = []
    for s in selection['selected']:
        kind, task = TARGETS[s['target']]
        d = dev[kind][dev[kind][s['target']].notna()].sort_index()
        h = hold[kind][hold[kind][s['target']].notna()].sort_index()
        yd, yh = d[s['target']].to_numpy(float), h[s['target']].to_numpy(float)
        loss = {}
        for name in (s['set'], s['comparator']):
            cols = columns(d, name)
            pred = fit_predict(s['family'], task, d[cols].to_numpy(float), yd, h[cols].to_numpy(float),
                               f['inner_len'][kind], cfg)
            loss[name] = row_loss(task, yh, pred)
        diff = loss[s['set']] - loss[s['comparator']]
        means = _bootstrap_means(diff, block=g['block'][kind], draws=g['draws'], seed=g['seed'])
        out.append({**{k: s[k] for k in ('target', 'family', 'set', 'comparator')}, 'n': int(len(diff)),
                    'mean_diff': float(diff.mean()), 'p': float((means >= 0).mean())})
    for r, adj in zip(out, holm([r['p'] for r in out]) if out else []):
        r['p_holm'] = adj
        r['passed'] = bool(adj < g['alpha'] and r['mean_diff'] < 0)
    return out