import numpy as np
import pandas as pd

from tradingagents.research.onchain_b3 import config, screen3 as S3


def _frames(rng):
    idx = pd.date_range('2017-10-02', '2024-12-23', freq='7D')
    n = len(idx)
    sig = rng.normal(size=n)
    w = pd.DataFrame({'f0_r__x': rng.normal(size=n), 'f1_a__z8': rng.normal(size=n), 'f4_sig__z8': sig,
                      'f5_noise__z8': rng.normal(size=n), 'f3a_noise__z8': rng.normal(size=n)}, index=idx)
    for t in ('T3', 'T4', 'T5', 'T6'):
        w[t] = rng.normal(size=n)
    w['T7'] = 2 * sig + 0.3 * rng.normal(size=n)
    w['T2'] = (rng.random(n) > 0.5).astype(float)
    di = pd.date_range('2017-10-02', '2024-12-30', freq='D')
    d = pd.DataFrame({c: rng.normal(size=len(di)) for c in ('f0_r__x', 'f1_a__z8', 'f4_sig__z8', 'f5_noise__z8', 'f3a_noise__z8')}, index=di)
    d['T1'] = (rng.random(len(di)) > 0.5).astype(float)
    return {'weekly': w, 'daily': d}


def test_screen3_counts_purges_and_signal():
    cfg = config.load()
    res = S3.run_screen3(_frames(np.random.default_rng(4)), cfg)
    assert len(res) == 7 * 2 * 3
    get = {(r['target'], r['family'], r['set']): r for r in res}
    assert get[('T7', 'linear', 'S5')]['passed'] and get[('T7', 'linear', 'S7')]['passed']
    assert not get[('T3', 'linear', 'S5')]['passed'] and not get[('T1', 'linear', 'S5')]['passed']
    sel = S3.select3(res, cfg)
    assert 1 <= len(sel) <= 3 and all(s['target'] == 'T7' for s in sel)


def test_purge_uses_target_horizon():
    idx = pd.date_range('2017-10-02', '2024-12-23', freq='7D')
    folds = S3.folds_for(idx, 'T6', config.load())
    year, train, test = folds[0]
    assert idx[train].max() == pd.Timestamp('2018-12-03')         # + 28 days <= 2019-01-01


def test_evaluate3_on_synthetic_holdout():
    rng = np.random.default_rng(6)
    def frame(a, b):
        idx = pd.date_range(a, b, freq='7D')
        sig = rng.normal(size=len(idx))
        return pd.DataFrame({'f0_r__x': rng.normal(size=len(idx)), 'f1_a__z8': rng.normal(size=len(idx)), 'f4_sig__z8': sig,
                             'T7': 2 * sig + 0.3 * rng.normal(size=len(idx))}, index=idx)
    sel = {'selected': [{'target': 'T7', 'family': 'linear', 'set': 'S5', 'comparator': 'S1'}]}
    res = S3.evaluate3({'weekly': frame('2017-10-02', '2024-12-23')}, {'weekly': frame('2025-01-06', '2026-10-05')}, sel, config.load())
    assert res[0]['n'] == 92 and res[0]['passed']