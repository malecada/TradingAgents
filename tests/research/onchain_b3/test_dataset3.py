from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b2 import dataset as DS2, periods
from tradingagents.research.onchain_b3 import config, dataset3 as D3


def test_value3_rules():
    assert D3.value3('f4_deg_gini', 0.4) == 0.4 and D3.value3('f4_transitivity', 0.1) == 0.1
    assert D3.value3('f4_components', np.e - 1) == pytest.approx(1.0) and D3.value3('f5_mean_3', 0.2) == 0.2
    assert D3.value3('f1_transfers', np.e - 1) == pytest.approx(1.0) and D3.value3('f3a_ex_net_value', -(np.e - 1)) == pytest.approx(-1.0)


def _market():
    d0 = date(2016, 12, 1)
    days = [d0 + timedelta(days=i) for i in range((periods.DEV_END - d0).days + 1)]
    rng = np.random.default_rng(0)
    p = dict(zip(days, 1000 * np.exp(np.cumsum(rng.normal(0, 0.02, len(days))))))
    return p, {d: 5e8 for d in days}


def _trans():
    rows = {w: {'f1_transfers': 1000.0 + i, 'f4_deg_gini': 0.3 + 0.01 * (i % 5), 'f5_mean_0': 0.1 + 0.001 * (i % 7)}
            for i, w in enumerate(periods.all_weeks())}
    return D3.transform3(DS2.raw_table(rows), 8, 6, 10.0)


def test_dev_four_week_targets_stop_at_cutoff():
    p, v = _market()
    df, _ = D3.weekly_samples3(_trans(), p, v, 'dev')
    assert len(df) == 378 and {'T2', 'T6', 'T7'} <= set(df.columns)
    last_ok = df[df['T6'].notna()].index.max()
    assert last_ok == pd.Timestamp('2024-12-02')                 # 2024-12-02 + 28 days = 2024-12-30
    assert df.loc[pd.Timestamp('2024-12-09'), ['T6', 'T7']].isna().all()
    assert pd.notna(df.loc[pd.Timestamp('2024-12-23'), 'T2'])          # 7-day targets still reach 2024-12-30


def test_columns3_from_config():
    p, v = _market()
    df, _ = D3.weekly_samples3(_trans(), p, v, 'dev')
    cfg = config.load()
    s5, s1 = set(D3.columns3(df, 'S5', cfg)), set(D3.columns3(df, 'S1', cfg))
    assert s5 - s1 == {c for c in df.columns if c.startswith('f4_')}
    assert all(c.startswith('f0_') for c in D3.columns3(df, 'S0', cfg))