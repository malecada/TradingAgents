# tradingagents/research/onchain_b4/flows.py
"""One day of admitted transfers -> 24 hourly rows (spec §4.3). Inflow = non-exchange to exchange,
outflow = exchange to non-exchange; transfers inside the exchange set are excluded. The same flows
are computed with labels only (`lab_` prefix) for exploration."""
from __future__ import annotations

import numpy as np
import pandas as pd

FLOW = ['eth_in_val', 'eth_out_val', 'eth_in_cnt', 'eth_out_cnt', 'eth_big_in',
        'stable_in_val', 'stable_out_val', 'stable_in_cnt', 'stable_out_cnt', 'stable_big_in']
SERIES = FLOW + ['act_gas_price', 'act_gas_used', 'act_tx_count', 'act_eth_transfers', 'act_eth_value']
LAB = ['lab_' + s for s in FLOW]


def _hours(ts, start):
    return ((np.asarray(ts, np.int64) - start) // 3600).astype(np.int64)


def _count(idx):
    return np.bincount(idx, minlength=24).astype(float)


def hourly(day, d, is_ex, is_lab, cfg_flows):
    start = int(pd.Timestamp(day).timestamp())
    hr = _hours(d.ts, start)
    out = {}
    for prefix, ex in (('', is_ex), ('lab_', is_lab)):
        se, de = ex(d.src), ex(d.dst)
        inflow, outflow = ~se & de, se & ~de
        for code, name, big in ((0, 'eth', cfg_flows['large_eth']), (1, 'stable', cfg_flows['large_usd'])):
            a = d.asset == code
            i, o = inflow & a, outflow & a
            out[f'{prefix}{name}_in_val'] = np.bincount(hr[i], weights=d.amount[i], minlength=24)
            out[f'{prefix}{name}_out_val'] = np.bincount(hr[o], weights=d.amount[o], minlength=24)
            out[f'{prefix}{name}_in_cnt'] = _count(hr[i])
            out[f'{prefix}{name}_out_cnt'] = _count(hr[o])
            out[f'{prefix}{name}_big_in'] = _count(hr[i & (d.amount >= big)])
    eth = d.asset == 0
    out['act_eth_transfers'] = _count(hr[eth])
    out['act_eth_value'] = np.bincount(hr[eth], weights=d.amount[eth], minlength=24)
    th = _hours(d.tx_ts, start)
    gas = []
    for k in range(24):
        v = d.tx_gwei[(th == k) & ~np.isnan(d.tx_gwei)]
        gas.append(float(np.median(v)) if len(v) else 0.0)
    out['act_gas_price'] = np.array(gas)
    bh = _hours(d.blk_ts, start)
    out['act_gas_used'] = np.bincount(bh, weights=d.blk_gas, minlength=24)
    out['act_tx_count'] = np.bincount(bh, weights=d.blk_txs, minlength=24)
    return pd.DataFrame(out, index=pd.date_range(day, periods=24, freq='h'))[SERIES + LAB]
