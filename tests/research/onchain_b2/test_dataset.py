import math
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b2 import dataset as DS
from tradingagents.research.onchain_b2 import periods


def test_transform_is_causal_and_correct():
    weeks = [f'w{i:02d}' for i in range(12)]
    raw = pd.DataFrame({'f2_mean_0': np.arange(1.0, 13.0)}, index=weeks)
    t = DS.transform(raw)
    assert math.isnan(t.loc['w05', 'f2_mean_0__z8'])                         # only 5 previous values
    assert t.loc['w06', 'f2_mean_0__z8'] == pytest.approx((7 - 3.5) / np.std(np.arange(1.0, 7.0)))
    assert t.loc['w08', 'f2_mean_0__z8'] == pytest.approx((9 - 4.5) / np.std(np.arange(1.0, 9.0)))
    assert t.loc['w08', 'f2_mean_0__d1'] == pytest.approx(1.0)
    raw2 = raw.copy()
    raw2.loc['w09', 'f2_mean_0'] = 1000.0
    assert DS.transform(raw2).loc['w08', 'f2_mean_0__z8'] == t.loc['w08', 'f2_mean_0__z8']   # no future leak


def test_value_transforms():
    raw = pd.DataFrame({'f1_transfers': [np.e - 1] * 10, 'f3a_ex_net_value': [-(np.e - 1)] * 10,
                        'f1_top_share': [0.5] * 10}, index=[f'w{i}' for i in range(10)])
    t = DS.transform(raw)
    assert t['f1_transfers__z8'].iloc[-1] == 0.0                              # constant series → zero std → 0
    assert DS._value('f1_transfers', np.e - 1) == pytest.approx(1.0)
    assert DS._value('f3a_ex_net_value', -(np.e - 1)) == pytest.approx(-1.0)
    assert DS._value('f1_top_share', 0.5) == 0.5 and DS._value('f3b_ex_n', np.e - 1) == pytest.approx(1.0)


def _market():
    d0 = date(2016, 12, 1)
    days = [d0 + timedelta(days=i) for i in range((date(2025, 1, 31) - d0).days)]
    rng = np.random.default_rng(0)
    p = dict(zip(days, 1000 * np.exp(np.cumsum(rng.normal(0, 0.02, len(days))))))
    v = dict(zip(days, np.full(len(days), 5e8)))
    return {d: x for d, x in p.items() if d <= periods.DEV_END}, {d: x for d, x in v.items() if d <= periods.DEV_END}


def _trans(missing=()):
    weeks = periods.all_weeks()
    rows = {w: (None if w in missing else {'f1_transfers': 1000.0 + i, 'f2_mean_0': 0.1 + 0.001 * (i % 7)})
            for i, w in enumerate(weeks)}
    return DS.transform(DS.raw_table(rows))


def test_weekly_dev_samples():
    p, v = _market()
    df, excluded = DS.weekly_samples(_trans(), p, v, 'dev')
    assert len(df) + len(excluded) == 378 and df.index.min() >= pd.Timestamp('2017-10-02')
    assert df.index.max() <= pd.Timestamp('2024-12-23') and {'T2', 'T3', 'T4', 'T5', 'f0_r1'} <= set(df.columns)
    assert DS.columns(df, 'S0') == sorted(c for c in df.columns if c.startswith('f0_'))
    assert set(DS.columns(df, 'S3')) == set(DS.columns(df, 'S1')) | {c for c in df.columns if c.startswith('f2_')}


def test_unavailable_week_excluded_with_reason():
    p, v = _market()
    df, excluded = DS.weekly_samples(_trans(missing={'2020-03-02'}), p, v, 'dev')
    assert (pd.Timestamp('2020-03-09') not in df.index) and ('2020-03-09', 'week_unavailable') in excluded


def test_daily_samples_use_latest_completed_week():
    p, v = _market()
    df, _ = DS.daily_samples(_trans(), p, v, 'dev')
    assert 'T1' in df.columns and df.index.max() == pd.Timestamp('2024-12-30')
    row = df.loc[pd.Timestamp('2020-03-08')]
    assert row['week'] == '2020-02-24'                                        # week 2020-03-02 not finished on 03-08

def test_z_scores_are_clipped():
    vals = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0 + 1e-9, 5.0]
    raw = pd.DataFrame({'f2_mean_0': vals}, index=[f'w{i}' for i in range(len(vals))])
    assert DS.transform(raw).iloc[-1]['f2_mean_0__z8'] == 10.0
