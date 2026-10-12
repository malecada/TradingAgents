import numpy as np

from tradingagents.research.onchain_b.neighborhoods import Adjacency
from tradingagents.research.onchain_b.weekly import WeekGraph


def _week():
    # 0→1 (c3), 1→0 (c1), 0→2 (c1), 2→3 (c5), 3→0 (c2), 0→0 (c1)
    ei = np.array([[0, 1, 0, 2, 3, 0], [1, 0, 2, 3, 0, 0]], np.int32)
    cnt = np.array([3, 1, 1, 5, 2, 1])
    ea = np.stack([np.log1p(cnt), np.log1p(cnt * 1.5)], 1).astype(np.float32)
    x = np.arange(16, dtype=np.float32).reshape(4, 4)
    return WeekGraph('2022-01-03', np.array([b'a', b'b', b'c', b'd']), x, ei, ea, cnt, {})


def test_full_neighborhood_of_hub():
    g = Adjacency.from_week(_week()).neighborhood(0, 32)
    assert list(g.nodes) == [0, 1, 2, 3] and g.center == 0
    e = {(int(s), int(d)) for s, d in g.edge_index.T}
    assert e == {(0, 1), (1, 0), (0, 2), (2, 3), (3, 0), (0, 0)}   # induced, self loop kept, global order kept
    assert g.x.dtype == np.float64 and g.edge_attr.dtype == np.float64


def test_n_max_keeps_strongest_neighbors():
    g = Adjacency.from_week(_week()).neighborhood(0, 3)
    # interaction with 0: node1 = 3+1 = 4, node3 = 2, node2 = 1 → keep {0,1,3}
    assert list(g.nodes) == [0, 1, 3]
    e = {(int(s), int(d)) for s, d in g.edge_index.T}
    assert e == {(0, 1), (1, 0), (2, 0), (0, 0)}


def test_center_with_two_neighbors_keeps_stronger():
    g = Adjacency.from_week(_week()).neighborhood(3, 2)
    # neighbors of 3: node2 (2→3 count 5) and node0 (3→0 count 2) → keep node2
    assert list(g.nodes) == [2, 3] and g.center == 1
    e = {(int(s), int(d)) for s, d in g.edge_index.T}
    assert e == {(0, 1)}


def test_edge_attr_follows_selected_edges():
    w = _week()
    g = Adjacency.from_week(w).neighborhood(3, 2)
    assert np.isclose(g.edge_attr[0, 0], np.log1p(5))
