# tests/research/onchain_b6/test_hourly6.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b3.history import Bloom
from tradingagents.research.onchain_b4.reader import addr_keys
from tradingagents.research.onchain_b6 import config, hourly6, labels6
from tradingagents.research.onchain_b6.reader6 import Day6

CFG = config.load()
A, B, C, X, Y, R, M, T = ('0x' + c * 40 for c in 'abcdef12')     # hex letters only: keys use the first 16 hex digits
TREAS = CFG['issuer']['usdt_treasury']
K = {n: int(addr_keys(np.array([a], object))[0]) for n, a in {'A': A, 'B': B, 'C': C, 'X': X, 'Y': Y, 'R': R, 'M': M, 'T': TREAS}.items()}


def _state(day_ord=100):
    doc = {'exchange': {X: 'okx', Y: 'kraken'}, 'dex': [R], 'bridge': [], 'mev': [M], 'funds': [], 'issuer': {'usdt_treasury': TREAS}}
    st = labels6.LabelState(doc, TREAS)
    st.observe(np.array([K['X'], K['Y'], K['R'], K['M']], np.uint64), day_ord - 1)
    st.begin_day(day_ord)
    return st


def _day(rows, day='2023-06-01'):
    T0 = int(pd.Timestamp(day, tz='UTC').timestamp())
    a = np.array(rows, dtype=object)
    return Day6(src=np.array(a[:, 0], np.uint64), dst=np.array(a[:, 1], np.uint64), token=np.array(a[:, 2], np.int8),
                amount=np.array(a[:, 3], float), ts=np.array([T0 + 3600 * int(h) + 7 for h in a[:, 4]], np.int64),
                mint=np.array(a[:, 5], bool), burn=np.array(a[:, 6], bool))


def test_day_rows_flows_issuance_large_and_bloom():
    rows = [(K['A'], K['X'], 1, 2e6, 0, 0, 0),       # USDT deposit 2M -> large, tk_usdt_in
            (K['X'], K['B'], 2, 5e5, 0, 0, 0),        # USDC withdrawal
            (K['A'], K['R'], 0, 3.0, 0, 0, 0),        # ETH into DEX
            (K['M'], K['C'], 1, 100.0, 0, 0, 0),      # stable out of MEV
            (0, K['A'], 2, 7e6, 1, 1, 0),             # USDC mint (hour 1)
            (K['B'], 0, 3, 1e6, 1, 0, 1),             # DAI burn
            (K['T'], K['X'], 1, 3e7, 1, 0, 0),        # treasury out, also a deposit of 30M (treasury is not an exchange)
            (K['A'], K['X'], 0, 600.0, 2, 0, 0),      # ETH deposit 600 -> large
            (K['X'], K['Y'], 1, 50.0, 2, 0, 0)]       # cross-entity exchange transfer
    st, bloom = _state(), Bloom(16, 3)
    bloom.add(np.array([K['A']], np.uint64))
    h, large = hourly6.day_rows('2023-06-01', _day(rows), st, bloom, CFG)
    assert len(h) == 24 and list(h.columns) == hourly6.COLUMNS
    assert h['tk_usdt_in'].iloc[0] == 2e6 and h['tk_usdc_out'].iloc[0] == 5e5
    assert h['cl_dex_eth_in'].iloc[0] == 3.0 and h['cl_mev_stable_out'].iloc[0] == 100.0
    assert h['is_usdc_mint'].iloc[1] == 7e6 and h['is_dai_burn'].iloc[1] == 1e6 and h['is_usdt_treasury_out'].iloc[1] == 3e7
    assert h['tk_usdt_in'].iloc[1] == 3e7 and h['gs_cex_cex_usd'].iloc[2] == 50.0
    assert h['gs_active'].iloc[1] == 2.0                                   # mint/burn rows are not graph edges
    assert sorted(zip(large['direction'], large['amount'])) == [(1, 600.0), (1, 2e6), (1, 3e7)]
    assert large['entity'].tolist() == [st.entity_names.index('okx')] * 3 and large['cp_new'].tolist()[0] == False
    assert h['gs_new_share'].iloc[0] > 0 and bloom.contains(np.array([K['B']], np.uint64)).all()


def test_mint_burn_only_in_issuance():
    st, bloom = _state(), Bloom(16, 3)
    h, large = hourly6.day_rows('2023-06-01', _day([(0, K['X'], 2, 9e6, 0, 1, 0), (K['X'], 0, 2, 9e6, 0, 0, 1)]), st, bloom, CFG)
    assert h['is_usdc_mint'].iloc[0] == 9e6 and h['is_usdc_burn'].iloc[0] == 9e6
    assert h['tk_usdc_in'].iloc[0] == 0.0 and h['tk_usdc_out'].iloc[0] == 0.0 and h['gs_active'].iloc[0] == 0.0 and len(large) == 0


def test_observe_marks_first_seen_labels():
    doc = {'exchange': {X: 'okx'}, 'dex': [], 'bridge': [], 'mev': [], 'funds': [], 'issuer': {'usdt_treasury': TREAS}}
    st = labels6.LabelState(doc, TREAS)
    st.begin_day(5)
    h, _ = hourly6.day_rows('2017-01-06', _day([(K['A'], K['X'], 1, 5e6, 0, 0, 0)], '2017-01-06'), st, Bloom(16, 3), CFG)
    assert h['tk_usdt_in'].iloc[0] == 0.0                                  # not active on its first day
    assert st.ex_first[0] == 5
