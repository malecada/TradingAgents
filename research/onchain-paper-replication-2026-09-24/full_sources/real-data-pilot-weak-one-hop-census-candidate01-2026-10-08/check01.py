"""Only synthetic arrays; no repository scientific imports or actual graph IO."""
import json

import numpy as np

from weak_one_hop_census import census


def verify(edges, n, chunk=2):
    before = edges.copy()
    expected = [{i} for i in range(n)]
    for u, v in edges.T:
        expected[int(u)].add(int(v))
        expected[int(v)].add(int(u))
    expected = [len(nodes) for nodes in expected]
    result = census(edges, n, max_work_bytes=10_000_000, chunk_edges=chunk)
    assert result['cardinalities'].tolist() == expected
    assert np.array_equal(edges, before)
    assert result['minimum_cardinality'] == min(expected)
    assert result['maximum_cardinality'] == max(expected)
    assert result['maximum_center_index'] == expected.index(max(expected))
    assert result['centers_above_declared_threshold'] == sum(x > 10000 for x in expected)
    return result


edges = np.array([[0, 1, 0, 0, 2, 2, 3, 3, 3],
                  [1, 0, 1, 0, 1, 2, 4, 4, 3]], dtype=np.int64)
for dtype in (np.int8, np.int64, np.uint64):
    for chunk in (1, 2, 3, 100):
        verify(edges.astype(dtype), 6, chunk)
verify(edges[:, ::-1], 6)  # Noncontiguous and reverse strides.
verify(np.empty((2, 0), dtype=np.int64), 3)
verify(np.array([[0, 0, 0], [0, 0, 0]], dtype=np.uint64), 1)
# Exhaust all directed edge subsets on three nodes, including loops.
arcs = [(u, v) for u in range(3) for v in range(3)]
for bits in range(1 << len(arcs)):
    chosen = [arc for index, arc in enumerate(arcs) if bits & (1 << index)]
    tiny = np.array(chosen, dtype=np.int64).reshape(-1, 2).T.copy()
    verify(tiny, 3)

hub = np.vstack((np.zeros(10001, dtype=np.int64), np.arange(1, 10002)))
result = verify(hub, 10002, 127)
assert result['maximum_cardinality'] == 10002
assert result['maximum_center_index'] == 0
assert result['centers_above_declared_threshold'] == 1

bad = [
    (np.zeros((3, 1), dtype=np.int64), 3, {}),
    (np.zeros((2, 1), dtype=float), 3, {}),
    (np.zeros((2, 1), dtype=bool), 3, {}),
    (np.zeros((2, 1), dtype=object), 3, {}),
    ([[0], [1]], 3, {}),
    (np.array([[0], [-1]]), 3, {}),
    (np.array([[0], [3]]), 3, {}),
    (np.array([[0], [2**64 - 1]], dtype=np.uint64), 3, {}),
    (edges, 0, {}), (edges, True, {}),
    (edges, 2**32 + 1, {}),
    (edges, 6, {'max_work_bytes': 1}),
    (edges, 6, {'chunk_edges': 0}),
    (edges, 6, {'chunk_edges': True}),
]
for edge, n, options in bad:
    try:
        census(edge, n, **({'max_work_bytes': 10_000_000} | options))
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError('invalid input accepted')
print(json.dumps({'status': 'PASS', 'exhaustive_three_node_graphs': 512,
                  'rejected_invalid_cases': len(bad),
                  'hub_summary': {k: v for k, v in result.items() if k != 'cardinalities'}}, indent=2))
