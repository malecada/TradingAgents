# tests/research/onchain_b7/test_features7.py
import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b7 import config, features7 as F

CFG = config.load()


def _weekly(n_weeks, rng):
    idx = pd.date_range('2024-01-01', periods=168 * n_weeks, freq='h')
    slot = idx.dayofweek * 24 + idx.hour
    return pd.Series(100.0 + 5.0 * slot + rng.normal(0, 0.1, len(idx)), index=idx)


def test_seasonal_excess_is_causal_and_needs_four_occurrences():
    rng = np.random.default_rng(1)
    x = _weekly(12, rng)
    a = F.seasonal_excess(x, 8, 4)
    assert a.iloc[:4 * 168].isna().all() and a.iloc[4 * 168:].notna().all()
    assert np.abs(a.iloc[4 * 168:]).max() < 0.01                             # the profile removes the weekly pattern
    y = x.copy()
    y.iloc[10 * 168 + 5] = 1e6                                               # one spike in week 10
    b = F.seasonal_excess(y, 8, 4)
    pd.testing.assert_series_equal(a.iloc[:10 * 168 + 5], b.iloc[:10 * 168 + 5])   # nothing earlier changes
    assert b.iloc[10 * 168 + 5] > 5                                          # the spike hour is far above its profile
    assert np.isclose(b.iloc[11 * 168 + 5], a.iloc[11 * 168 + 5], atol=0.05)   # median profile ignores one spike
    with pytest.raises(ValueError):
        F.seasonal_excess(x.iloc[[0, 1, 5]], 8, 4)


def test_multiscale_columns_windows_end_at_h():
    rng = np.random.default_rng(2)
    idx = pd.date_range('2023-01-01', periods=3000, freq='h')
    raw = pd.DataFrame({'eth_in_val': rng.gamma(2, 3, 3000), 'gs_active': rng.gamma(2, 3, 3000)}, index=idx)
    a = F.multiscale(raw, CFG['engineering'])
    kinds = {'ex1', 'z1', 's6z', 's24z', 's168z', 'burst'}
    assert set(a.columns) == {f'n_{s}__{k}' for s in raw.columns for k in kinds}
    b = F.multiscale(raw.assign(eth_in_val=raw['eth_in_val'].where(raw.index < idx[2500], 999.0)), CFG['engineering'])
    pd.testing.assert_frame_equal(a.iloc[:2500], b.iloc[:2500])              # future values never leak backwards
    assert b['n_eth_in_val__burst'].iloc[2500] > a['n_eth_in_val__burst'].iloc[2500]   # the hour's own value counts
    assert a['n_eth_in_val__s168z'].iloc[2400:].notna().all() and a['n_eth_in_val__s168z'].iloc[:1600].isna().all()
    assert a.abs().max().max() <= CFG['engineering']['clip']


def test_event_hours_since_last_large_deposit():
    idx = pd.date_range('2024-03-01', periods=400, freq='h')
    t = lambda s: int(pd.Timestamp(s, tz='UTC').timestamp())
    large = pd.DataFrame({'ts': [t('2024-03-02 10:30'), t('2024-03-02 11:10'), t('2024-03-05 00:00'), t('2024-03-06 03:00')],
                          'token': [1, 0, 2, 1], 'amount': [2e7, 9e3, 6e7, 1.2e7], 'direction': [1, 1, 1, -1]})
    e = F.event_hours(large, idx, CFG['events']['thresholds'], 168)
    h = lambda s: pd.Timestamp(s)
    assert list(e.columns) == ['ev_since_10m', 'ev_since_50m']
    assert e.loc[h('2024-03-02 09:00'), 'ev_since_10m'] == np.log1p(168)     # before the first event: capped
    assert e.loc[h('2024-03-02 10:00'), 'ev_since_10m'] == 0.0               # event inside the hour counts at its end
    assert e.loc[h('2024-03-02 11:00'), 'ev_since_10m'] == np.log1p(1)       # the ETH deposit does not count
    assert e.loc[h('2024-03-05 00:00'), 'ev_since_50m'] == 0.0 and e.loc[h('2024-03-04 23:00'), 'ev_since_50m'] == np.log1p(168)
    assert e.loc[h('2024-03-06 03:00'), 'ev_since_10m'] == np.log1p(27)      # withdrawals do not count
    assert e['ev_since_10m'].max() == np.log1p(168)


def test_interactions_are_products():
    idx = pd.date_range('2024-01-01', periods=3, freq='h')
    t = pd.DataFrame({'a': [1.0, 2.0, np.nan], 'b': [3.0, 0.5, 1.0]}, index=idx)
    out = F.interactions(t, [['ix_ab', 'a', 'b']])
    assert list(out.columns) == ['ix_ab'] and out['ix_ab'].tolist()[:2] == [3.0, 1.0] and np.isnan(out['ix_ab'].iloc[2])
