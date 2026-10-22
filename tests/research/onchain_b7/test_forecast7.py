# tests/research/onchain_b7/test_forecast7.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b7 import config, forecast7 as F

CFG = config.load()
SMALL = {**CFG, 'families': ['ridge', 'trees_es'], 'folds': {'inner_len': 400, 'min_train': 200},
         'models': {**CFG['models'], 'trees_es': {**CFG['models']['trees_es'], 'max_iter': 30, 'min_iter': 5}},
         'gate': {**CFG['gate'], 'draws': 200, 'block': 24}}


def _table(start, end, rng):
    idx = pd.date_range(start, end, freq='6h')
    n = len(idx)
    sig = rng.normal(size=n)
    t = pd.DataFrame({'h0_r1': rng.normal(size=n), 'px_rv6': rng.normal(size=n), 'rg_range1': rng.normal(size=n), 'mk_iv': rng.normal(size=n),
                      'eth_in_val__h1z': rng.normal(size=n), 'act_tx_count__h1z': rng.normal(size=n),
                      'n_eth_in_val__ex1': rng.normal(size=n), 'ev_since_10m': rng.normal(size=n), 'ix_eth_val_rv6': rng.normal(size=n),
                      'n_gs_active__ex1': sig, 'lab_eth_in_val__h1z': rng.normal(size=n)}, index=idx)
    y = pd.DataFrame({'V6': 2 * sig + 0.3 * rng.normal(size=n), 'J6': (sig > 1.3).astype(float)}, index=idx)
    return t, y


def test_set_prefixes_fits_and_comparisons():
    assert F.set_prefixes('Y2', 'B', CFG) == ['h0_', 'px_', 'rg_', 'mk_', 'n_eth_', 'n_stable_', 'n_act_', 'ev_', 'ix_', 'n_gs_', 'n_tk_', 'n_cl_', 'n_is_']
    assert F.set_prefixes('X1a', 'A', CFG) == ['h0_', 'px_', 'rg_', 'eth_', 'stable_', 'act_']
    assert len(F.fits(CFG)) == 11 and F.fits(CFG)[-1] == ('trees_fixed', 'Y2')
    comps = F.comparisons(CFG)
    assert len(comps) == 11 and comps[0] == (('ridge', 'Y1'), ('ridge', 'X1')) and comps[-1] == (('trees_es', 'Y2'), ('trees_fixed', 'Y2'))


def test_samples_window_mask_and_finite_rows():
    rng = np.random.default_rng(10)
    t, y = _table('2021-01-01', '2022-03-31', rng)
    t.loc[t.index[300], 'n_gs_active__ex1'] = np.nan                                 # one incomplete row inside the window
    t.loc[t.index[301], 'lab_eth_in_val__h1z'] = np.nan                              # a column no set uses
    cfg = {**SMALL, 'tracks': {**SMALL['tracks'], 'B': {**SMALL['tracks']['B'], 'start': '2021-02-01', 'end': '2022-01-31'}}}
    s = F.samples('B', t, y, cfg)
    assert s.index.min() == pd.Timestamp('2021-02-01') and s.index.max() == pd.Timestamp('2022-01-31 18:00')
    assert t.index[300] not in s.index and t.index[301] in s.index
    assert 'lab_eth_in_val__h1z' not in s.columns and 'mk_iv' in s.columns
    assert np.isnan(s.loc[pd.Timestamp('2022-01-31 18:00'), 'V6']) and np.isfinite(s.loc[pd.Timestamp('2022-01-31 12:00'), 'V6'])
    a = F.samples('A', t.drop(columns=['mk_iv']), y, {**cfg, 'tracks': {**cfg['tracks'], 'A': {**cfg['tracks']['A'], 'start': '2021-02-01', 'end': '2022-01-31'}}})
    assert 'mk_iv' not in a.columns and len(a) == len(s)


def test_predict_compare_criteria_and_report():
    rng = np.random.default_rng(11)
    cfg = {**SMALL, 'targets': {'V6': CFG['targets']['V6'], 'J6': CFG['targets']['J6']},
           'tracks': {'A': {**SMALL['tracks']['A'], 'start': '2019-01-01', 'end': '2024-12-31'},
                      'B': {**SMALL['tracks']['B'], 'start': '2021-04-01', 'end': '2026-10-12'}}}
    ta, ya = _table('2019-01-01', '2024-12-31', rng)
    sa = F.samples('A', ta.drop(columns=['mk_iv']), ya, cfg)
    P, meta = F.predict_all(sa, 'V6', 'A', cfg)
    assert {'ridge:X0', 'trees_es:Y2', 'trees_fixed:Y2', 'y', 'const', 'tested'} <= set(P.columns)
    assert P['tested'].sum() == (sa.index.year >= 2020).sum()                       # every test-year row is tested (last row 2024-12-31 00:00 keeps V6)
    assert set(meta['trees_es:Y2']) == {2020, 2021, 2022, 2023, 2024} and meta['trees_es:Y2'][2022]['n_iter'] >= 5
    res = F.compare(P, 'V6', 'A', cfg)
    assert len(res) == 11
    get = {(r['family'], r['set'], r['comparator']): r for r in res}
    assert get[('ridge', 'Y2', 'Y1')]['passed'] and get[('ridge', 'Y2', 'Y1')]['criterion'] == 'interval+years'
    assert not get[('ridge', 'X1', 'X0')]['passed'] and get[('trees_es|trees_fixed', 'Y2', 'Y2')]['n'] > 0
    assert get[('ridge', 'Y2', 'X0')]['gain_set'] > 0.5 and abs(get[('ridge', 'X1', 'X0')]['gain_set']) < 0.1
    tb, yb = _table('2021-04-01', '2026-10-12', rng)
    sb = F.samples('B', tb, yb, cfg)
    Pb, _ = F.predict_all(sb, 'J6', 'B', cfg)
    rb = F.compare(Pb, 'J6', 'B', cfg)
    assert len(rb) == 22
    gb = {(r['family'], r['set'], r['group']): r for r in rb}
    assert gb[('trees_es', 'Y2', '2022-24')]['criterion'] == 'interval+sign' and gb[('trees_es', 'Y2', '2025-26')]['criterion'] == 'sign'
    assert gb[('trees_es', 'Y2', '2022-24')]['passed'] and gb[('trees_es', 'Y2', '2022-24')]['loss_constant'] > gb[('trees_es', 'Y2', '2022-24')]['loss_set']
    text = F.report(res + rb)
    assert '| A | V6 | ridge | Y2 vs Y1 | 2020-24 |' in text and '| B | J6 | trees_es | Y2 vs Y1 | 2025-26 |' in text
    detail = F.detail_report({'A_V6': meta})
    assert 'trees_es:Y2' in detail and '2022' in detail
