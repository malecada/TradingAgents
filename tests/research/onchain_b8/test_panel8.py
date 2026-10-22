# tests/research/onchain_b8/test_panel8.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b8 import config, hourly8 as Hh, panel8 as P

CFG = config.load()


def _panel(n_tok, hours, rng):
    frames = []
    for j in range(n_tok):
        f = pd.DataFrame({'n_dep_usd__s24z': rng.normal(size=len(hours)), 'n_dep_usd__ex1': rng.normal(size=len(hours)),
                          'n_dep_usd__z1': rng.normal(size=len(hours)), 'h0_rv24': rng.gamma(2, 1, len(hours)),
                          'h0_lvol24': rng.normal(size=len(hours)), 'px_rv6': rng.gamma(2, 1, len(hours)),
                          'V6': rng.normal(size=len(hours)), 'V24': rng.normal(size=len(hours)) + j}, index=hours)
        f['token'] = np.int16(j)
        frames.append(f)
    return pd.concat(frames)


def test_token_series_and_frame_entry():
    rng = np.random.default_rng(21)
    hours = pd.date_range('2023-01-01', periods=24 * 200, freq='h')
    days = [pd.DataFrame({'hour': np.repeat(hours[k * 24:(k + 1) * 24], 2), 'token': np.tile(np.array([0, 1], np.int16), 24),
                          **{s: rng.gamma(2, 3, 48) for s in Hh.SERIES}}) for k in range(200) if k != 50]   # day 50 missing
    s = P.token_series(days, hours, 1)
    assert s.shape == (4800, 7) and list(s.columns) == Hh.SERIES and s.iloc[50 * 24:51 * 24].isna().all().all()
    assert s.iloc[0, 0] == days[0].loc[1, 'dep_usd']
    bars = pd.DataFrame({'close': 10 * np.exp(np.cumsum(rng.normal(0, 0.01, 4000))), 'qvol': rng.gamma(2, 1e5, 4000)},
                        index=hours[400:4400])
    f = P.token_frame(s, bars, CFG)
    assert f.index.min() == hours[400] + pd.Timedelta(days=30) and f.index.max() == hours[4399]
    assert len([c for c in f.columns if c.startswith('n_')]) == 42 and {'h0_rv24', 'px_rv6', 'V6', 'V24'} <= set(f.columns)
    assert 'token' not in f.columns


def test_cross_section_min_tokens_and_xv24():
    rng = np.random.default_rng(22)
    hours = pd.date_range('2023-01-01', periods=10, freq='h')
    cfg = {**CFG, 'panel': {**CFG['panel'], 'min_tokens_hour': 3}}
    p = _panel(4, hours, rng)
    p = p[~((p.index == hours[2]) & (p['token'] >= 2))]                                 # hour 2 has 2 tokens
    x = P.cross_section(p, cfg)
    cols = ['xs_n_dep_usd__s24z', 'xs_n_dep_usd__ex1', 'xs_h0_rv24', 'xs_h0_lvol24']
    assert set(c for c in x.columns if c.startswith('xs_')) == set(cols) and 'XV24' in x.columns
    h0 = x.loc[hours[0]]
    assert np.isclose(h0['xs_h0_rv24'].mean(), 0) and np.isclose(h0['xs_h0_rv24'].std(ddof=1), 1)
    assert np.allclose(h0['XV24'], h0['V24'] - h0['V24'].mean())
    assert x.loc[hours[2], cols + ['XV24']].isna().all().all() and x.loc[hours[3], cols].notna().all().all()
    assert len(x) == len(p) and (x['token'] == p['token']).all()
