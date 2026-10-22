# tests/research/onchain_b8/test_reader8.py
import numpy as np
import pandas as pd
import pyarrow as pa
import pytest

from tradingagents.research.onchain_b2.s3source import DayUnavailable
from tradingagents.research.onchain_b4.reader import ZERO, addr_keys
from tradingagents.research.onchain_b8 import reader8 as R

A, B, C = ('0x' + ch * 40 for ch in 'abc')
TOK1, TOK2, TOK9 = ('0x' + ch * 40 for ch in '129')


def _table(day='2023-05-01'):
    t0 = pd.Timestamp(day, tz='UTC')
    rows = [(TOK1, A, B, 5e18, 1), (TOK1.upper(), B, C, 2e18, 2), (TOK2, A, C, 7e6, 3), (TOK9, A, B, 1e18, 4),
            (TOK1, A, A, 1e18, 5), (TOK1, ZERO, A, 1e18, 6), (TOK1, A, B, 0.0, 7)]
    return pa.table({'token_address': [r[0] for r in rows], 'from_address': [r[1] for r in rows], 'to_address': [r[2] for r in rows],
                     'value': pa.array([r[3] for r in rows], pa.float64()), 'block_number': [r[4] for r in rows],
                     'block_timestamp': pa.array([(t0 + pd.Timedelta(minutes=r[4])).to_datetime64() for r in rows], pa.timestamp('ns'))})


def test_admit8_filters_scales_and_indexes():
    d = R.admit8(_table(), {TOK1: (0, 18), TOK2: (1, 6)})
    assert d.rows == {'transfers': 3} and d.token.tolist() == [0, 0, 1] and d.token.dtype == np.int16
    assert np.allclose(d.amount, [5.0, 2.0, 7.0])
    ka, kb, kc = addr_keys(np.array([A, B, C], object))
    assert d.src.tolist() == [ka, kb, ka] and d.dst.tolist() == [kb, kc, kc]
    assert d.ts.tolist() == [int(pd.Timestamp('2023-05-01 00:01', tz='UTC').timestamp()) + 60 * k for k in (0, 1, 2)]


def test_read_day8_retries_then_unavailable(monkeypatch):
    calls = []

    def fake_read(filesystem, root, table, day):
        calls.append(table)
        if len(calls) < 3 or day == '2023-05-02':
            raise OSError('timeout')
        return _table(day)
    monkeypatch.setattr(R, '_read_table', fake_read)
    d = R.read_day8('2023-05-01', filesystem=None, root='r', contracts={TOK1: (0, 18)}, retries=[0, 0], sleep=lambda s: None)
    assert d.rows['transfers'] == 2 and calls == ['token_transfers'] * 3
    with pytest.raises(DayUnavailable):
        R.read_day8('2023-05-02', filesystem=None, root='r', contracts={TOK1: (0, 18)}, retries=[0], sleep=lambda s: None)
