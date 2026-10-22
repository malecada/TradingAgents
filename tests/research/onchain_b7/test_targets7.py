# tests/research/onchain_b7/test_targets7.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b7 import config, targets7 as T

CFG = config.load()
H = pd.Timedelta(hours=1)


def _minutes(start, hours, rng):
    idx = pd.date_range(start, periods=60 * hours, freq='min')
    return pd.Series(100.0 * np.exp(np.cumsum(rng.normal(0, 1e-4, len(idx)))), index=idx)


def test_range_features_require_minutes():
    rng = np.random.default_rng(3)
    m = _minutes('2024-01-01', 48, rng)
    h = pd.Timestamp('2024-01-01 05:00')
    m.loc[h:h + pd.Timedelta(minutes=59)] = 100.0
    m.loc[h + pd.Timedelta(minutes=30)] = 110.0                              # one hour with a known 10 % range
    m = m.drop(m.loc[h + 2 * H:h + 2 * H + pd.Timedelta(minutes=40)].index)   # an outage of 41 minutes
    idx = pd.date_range('2024-01-01', periods=48, freq='h')
    f = T.range_features(m, idx, CFG['range'])
    assert np.isclose(f.loc[h, 'rg_range1'], np.log(1.1)) and np.isnan(f.loc[h + 2 * H, 'rg_range1'])
    assert np.isfinite(f['rg_range1'].drop(h + 2 * H)).all() and (f['rg_range1'].dropna() >= 0).all()
    assert f['rg_range24'].iloc[:31].isna().all() and np.isfinite(f.loc[idx[31], 'rg_range24'])   # warm-up, then the outage hour inside the window


def test_jump_targets_threshold_and_warmup():
    idx = pd.date_range('2023-01-01', periods=2000, freq='h')
    r = 0.01 * np.where(np.arange(len(idx)) % 2 == 0, 1.0, -1.0)            # alternating ±1 %: σ̂ = 1 %, multi-hour moves cancel
    r[1500] = 0.2                                                            # one 20 % hour
    bars = pd.DataFrame({'close': 1000 * np.exp(np.cumsum(r)), 'qvol': 1.0}, index=idx)
    j = T.jump_targets(bars, CFG['jump'])
    assert j['J6'].iloc[:CFG['jump']['sigma_min']].isna().all()               # σ̂ unavailable → NaN, not 0
    assert j['J6'].iloc[1494:1500].eq(1.0).all() and j['J6'].iloc[1500:1510].eq(0.0).all()
    assert j['J24'].iloc[1476:1500].eq(1.0).all() and j['J24'].iloc[1400:1476].eq(0.0).all()
    assert j['J6'].iloc[-6:].isna().all() and j['J24'].iloc[-24:].isna().all()
    assert j['J6'].iloc[600:1400].eq(0.0).all() and j['J24'].iloc[600:1400].eq(0.0).all()


def test_mmax_alignment_and_missing():
    rng = np.random.default_rng(5)
    m = _minutes('2024-01-01', 72, rng)
    jump_min = pd.Timestamp('2024-01-02 03:17')
    m.loc[jump_min:] *= 1.05                                                 # a 5 % step at minute 03:17 of day 2
    idx = pd.date_range('2024-01-01', periods=72, freq='h')
    t = T.mmax_targets(m, idx, CFG['mmax'])
    big = t['M6'] > np.log(0.045)
    first_hour = pd.Timestamp('2024-01-01 21:00')                            # next 6 h = 22:00 … 03:59 of day 2
    last_hour = pd.Timestamp('2024-01-02 02:00')                             # next 6 h = 03:00 … 08:59
    assert big.loc[first_hour] and big.loc[last_hour] and not big.loc[first_hour - H] and not big.loc[last_hour + H]
    assert (t['M24'] > np.log(0.045)).loc[pd.Timestamp('2024-01-01 04:00'):pd.Timestamp('2024-01-02 02:00')].all()
    assert t['M6'].iloc[-6:].isna().all() and np.isfinite(t['M6'].iloc[-7])
    gap = m.drop(m.loc[pd.Timestamp('2024-01-01 10:00'):pd.Timestamp('2024-01-01 10:30')].index)   # 31 missing minutes
    g = T.mmax_targets(gap, idx, CFG['mmax'])
    assert np.isnan(g.loc[pd.Timestamp('2024-01-01 05:00'), 'M6']) and np.isfinite(g.loc[pd.Timestamp('2024-01-01 05:00'), 'M24'])
