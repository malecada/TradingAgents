# tests/research/onchain_b4/test_dataset4.py
from datetime import date, timedelta

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b4 import config, dataset4 as D, flows


def _raw(start, hours, seed=1):
    idx = pd.date_range(start, periods=hours, freq='h')
    rng = np.random.default_rng(seed)
    return pd.DataFrame({c: rng.gamma(2.0, 3.0, len(idx)) for c in flows.SERIES + flows.LAB}, index=idx)


def _bars(start, hours, seed=2):
    idx = pd.date_range(start, periods=hours, freq='h')
    rng = np.random.default_rng(seed)
    return pd.DataFrame({'close': 1000 * np.exp(np.cumsum(rng.normal(0, 0.01, len(idx)))),
                         'qvol': rng.gamma(2.0, 1e6, len(idx))}, index=idx)


def test_hourly_transforms_are_causal_and_counted():
    c = config.load()['hourly']
    raw = _raw('2024-01-01', 1500)
    a = D.transform_hourly(raw, c)
    changed = raw.copy()
    changed.iloc[1200:] *= 5
    b = D.transform_hourly(changed, c)
    pd.testing.assert_frame_equal(a.iloc[:1200], b.iloc[:1200])
    registered = [x for x in a.columns if not x.startswith('lab_')]
    assert len(registered) == 32 and a.iloc[1000:].notna().all().all()
    const = pd.Series(3.0, index=raw.index)
    assert (D.zscore(const, 168, 120, 10.0).dropna() == 0).all()


def test_price_features_and_targets():
    bars = _bars('2024-01-01', 400)
    f, t = D.price_features(bars), D.hourly_targets(bars)
    lc = np.log(bars['close'])
    h = bars.index[200]
    assert np.isclose(f.loc[h, 'h0_r24'], lc.iloc[200] - lc.iloc[176])
    assert np.isclose(t.loc[h, 'R6'], lc.iloc[206] - lc.iloc[200])
    r = lc.diff()
    assert np.isclose(t.loc[h, 'V6'], np.log(np.sqrt((r.iloc[201:207] ** 2).sum())))
    assert len([x for x in f.columns if x.startswith('h0_')]) == 8


def test_missing_bar_excludes_dependent_rows():
    bars = _bars('2024-06-01', 1200).drop(pd.Timestamp('2024-06-30 12:00'))
    cfg = config.load()
    trans = D.transform_hourly(_raw('2024-05-01', 2000), cfg['hourly'])
    s, ex = D.hourly_samples(trans, bars, 'dev', cfg)
    gap = pd.Timestamp('2024-06-30 12:00')
    assert gap not in s.index and pd.Timestamp('2024-06-30 13:00') not in s.index      # r1 needs the missing close
    assert pd.isna(s.loc[pd.Timestamp('2024-06-30 11:00'), 'R1']) and ex['features_incomplete'] > 0


def test_hourly_windows_stop_at_cutoff():
    cfg = config.load()
    bars = _bars('2024-11-01', 24 * 75)
    trans = D.transform_hourly(_raw('2024-10-01', 24 * 110), cfg['hourly'])
    dev, _ = D.hourly_samples(trans, bars[bars.index <= '2024-12-31 23:00'], 'dev', cfg)
    assert dev['R24'].last_valid_index() == pd.Timestamp('2024-12-30 23:00')
    assert dev['R1'].last_valid_index() == pd.Timestamp('2024-12-31 22:00')
    hold, _ = D.hourly_samples(trans, bars, 'holdout', cfg)
    assert hold.index.min() >= pd.Timestamp('2025-01-01')


def _cm(start, n):
    idx = pd.date_range(start, periods=n, freq='D')
    rng = np.random.default_rng(3)
    df = pd.DataFrame({m: rng.gamma(5.0, 100.0, n) for m in config.load()['cm']['eth']}, index=idx)
    for a in ('usdt', 'usdc', 'dai'):
        df[a] = rng.gamma(5.0, 1e9, n)
    return df


def test_daily_lag_and_windows():
    cfg = config.load()
    cm = _cm('2024-06-01', 214)
    prices = {(date(2024, 6, 1) + timedelta(days=k)): 1000.0 + k for k in range(214)}
    volumes = {d: 1e9 for d in prices}
    v = D.cm_values(cm, prices)
    spike = cm.copy()
    spike.loc['2024-10-01', 'FlowInExNtv'] *= 50
    a, b = D.transform_daily(v, cfg['daily']), D.transform_daily(D.cm_values(spike, prices), cfg['daily'])
    assert a.loc['2024-10-01', 'cmf_in__z28'] == b.loc['2024-10-01', 'cmf_in__z28']
    assert a.loc['2024-10-02', 'cmf_in__z28'] != b.loc['2024-10-02', 'cmf_in__z28']
    assert len(a.columns) == 20
    s, _ = D.daily_samples(a, prices, volumes, 'dev', cfg)
    assert s['R7'].last_valid_index() == pd.Timestamp('2024-12-24')
    assert s['T1'].last_valid_index() == pd.Timestamp('2024-12-30')
