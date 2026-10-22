# tests/research/onchain_b7/test_models7.py
import numpy as np

from tradingagents.research.onchain_b7 import config, models7 as M

CFG = config.load()
ES = {**CFG['models']['trees_es'], 'max_iter': 80, 'min_iter': 5}


def _data(n, rng, flip_tail=False):
    X = rng.normal(size=(n, 6))
    y = 2.0 * X[:, 0] - X[:, 1] ** 2 + 0.3 * rng.normal(size=n)
    if flip_tail:
        tail = int(0.1 * n)
        y[-tail:] = -y[-tail:]
    return X, y


def test_choose_iter_uses_the_time_ordered_tail():
    rng = np.random.default_rng(7)
    X, y = _data(4000, rng)
    n_iter, losses = M.choose_iter('regression', X, y, ES)
    assert len(losses) == 80 and 5 <= n_iter <= 80 and n_iter > 20                 # signal: keeps boosting
    Xf, yf = _data(4000, rng, flip_tail=True)
    n_flip, _ = M.choose_iter('regression', Xf, yf, ES)
    assert n_flip == 5                                                             # a tail that contradicts the head stops at the minimum
    yc = (y > np.quantile(y, 0.9)).astype(float)
    n_cls, lc = M.choose_iter('classification', X, yc, ES)
    assert 5 <= n_cls <= 80 and len(lc) == 80


def test_fit_predict7_families_and_info():
    rng = np.random.default_rng(8)
    X, y = _data(3000, rng)
    cfg = {**CFG, 'models': {**CFG['models'], 'trees_es': ES}, 'folds': {**CFG['folds'], 'inner_len': 500}}
    base = ((y[:2500] - y[:2500].mean()) ** 2).mean()
    for fam in ('ridge', 'trees_es', 'trees_fixed'):
        info = {}
        p = M.fit_predict7(fam, 'regression', X[:2500], y[:2500], X[2500:], cfg, info)
        assert p.shape == (500,) and np.isfinite(p).all() and ((y[2500:] - p) ** 2).mean() < 0.6 * base
        assert ('n_iter' in info) == (fam == 'trees_es') and info['alpha'] == (None if fam != 'ridge' else info['alpha'])
    yc = (y > np.quantile(y, 0.8)).astype(float)
    p = M.fit_predict7('trees_es', 'classification', X[:2500], yc[:2500], X[2500:], cfg)
    assert p.shape == (500,) and (p >= 0).all() and (p <= 1).all() and p[yc[2500:] == 1].mean() > p[yc[2500:] == 0].mean()


def test_fit_predict7_single_class_fallback():
    rng = np.random.default_rng(9)
    X, y = _data(1000, rng)
    cfg = {**CFG, 'models': {**CFG['models'], 'trees_es': ES}}
    zeros = np.zeros(800)
    assert (M.fit_predict7('trees_es', 'classification', X[:800], zeros, X[800:], cfg) == 0.0).all()
    head_only = zeros.copy()
    head_only[-20:] = 1.0                                                          # positives only in the tail: the head has one class
    p = M.fit_predict7('trees_es', 'classification', X[:800], head_only, X[800:], cfg)
    assert p.shape == (200,) and np.isfinite(p).all()
