# tests/research/onchain_b8/test_forecast8.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b8 import config, forecast8 as F

CFG = config.load()
SMALL = {**CFG, 'folds': {'test_years': [2022, 2023], 'inner_len': 200, 'min_train': 100, 'min_year_wins': 2},
         'models': {**CFG['models'], 'trees_es': {**CFG['models']['trees_es'], 'max_iter': 30, 'min_iter': 5}},
         'gate': {**CFG['gate'], 'draws': 200, 'block': 24}, 'window': {'first_day': '2021-01-01', 'last_day': '2023-12-31'}}


def _panel(rng, n_tok=6, start='2021-01-01', end='2023-12-31'):
    hours = pd.date_range(start, end, freq='12h')
    frames = []
    for j in range(n_tok):
        sig = rng.normal(size=len(hours))
        f = pd.DataFrame({'h0_r1': rng.normal(size=len(hours)), 'px_rv6': rng.normal(size=len(hours)), 'xs_h0_rv24': rng.normal(size=len(hours)),
                          'n_dep_usd__z1': rng.normal(size=len(hours)), 'xs_n_dep_usd__ex1': sig, 'other': 1.0,
                          'V6': 2 * sig + 0.3 * rng.normal(size=len(hours)), 'V24': rng.normal(size=len(hours)), 'XV24': rng.normal(size=len(hours))},
                         index=hours)
        f['token'] = np.int16(j)
        frames.append(f)
    return pd.concat(frames).sort_index(kind='stable')


def test_samples_and_prefixes():
    assert F.set_prefixes('P2', CFG) == ['h0_', 'px_', 'xs_h0_', 'n_', 'xs_n_']
    rng = np.random.default_rng(31)
    p = _panel(rng)
    p.iloc[10, p.columns.get_loc('n_dep_usd__z1')] = np.nan
    s = F.samples(p, SMALL)
    assert 'other' not in s.columns and 'token' in s.columns and len(s) == len(p) - 1
    assert s.loc[pd.Timestamp('2023-12-31 00:00'), 'V24'].isna().all() and s.loc[pd.Timestamp('2023-12-31 00:00'), 'V6'].notna().all()   # the 12-hourly range ends at 00:00


def test_compare_weights_hours_not_rows():
    rng = np.random.default_rng(32)
    p = _panel(rng)
    s = F.samples(p, SMALL)
    P, meta = F.predict_all(s, 'V6', SMALL)
    assert {'ridge:P0', 'trees_es:P2', 'token', 'y', 'const', 'tested'} <= set(P.columns) and set(meta['ridge:P2']) == {2022, 2023}
    res = F.compare(P, 'V6', SMALL)
    assert len(res) == 6
    get = {(r['family'], r['set'], r['comparator']): r for r in res}
    r = get[('ridge', 'P2', 'P1')]
    assert r['passed'] and r['criterion'] == 'interval+years' and r['n_hours'] == P['tested'].sum() // 6 and r['n_rows'] == P['tested'].sum()
    assert not get[('ridge', 'P1', 'P0')]['passed'] and get[('ridge', 'P2', 'P0')]['gain_set'] > 0.5
    # hour weighting: duplicate every row of one hour 50 times -> the per-hour mean is unchanged, so the statistics are too
    h = P.index[P['tested'].to_numpy()][0]
    dup = pd.concat([P] + [P.loc[[h]]] * 50).sort_index(kind='stable')
    r2 = {(x['family'], x['set'], x['comparator']): x for x in F.compare(dup, 'V6', SMALL)}[('ridge', 'P2', 'P1')]
    assert r2['n_hours'] == r['n_hours'] and np.isclose(r2['mean_diff'], r['mean_diff']) and r2['n_rows'] == r['n_rows'] + 300
    t = F.per_token(P, 'V6', SMALL)
    assert set(t['token']) == set(range(6)) and len(t) == 6 * 6 and (t['n'] > 0).all()
    text = F.report(res)
    assert '| V6 | ridge | P2 vs P1 |' in text


