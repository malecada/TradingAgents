# tradingagents/research/onchain_b7/models7.py
"""Model families (spec §6): ridge / logistic with B2's alpha search, B4's fixed trees, and
trees whose iteration count is chosen on the time-ordered last part of the training window."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

from ..onchain_b2.screen import fit_predict, row_loss

_ES_KEYS = ('tail_frac', 'min_iter', 'min_tail_pos')


def _tree(task, params):
    cls = HistGradientBoostingClassifier if task == 'classification' else HistGradientBoostingRegressor
    return cls(**{k: v for k, v in params.items() if k not in _ES_KEYS}, early_stopping=False)


def _predict(model, task, X):
    return model.predict_proba(X)[:, 1] if task == 'classification' else model.predict(X)


def choose_iter(task, Xtr, ytr, c, info=None):
    """Fit on the first (1 − tail_frac) rows, score every stage on the last tail_frac rows and
    return the stage count with the smallest tail loss, at least min_iter, with the losses.
    Classification falls back to min_iter when the head or the tail holds a single class or
    the tail holds fewer than min_tail_pos positives (a positive-free tail rewards every
    extra stage); the tail support is recorded in `info`."""
    n = len(Xtr)
    tail = max(1, int(round(c['tail_frac'] * n)))
    head_y, tail_y = ytr[:-tail], ytr[-tail:]
    if info is not None:
        info['tail_n'] = int(tail)
        if task == 'classification':
            info['tail_pos'] = int(tail_y.sum())
    if task == 'classification' and (len(np.unique(head_y)) < 2 or len(np.unique(tail_y)) < 2
                                     or tail_y.sum() < c['min_tail_pos']):
        return int(c['min_iter']), np.array([])
    m = _tree(task, c).fit(Xtr[:-tail], head_y)
    stages = m.staged_predict_proba(Xtr[-tail:]) if task == 'classification' else m.staged_predict(Xtr[-tail:])
    losses = np.array([row_loss(task, ytr[-tail:], p[:, 1] if task == 'classification' else p).mean() for p in stages])
    lo = min(int(c['min_iter']), len(losses))
    return int(lo + np.argmin(losses[lo - 1:])), losses


def fit_predict7(family, task, Xtr, ytr, Xte, cfg, info=None):
    if family in ('ridge', 'trees_fixed'):
        return fit_predict('linear' if family == 'ridge' else 'trees', task, Xtr, ytr, Xte, cfg['folds']['inner_len'], cfg, info)
    if family != 'trees_es':
        raise ValueError(f'unknown family {family}')
    if info is not None:
        info['alpha'] = None
    if task == 'classification' and len(np.unique(ytr)) < 2:
        return np.full(len(Xte), float(ytr.mean()))
    c = cfg['models']['trees_es']
    n_iter, _ = choose_iter(task, Xtr, ytr, c, info)
    if info is not None:
        info['n_iter'] = n_iter
    return _predict(_tree(task, {**c, 'max_iter': n_iter}).fit(Xtr, ytr), task, Xte)
