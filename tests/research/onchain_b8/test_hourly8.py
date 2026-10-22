# tests/research/onchain_b8/test_hourly8.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b4.reader import addr_keys
from tradingagents.research.onchain_b6.labels6 import LabelState
from tradingagents.research.onchain_b8 import config, hourly8 as Hh
from tradingagents.research.onchain_b8.reader8 import Day8

A, B, X, Y, Z = ('0x' + ch * 40 for ch in 'abxyc')


def _state(first_seen):
    doc = {'exchange': {X: 'okx', Y: 'binance', Z: 'bybit'}, 'dex': [], 'bridge': [], 'mev': [], 'funds': []}
    st = LabelState(doc, '0x5754284f345afc66a98fbb0a0afe71e0f007b949')
    keys = addr_keys(np.array([X, Y, Z], object))
    for k, day in zip(keys, first_seen):
        st.ex_first[np.searchsorted(st.ex_keys, k)] = day
    return st


def test_day_rows_flows_activation_and_prices():
    day = '2023-05-01'
    t0 = int(pd.Timestamp(day, tz='UTC').timestamp())
    ka, kb, kx, ky, kz = addr_keys(np.array([A, B, X, Y, Z], object))
    #            A->X dep   X->B wd    X->Y ex-ex   A->B plain  B->Z (Z seen today: not an exchange)  A->X tok1 no price
    src = np.array([ka, kx, kx, ka, kb, ka], np.uint64)
    dst = np.array([kx, kb, ky, kb, kz, kx], np.uint64)
    d = Day8(src=src, dst=dst, token=np.array([0, 0, 0, 0, 0, 1], np.int16), amount=np.array([10.0, 4.0, 100.0, 1.0, 50.0, 3.0]),
             ts=np.array([t0 + 60, t0 + 120, t0 + 3700, t0 + 3800, t0 + 7300, t0 + 60], np.int64))
    st = _state([config.day_ord('2023-01-01'), config.day_ord('2023-01-01'), config.day_ord(day)])
    st.begin_day(config.day_ord(day))
    prices = np.full((24, 2), np.nan)
    prices[:, 0] = 2.0                                                          # token 0 priced at 2 all day; token 1 unpriced
    rows = Hh.day_rows(day, d, st, prices, big_usd=15.0)
    assert len(rows) == 48 and list(rows.columns) == ['hour', 'token'] + Hh.SERIES
    r = rows.set_index(['hour', 'token'])
    h = lambda k: pd.Timestamp(day) + pd.Timedelta(hours=k)
    assert r.loc[(h(0), 0), 'dep_usd'] == 20.0 and r.loc[(h(0), 0), 'wd_usd'] == 8.0
    assert r.loc[(h(0), 0), 'dep_cnt'] == 1 and r.loc[(h(0), 0), 'wd_cnt'] == 1 and r.loc[(h(0), 0), 'tx_cnt'] == 2
    assert r.loc[(h(0), 0), 'active'] == 3 and r.loc[(h(0), 0), 'big_cnt'] == 1    # A, X, B; only the $20 deposit is big
    assert r.loc[(h(1), 0), 'dep_usd'] == 0.0 and r.loc[(h(1), 0), 'wd_usd'] == 0.0 and r.loc[(h(1), 0), 'tx_cnt'] == 2   # ex→ex and plain
    assert r.loc[(h(2), 0), 'dep_usd'] == 0.0 and r.loc[(h(2), 0), 'tx_cnt'] == 1   # Z first seen today: not yet an exchange
    assert np.isnan(r.loc[(h(0), 1), 'dep_usd']) and r.loc[(h(0), 1), 'dep_cnt'] == 1 and r.loc[(h(0), 1), 'big_cnt'] == 0
    assert np.isnan(r.loc[(h(5), 1), 'dep_usd']) and r.loc[(h(5), 1), 'tx_cnt'] == 0 and r.loc[(h(5), 0), 'dep_usd'] == 0.0
    st.begin_day(config.day_ord('2023-05-02'))
    rows2 = Hh.day_rows('2023-05-02', Day8(src=src[4:5], dst=dst[4:5], token=np.array([0], np.int16), amount=np.array([50.0]),
                                          ts=np.array([t0 + 86400 + 10], np.int64)), st, prices, big_usd=15.0)
    assert rows2.set_index(['hour', 'token']).loc[(pd.Timestamp('2023-05-02'), 0), 'dep_usd'] == 100.0   # active from the next day


def test_price_matrix_aligns_tokens_and_hours():
    hours = pd.date_range('2023-05-01', periods=48, freq='h')
    b0 = pd.DataFrame({'close': np.arange(1, 25, dtype=float), 'qvol': 1.0}, index=pd.date_range('2023-05-01', periods=24, freq='h'))
    b1 = pd.DataFrame({'close': [7.0, 8.0], 'qvol': 1.0}, index=pd.DatetimeIndex(['2023-05-02 03:00', '2023-05-02 05:00']))
    m = Hh.price_matrix([b0, b1], hours)
    assert m.shape == (48, 2) and m[0, 0] == 1.0 and m[23, 0] == 24.0 and np.isnan(m[24, 0])
    assert np.isnan(m[26, 1]) and m[27, 1] == 7.0 and np.isnan(m[28, 1]) and m[29, 1] == 8.0
