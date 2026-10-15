# tests/research/onchain_b4/test_screen4.py
import copy

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b.evaluate import _bootstrap_means
from tradingagents.research.onchain_b4 import config, screen4 as S


def test_chunked_bootstrap_equals_reference():
    x = np.random.default_rng(1).normal(size=500)
    assert np.allclose(S.bootstrap_means(x, 28, 300, 7, chunk=37), _bootstrap_means(x, 28, 300, 7))


def _frames(rng):
    hi = pd.date_range('2017-10-02', '2024-12-31 23:00', freq='6h')
    n = len(hi)
    sig = rng.normal(size=n)
    h = pd.DataFrame({'h0_r1': rng.normal(size=n), 'eth_x__h1z': sig, 'stable_x__h1z': rng.normal(size=n),
                      'act_x__h1z': rng.normal(size=n)}, index=hi)
    for t in ('R1', 'R6', 'R24', 'V6'):
        h[t] = rng.normal(size=n)
    h['V24'] = 2 * sig + 0.3 * rng.normal(size=n)
    di = pd.date_range('2017-10-02', '2024-12-30', freq='D')
    d = pd.DataFrame({'f0_r1': rng.normal(size=len(di)), 'cmf_x__z28': rng.normal(size=len(di)),
                      'cmo_x__z28': rng.normal(size=len(di))}, index=di)
    d['T1'] = (rng.random(len(di)) > 0.5).astype(float)
    d['R7'], d['V7'] = rng.normal(size=len(di)), rng.normal(size=len(di))
    return {'hourly': h, 'daily': d}


def test_screen4_counts_signal_constant_columns_and_selection():
    cfg = copy.deepcopy(config.load())
    cfg['families'] = ['linear']
    res = S.run_screen4(_frames(np.random.default_rng(4)), cfg)
    assert len(res) == 21
    get = {(r['target'], r['set']): r for r in res}
    assert get[('V24', 'HE')]['passed'] and get[('V24', 'HA')]['passed'] and not get[('V24', 'HS')]['passed']
    assert not get[('R1', 'HE')]['passed'] and not get[('T1', 'DF')]['passed']
    assert 'r2c_HE' in get[('V24', 'HE')]['extra'] and 'llgain_DF' in get[('T1', 'DF')]['extra']
    sel = S.select4(res, cfg)
    assert sel and sel == sorted(sel, key=lambda s: s['dev_hi'] / get[(s['target'], s['set'])]['loss_comparator'])
    assert [s['target'] for s in sel[:2]] == ['V24', 'V24']           # noise may add a chance pass after them
    text = S.report4(res, sel)
    assert '21 comparisons' in text and 'V24' in text and 'vs constant' in text


def test_evaluate4_refits_and_applies_holm():
    cfg = config.load()
    rng = np.random.default_rng(5)
    f = _frames(rng)
    hold = _frames(np.random.default_rng(6))
    for k in hold:
        hold[k].index = hold[k].index + pd.DateOffset(years=8)
    sel = {'selected': [{'target': 'V24', 'family': 'linear', 'set': 'HE', 'comparator': 'H0'},
                        {'target': 'R1', 'family': 'linear', 'set': 'HE', 'comparator': 'H0'}]}
    out = S.evaluate4(f, hold, sel, cfg)
    assert [r['target'] for r in out] == ['V24', 'R1'] and out[0]['passed'] and not out[1]['passed']
    assert out[0]['p_holm'] >= out[0]['p']
