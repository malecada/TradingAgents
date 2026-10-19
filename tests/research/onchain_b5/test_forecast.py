# tests/research/onchain_b5/test_forecast.py
import copy

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b5 import config, forecast


def _table(rng):
    idx = pd.date_range('2021-04-01 02:00', '2026-10-12', freq='D')
    n = len(idx)
    df = pd.DataFrame({'h0_r1': rng.normal(size=n), 'px_abs_r1': rng.normal(size=n), 'mk_dvol': rng.normal(size=n),
                       'mk_iv': rng.normal(size=n), 'eth_x__h1z': rng.normal(size=n), 'stable_x__h1z': rng.normal(size=n)},
                      index=idx)
    df['y'] = 0.8 * df['mk_iv'] + 1.5 * df['stable_x__h1z'] + 0.3 * rng.normal(size=n)
    df['tau_h'] = 6.0
    return df


def test_forecast_comparisons_groups_and_signal():
    cfg = copy.deepcopy(config.load())
    cfg['families'] = ['linear']
    preds, res = forecast.run(_table(np.random.default_rng(3)), cfg)
    assert list(preds.columns) == ['linear:M0', 'linear:M1', 'linear:M2', 'linear:IV']
    assert preds.loc[:'2021-12-31'].isna().all().all() and preds.loc['2022-01-01':].notna().all().all()
    assert len(res) == 3 * 2
    get = {(r['set'], r['comparator'], r['group']): r for r in res}
    assert get[('M2', 'M1', '2022-24')]['hi'] < 0 and get[('M2', 'IV', '2025-26')]['hi'] < 0
    assert get[('M1', 'M0', '2022-24')]['hi'] < 0
    assert set(get[('M2', 'M1', '2022-24')]['years']) == {2022, 2023, 2024}