def test_predict_all_prefiltered_sorted_input_gives_identical_predictions():
    rng = np.random.default_rng(33)
    p = _panel(rng)
    s = F.samples(p, SMALL)
    P1, _ = F.predict_all(s, 'V6', {**SMALL, 'families': ['ridge']})
    d = s[s['V6'].notna()]                                                             # already filtered and hour-sorted
    P2, _ = F.predict_all(d, 'V6', {**SMALL, 'families': ['ridge']})
    pd.testing.assert_frame_equal(P1, P2)
    assert F.needed_columns(SMALL, p) == sorted(set(['token'] + [c for c in p.columns if c.startswith(tuple(F.set_prefixes('P2', SMALL)))] + list(SMALL['targets'])))


def test_bundle_predictions_match_frame_path_and_folds_are_slices():
    rng = np.random.default_rng(34)
    p = _panel(rng)
    s = F.samples(p, SMALL)
    cfg = {**SMALL, 'families': ['ridge']}
    P1, _ = F.predict_all(s, 'V6', cfg)
    b = F.bundle(s[s['V6'].notna()], 'V6', cfg)
    assert set(b) == {'X', 'cols', 'y', 'token', 'index'} and b['X'].dtype == np.float32 and b['X'].shape[1] == len(b['cols'])
    P2, _ = F.predict_bundle(b, 'V6', cfg)
    pd.testing.assert_frame_equal(P1, P2)
    fl = F.fold_slices(b['index'], cfg['folds']['test_years'], 6 / 24, cfg['folds']['min_train'])
    assert [yr for yr, _, _ in fl] == [2022, 2023] and all(isinstance(tr, slice) and isinstance(te, slice) for _, tr, te in fl)
    assert fl[0][0] == 2022 and fl[0][1].start == 0 and fl[0][2].start == fl[0][1].stop or fl[0][2].start > fl[0][1].stop
    yrs = b['index'].year
    assert (yrs[fl[1][2]] == 2023).all() and (b['index'][:fl[1][1].stop] + pd.Timedelta(days=6 / 24) <= pd.Timestamp('2023-01-01')).all()


def test_samples_for_one_target_matches_filtered_full_samples():
    rng = np.random.default_rng(35)
    p = _panel(rng)
    p.iloc[7, p.columns.get_loc('h0_r1')] = np.nan
    full = F.samples(p, SMALL)
    one = F.samples(p, SMALL, target='V24')
    ref = full[full['V24'].notna()].drop(columns=['V6', 'XV24'])
    pd.testing.assert_frame_equal(one, ref[one.columns])
    assert 'V6' not in one.columns and len(one) == len(ref) and one['V24'].notna().all()


def test_load_bundle_from_parquet_matches_frame_path(tmp_path):
    rng = np.random.default_rng(36)
    p = _panel(rng)
    p.iloc[7, p.columns.get_loc('h0_r1')] = np.nan
    p.iloc[9, p.columns.get_loc('V24')] = np.nan
    feat = [c for c in p.columns if c not in ('token', 'V6', 'V24', 'XV24', 'other')]
    q = p.copy()
    q[feat] = q[feat].astype(np.float32)
    q.to_parquet(tmp_path / 'panel.parquet')
    ref = F.bundle(F.samples(q, SMALL, target='V24'), 'V24', SMALL)
    b = F.load_bundle(tmp_path / 'panel.parquet', 'V24', SMALL)
    assert b['cols'] == ref['cols'] and np.array_equal(b['X'], ref['X']) and np.array_equal(b['y'], ref['y'])
    assert np.array_equal(b['token'], ref['token']) and b['index'].equals(ref['index'])
    sup = F.support(tmp_path / 'panel.parquet', SMALL)
    full = F.samples(q, SMALL)
    assert sup['V24']['n'] == int(full['V24'].notna().sum()) and sup['V6']['years'][2021]['tokens'] == 6
    assert sup['V24']['years'][2023]['hours'] == full.loc['2023', 'V24'].dropna().index.nunique()
