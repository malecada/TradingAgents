# tests/research/onchain_b6/test_forecast6.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b6 import config, forecast6 as F

CFG = config.load()


def _samples(start, end, rng):
    idx = pd.date_range(start, end, freq='6h')
    n = len(idx)
    sig = rng.normal(size=n)
    df = pd.DataFrame({'h0_r1': rng.normal(size=n), 'px_rv6': rng.normal(size=n), 'mk_iv': rng.normal(size=n),
                       'eth_in_val__h1z': rng.normal(size=n), 'gs_core2_share__h1z': sig, 'tk_usdt_in__h1z': rng.normal(size=n),
                       'tron_in_val__h1z': rng.normal(size=n)}, index=idx)
    df['V6'] = 2 * sig + 0.3 * rng.normal(size=n)
    df['V24'] = rng.normal(size=n)
    return df


def test_set_prefixes_and_run_all_criteria():
    cfg = {**CFG, 'families': ['linear']}
    assert F.set_prefixes('X2', 'B', cfg, False) == ['h0_', 'px_', 'mk_', 'eth_', 'stable_', 'gs_']
    assert F.set_prefixes('X5', 'A', cfg, True)[-1] == 'tron_'
    rng = np.random.default_rng(5)
    res = F.run_all({'A': _samples('2017-10-02', '2024-12-31', rng), 'B': _samples('2021-04-01', '2026-10-12', rng)}, cfg, with_tron=True)
    assert len(res) == 10 + 20                        # track A: 5 comparisons x 1 group x 2 targets; track B: x 2 groups
    get = {(r['track'], r['target'], r['set'], r['group']): r for r in res}
    assert get[('A', 'V6', 'X2', '2019-24')]['passed'] and not get[('A', 'V6', 'X3', '2019-24')]['passed']
    assert get[('B', 'V6', 'X2', '2022-24')]['passed'] and 'passed' in get[('B', 'V6', 'X2', '2025-26')]
    assert not get[('A', 'V24', 'X2', '2019-24')]['passed']
    text = F.report(res)
    assert '| A | V6 | linear | X2 vs X1 | 2019-24 |' in text


def test_tron_runs_only_its_own_comparison_on_its_subsample():
    cfg = {**CFG, 'families': ['linear']}
    rng = np.random.default_rng(6)
    res = F.run_all({'B': _samples('2021-04-01', '2026-10-12', rng)}, cfg, with_tron=True, only_tron=True)
    assert {(r['set'], r['comparator']) for r in res} == {('X5', 'X4')} and len(res) == 2 * 2
    base = F.run_all({'B': _samples('2021-04-01', '2026-10-12', rng).drop(columns=['tron_in_val__h1z'])}, cfg, with_tron=False)
    assert all(r['set'] != 'X5' for r in base) and len(base) == 2 * 4 * 2
