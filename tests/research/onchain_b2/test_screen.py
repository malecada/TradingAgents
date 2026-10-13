import numpy as np
import pandas as pd

from tradingagents.research.onchain_b2 import config, screen as SC


def _weekly(rng):
    idx = pd.date_range('2017-10-02', '2024-12-23', freq='7D')
    n = len(idx)
    sig = rng.normal(size=n)
    df = pd.DataFrame({'f0_r1__x': rng.normal(size=n), 'f1_sig__z8': sig, 'f3a_noise__z8': rng.normal(size=n),
                       'f2_noise__z8': rng.normal(size=n), 'f3b_noise__z8': rng.normal(size=n)}, index=idx)
    df['T2'] = (sig + 0.3 * rng.normal(size=n) > 0).astype(float)
    df['T3'] = 2 * sig + 0.3 * rng.normal(size=n)
    df['T4'] = rng.normal(size=n)
    df['T5'] = rng.normal(size=n)
    return df


def _daily(rng):
    idx = pd.date_range('2017-10-02', '2024-12-30', freq='D')
    n = len(idx)
    df = pd.DataFrame({'f0_r1__x': rng.normal(size=n), 'f1_sig__z8': rng.normal(size=n),
                       'f3a_noise__z8': rng.normal(size=n), 'f2_noise__z8': rng.normal(size=n),
                       'f3b_noise__z8': rng.normal(size=n)}, index=idx)
    df['T1'] = (rng.random(n) > 0.5).astype(float)
    return df


def test_folds_purge_and_years():
    idx = pd.date_range('2017-10-02', '2024-12-23', freq='7D')
    f = SC.folds(idx, [2019], purge_days=7)
    year, train, test = f[0]
    assert year == 2019 and idx[train].max() == pd.Timestamp('2018-12-24') and idx[test].min() == pd.Timestamp('2019-01-07')
    assert (idx[test].year == 2019).all()


def test_screen_finds_real_signal_and_rejects_noise():
    rng = np.random.default_rng(1)
    cfg = config.load()
    res = SC.run_screen({'weekly': _weekly(rng), 'daily': _daily(rng)}, cfg)
    get = {(r['target'], r['family'], r['set']): r for r in res}
    assert len(res) == 5 * 2 * 4
    assert get[('T3', 'linear', 'S1')]['passed'] and get[('T3', 'linear', 'S1')]['wins'] >= 4
    assert get[('T2', 'linear', 'S1')]['passed']
    assert not get[('T3', 'linear', 'S2')]['passed'] and not get[('T1', 'linear', 'S1')]['passed']
    sel = SC.select(res, cfg)
    assert 1 <= len(sel) <= 3 and all(s['set'] == 'S1' for s in sel)
    text = SC.report(res, sel)
    assert '| T3 | linear | S1 vs S0 |' in text and 'Selected for the holdout' in text


def test_row_loss():
    assert np.allclose(SC.row_loss('regression', np.array([1.0, 2.0]), np.array([0.0, 2.0])), [1.0, 0.0])
    ll = SC.row_loss('classification', np.array([1.0, 0.0]), np.array([0.5, 0.5]))
    assert np.allclose(ll, [np.log(2), np.log(2)])


def test_select_prefers_graph_sets_on_ties():
    base = dict(target='T4', family='linear', passed=True, mean_diff=-0.1, hi=-0.05)
    res = [{**base, 'set': 'S1', 'comparator': 'S0'}, {**base, 'set': 'S3', 'comparator': 'S1'}]
    assert SC.select(res, {'gate': {'max_selected': 1}})[0]['set'] == 'S3'