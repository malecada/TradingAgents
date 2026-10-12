import numpy as np
import pyarrow as pa
import pytest

from tradingagents.research.onchain_b import weekly as W

A, B, C, D = ('0x' + c * 40 for c in 'abcd')


def _day(rows):
    return pa.table({'hash': ['0x' + f'{i:064x}' for i, _ in enumerate(rows)],
                     'block_timestamp': pa.array([0] * len(rows), pa.timestamp('ns')),
                     'from_address': [r[0] for r in rows], 'to_address': [r[1] for r in rows],
                     'value': [r[2] for r in rows], 'receipt_status': [r[3] for r in rows]})


def test_admission_filters_and_counters():
    t = _day([(A, B, 3e18, 1), (A, B, 2e18, 1), (B, C, 1e18, 0), (A, None, 1e18, 1), (C, A, 0.0, 1), (A, A, 1e18, 1)])
    events, counters = W.admitted_events(t)
    assert events.num_rows == 3
    assert counters == {'rows': 6, 'admitted': 3, 'failed': 1, 'null_recipient': 1, 'zero_value': 1}


def test_duplicate_hash_rejected():
    t = _day([(A, B, 1e18, 1), (A, B, 1e18, 1)])
    t = t.set_column(0, 'hash', pa.array(['0x' + '1' * 64] * 2))
    with pytest.raises(ValueError, match='duplicate'):
        W.admitted_events(t)


def test_aggregation_and_subgraph():
    ev1, _ = W.admitted_events(_day([(A, B, 3e18, 1), (A, B, 2e18, 1), (A, A, 1e18, 1)]))
    ev2, _ = W.admitted_events(_day([(B, C, 1e18, 1), (D, C, 1e18, 1)]))
    pairs = W.aggregate_pairs([ev1, ev2])
    rows = {(r['src'], r['dst']): (r['count'], r['value_eth']) for r in pairs.to_pylist()}
    assert rows[(A, B)] == (2, 5.0) and rows[(A, A)] == (1, 1.0) and rows[(B, C)] == (1, 1.0)
    # activity: A = out 3 + in 1 = 4, B = in 2 + out 1 = 3, C = in 2, D = out 1 → top-3 = A, B, C
    g = W.top_k_subgraph(pairs, 3, '2022-01-03')
    assert list(g.addresses.astype(str)) == sorted([A, B, C])
    e = {(int(s), int(d)) for s, d in g.edge_index.T}
    assert e == {(0, 1), (0, 0), (1, 2)}
    assert g.summary['k_effective'] == 3 and g.summary['full_nodes'] == 4
    # node features recomputed on induced graph: B has in_count 2 (A→B count 2), out_count 1
    xb = g.x[1]
    assert np.isclose(xb[0], np.log1p(2)) and np.isclose(xb[1], np.log1p(1))


def test_fewer_than_k_nodes():
    ev, _ = W.admitted_events(_day([(A, B, 1e18, 1)]))
    g = W.top_k_subgraph(W.aggregate_pairs([ev]), 50, '2022-01-03')
    assert g.summary['k_effective'] == 2 and g.x.shape == (2, 4)


def test_save_load_roundtrip(tmp_path):
    ev, _ = W.admitted_events(_day([(A, B, 1e18, 1), (B, A, 2e18, 1)]))
    g = W.top_k_subgraph(W.aggregate_pairs([ev]), 2, '2022-01-03')
    W.save(g, tmp_path / 'w')
    h = W.load(tmp_path / 'w')
    assert (h.addresses == g.addresses).all() and np.array_equal(h.edge_index, g.edge_index) and h.summary == g.summary
