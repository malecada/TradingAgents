# tests/research/onchain_b6/test_dataset6.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b5 import implied
from tradingagents.research.onchain_b6 import config, dataset6 as D

CFG = config.load()


def test_transform_raw_is_causal_and_named():
    idx = pd.date_range('2024-01-01', periods=1500, freq='h')
    raw = pd.DataFrame({'gs_active': np.random.default_rng(1).gamma(2, 3, 1500), 'tk_usdt_in': 1.0}, index=idx)
    a = D.transform_raw(raw, CFG['transforms'])
    b = D.transform_raw(raw.assign(gs_active=raw['gs_active'].where(raw.index < idx[1200], 99.0)), CFG['transforms'])
    pd.testing.assert_frame_equal(a.iloc[:1200], b.iloc[:1200])
    assert set(a.columns) == {'gs_active__h1z', 'gs_active__d24z', 'tk_usdt_in__h1z', 'tk_usdt_in__d24z'}
    assert (a['tk_usdt_in__h1z'].dropna() == 0).all()


def test_iv_hourly_min_trades_and_ffill_limit():
    ts0 = int(pd.Timestamp('2023-06-01', tz='UTC').timestamp() * 1000)
    rows = [(0.2, 50.0), (0.3, 52.0), (0.4, 54.0), (5.5, 60.0)]      # 3 trades in hour 0, one in hour 5
    df = implied.prepare(pd.DataFrame([{'timestamp': ts0 + int(h * 3.6e6), 'trade_id': str(i), 'instrument_name': 'ETH-2JUN23-1900-C',
                                        'iv': iv, 'price': 0.01, 'index_price': 1900.0, 'amount': 1.0, 'direction': 'buy'}
                                       for i, (h, iv) in enumerate(rows)]))
    s = D.iv_hourly(lambda d: df if d == '2023-06-01' else None, ['2023-06-01'], 3, 3, {'moneyness': 0.02, 'iv_min_ahead_h': 2})
    h = lambda k: pd.Timestamp('2023-06-01') + pd.Timedelta(hours=k)
    assert np.isclose(s[h(0)], np.log(0.52)) and np.isclose(s[h(3)], np.log(0.52)) and np.isnan(s.get(h(4), np.nan))
    assert h(5) not in s.dropna().index                                  # one trade: ineligible, not filled


def test_samples_windows_and_targets():
    idx = pd.date_range('2021-01-01', periods=24 * 400, freq='h')
    rng = np.random.default_rng(2)
    bars = pd.DataFrame({'close': 1000 * np.exp(np.cumsum(rng.normal(0, 0.004, len(idx)))), 'qvol': rng.gamma(2.0, 1e6, len(idx))}, index=idx)
    feats = pd.DataFrame({'gs_active__h1z': rng.normal(size=len(idx)), 'eth_in_val__h1z': rng.normal(size=len(idx)),
                          'mk_iv': rng.normal(size=len(idx))}, index=idx)
    cfg = {**CFG, 'tracks': {'B': {**CFG['tracks']['B'], 'start': '2021-04-01', 'end': '2022-01-31'}}}
    s = D.samples('B', feats, bars, cfg)
    assert s.index.min() >= pd.Timestamp('2021-04-01') and s['V24'].last_valid_index() == pd.Timestamp('2022-01-30 23:00')
    assert s['V6'].last_valid_index() == pd.Timestamp('2022-01-31 17:00') and {'V6', 'V24', 'h0_r1', 'px_rv6'} <= set(s.columns)
