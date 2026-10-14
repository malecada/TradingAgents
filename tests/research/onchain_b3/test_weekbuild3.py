import math
from datetime import date, timedelta

import numpy as np
import pyarrow as pa
import pytest

from tradingagents.research.onchain_b.weekly import admitted_events
from tradingagents.research.onchain_b3 import config, targets3 as T3, weekbuild3 as WB

A, B, C, E = ('0x' + c * 40 for c in 'abce')
EX = pa.array([E])
EXB = np.array([E], dtype='S42')


def _day(rows):
    return pa.table({'hash': ['0x' + f'{i:064x}' for i in range(len(rows))],
                     'block_timestamp': pa.array([0] * len(rows), pa.timestamp('ns')),
                     'from_address': [r[0] for r in rows], 'to_address': [r[1] for r in rows],
                     'value': [r[2] * 1e18 for r in rows], 'receipt_status': [1] * len(rows)})


def test_build_week3_outputs():
    cfg = {**config.load(), 'k': 3}
    ev, c = admitted_events(_day([(A, B, 1.0), (B, C, 2.0), (C, A, 1.5), (A, E, 4.0), (B, A, 0.5)]))
    summary, graph, keys = WB.build_week3('2019-06-03', [ev], [c], EX, EXB, cfg, week_index=127)
    assert summary['f1']['f1_transfers'] == 5 and summary['f3a']['f3a_ex_in_value'] == pytest.approx(4.0)
    assert len([k for k in summary['f4'] if k.startswith('f4_')]) == 26
    assert summary['f4']['f4_components'] == 1 and summary['f4']['f4_recip_edge_share'] == pytest.approx(2 / 5)
    assert graph.n == 3 and keys.dtype == np.uint64 and len(keys) == 4


def _px(f, n=90):
    d0 = date(2020, 1, 1)
    return {d0 + timedelta(days=i): f(i) for i in range(n)}


def test_four_week_targets():
    p = _px(lambda i: 100.0 * 1.01 ** i)
    m = date(2020, 1, 10)
    assert T3.t6(p, m) == pytest.approx(28 * math.log(1.01))
    q = _px(lambda i: 100.0 * (1.02 if i % 2 else 1.0))
    assert T3.t7(q, m) == pytest.approx(math.log(math.sqrt(28) * math.log(1.02)))
    assert T3.t6(p, date(2020, 3, 10)) is None                     # +28 days = 2020-04-07, beyond the 90-day series