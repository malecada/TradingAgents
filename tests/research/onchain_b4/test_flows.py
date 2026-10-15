# tests/research/onchain_b4/test_flows.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b4 import flows
from tradingagents.research.onchain_b4.entities import member
from tradingagents.research.onchain_b4.reader import Day

U, X, Q, L = 1, 2, 3, 100           # user, known deposit, new deposit, label
T0 = int(pd.Timestamp('2025-06-02').timestamp())
h = lambda k: T0 + 3600 * k + 5


def _day():
    rows = [(U, X, 0, 150.0, 3), (X, L, 0, 150.0, 4), (L, X, 0, 0.01, 4), (L, U, 0, 2.0, 5),
            (U, L, 1, 2e6, 6), (U, Q, 0, 1.0, 1), (Q, L, 0, 1.0, 2)]
    a = np.array(rows, dtype=object)
    return Day(src=np.array(a[:, 0], np.uint64), dst=np.array(a[:, 1], np.uint64), asset=np.array(a[:, 2], np.int8),
               amount=np.array(a[:, 3], float), ts=np.array([h(k) for k in a[:, 4]], np.int64),
               block=np.arange(len(rows), dtype=np.int64),
               tx_ts=np.array([h(0), h(0), h(0), h(7)], np.int64), tx_gwei=np.array([1.0, 3.0, np.nan, 9.0]),
               blk_ts=np.array([h(0), h(0)], np.int64), blk_gas=np.array([10.0, 20.0]), blk_txs=np.array([2.0, 3.0]))


def test_hourly_flows_entities_and_labels_only():
    ex = lambda k: member(np.array([X, L], np.uint64), k)
    lab = lambda k: member(np.array([L], np.uint64), k)
    r = flows.hourly('2025-06-02', _day(), ex, lab, {'large_eth': 100.0, 'large_usd': 1e6})
    assert len(r) == 24 and list(r.columns) == flows.SERIES + flows.LAB and r.index[0] == pd.Timestamp('2025-06-02')
    r = r.reset_index(drop=True)
    assert r['eth_in_val'][3] == 150.0 and r['eth_big_in'][3] == 1 and r['eth_in_val'][4] == 0.0     # sweep internal
    assert r['eth_out_val'][4] == 0.0 and r['eth_out_val'][5] == 2.0                                   # top-up internal
    assert r['eth_in_val'][1] == 0.0 and r['eth_in_val'][2] == 1.0                                     # new deposit: once, at sweep
    assert r['stable_in_val'][6] == 2e6 and r['stable_big_in'][6] == 1 and r['stable_in_cnt'][6] == 1
    assert r['lab_eth_in_val'][3] == 0.0 and r['lab_eth_in_val'][4] == 150.0 and r['lab_eth_out_cnt'][4] == 1
    assert r['act_gas_price'][0] == 2.0 and r['act_gas_price'][7] == 9.0 and r['act_gas_price'][1] == 0.0
    assert r['act_gas_used'][0] == 30.0 and r['act_tx_count'][0] == 5.0
    assert r['act_eth_transfers'].sum() == 6 and r['act_eth_value'][3] == 150.0
