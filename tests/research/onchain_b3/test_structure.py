import math

import networkx as nx
import numpy as np
import pyarrow as pa
import pytest

from tradingagents.research.onchain_b.weekly import _index
from tradingagents.research.onchain_b3 import structure as ST

CFG = {'hill_min': 50, 'hill_frac': 0.01, 'cores': [2, 3, 5, 10],
       'pagerank': {'damping': 0.85, 'tol': 1e-12, 'max_iter': 1000}, 'wedges': 200000}


def addr(i):
    return '0x' + f'{i:040x}'


def pairs(edges):
    return pa.table({'src': [addr(a) for a, b, c, v in edges], 'dst': [addr(b) for a, b, c, v in edges],
                     'count': [c for *_, c, v in edges], 'value_eth': [float(v) for *_, v in edges]})


def test_gini_and_hill():
    assert ST.gini([1, 1, 1, 1]) == pytest.approx(0.0) and ST.gini([0, 0, 0, 4]) == pytest.approx(0.75)
    rng = np.random.default_rng(0)
    x = (1 - rng.random(200000)) ** (-1 / 2.0)              # Pareto, tail index 2
    assert ST.hill(x, 50, 0.01) == pytest.approx(2.0, abs=0.2)


def test_against_networkx_on_random_graph():
    rng = np.random.default_rng(1)
    g = nx.gnm_random_graph(400, 1600, seed=2, directed=True)
    edges = [(u, v, 1, float(rng.integers(1, 10))) for u, v in g.edges()]
    idx = _index(pairs(edges))
    addresses, s, d, count, value = idx
    n = len(addresses)
    f = ST.structure_features(idx, np.zeros(n, bool), CFG, seed=7)
    # rebuild the same graph in networkx on the index's node numbering
    G = nx.DiGraph()
    G.add_nodes_from(range(n))
    for a, b, w in zip(s, d, value):
        if a != b:
            G.add_edge(int(a), int(b), weight=float(w))
    U = G.to_undirected()
    assert f['f4_components'] == nx.number_connected_components(U)
    pr = nx.pagerank(G, alpha=0.85, tol=1e-12, max_iter=1000, weight=None)
    p = ST.pagerank(s, d, np.ones(len(s)), n, 0.85, 1e-12, 1000)
    assert max(abs(p[i] - pr[i]) for i in range(n)) < 1e-8
    prv = nx.pagerank(G, alpha=0.85, tol=1e-12, max_iter=1000, weight='weight')
    pv = ST.pagerank(s, d, value, n, 0.85, 1e-12, 1000)
    assert max(abs(pv[i] - prv[i]) for i in range(n)) < 1e-8
    core = nx.core_number(nx.Graph(U))
    for k in (2, 3, 5, 10):
        assert f[f'f4_core{k}_share'] == pytest.approx(sum(1 for v in core.values() if v >= k) / n)
    assert f['f4_transitivity'] == pytest.approx(nx.transitivity(nx.Graph(U)), abs=0.01)
    recip = sum(1 for a, b in G.edges() if G.has_edge(b, a)) / G.number_of_edges()
    assert f['f4_recip_edge_share'] == pytest.approx(recip)


def test_hand_graph_values():
    # A->B 2x(10), B->A 1x(5), B->C (1), C->D (1), E->E self (3), F->G (1)
    e = [(1, 2, 2, 10), (2, 1, 1, 5), (2, 3, 1, 1), (3, 4, 1, 1), (5, 5, 1, 3), (6, 7, 1, 1)]
    idx = _index(pairs(e))
    n = len(idx[0])
    f = ST.structure_features(idx, np.zeros(n, bool), CFG, seed=1)
    assert n == 7
    assert f['f4_components'] == 3 and f['f4_pair_components'] == 1      # {1,2,3,4}, {5}, {6,7}
    assert f['f4_giant_node_share'] == pytest.approx(4 / 7)
    assert f['f4_giant_value_share'] == pytest.approx(17 / 18)            # non-self ETH: 10+5+1+1+1
    assert f['f4_recip_edge_share'] == pytest.approx(2 / 5) and f['f4_recip_value_share'] == pytest.approx(15 / 18)
    assert f['f4_leaf_share'] == pytest.approx(4 / 7)                     # nodes 1, 4, 6, 7 have one counterparty
    assert f['f4_maxdeg_share'] == pytest.approx(2 / 8)                   # node 2 has 2 counterparties; sum of degrees 8


def test_self_only_nodes():
    e = [(1, 1, 1, 2.0), (2, 3, 1, 1.0)]
    idx = _index(pairs(e))
    n = len(idx[0])
    f = ST.structure_features(idx, np.zeros(n, bool), CFG, seed=1)
    assert n == 3 and f['f4_leaf_share'] == pytest.approx(2 / 3) and f['f4_components'] == 2
    assert all(math.isfinite(v) for k, v in f.items() if k != 'f4_deg_tail')


def test_degenerate_graphs_are_finite():
    idx = _index(pairs([(1, 2, 1, 1.0)]))
    f = ST.structure_features(idx, np.zeros(2, bool), CFG, seed=1)
    assert f['f4_transitivity'] == 0.0 and f['f4_log_wedges'] == 0.0 and f['f4_recip_edge_share'] == 0.0
    assert f['f4_core2_share'] == 0.0 and f['f4_components'] == 1
    assert all(math.isfinite(v) for k, v in f.items() if k != 'f4_deg_tail')


def test_exchange_pagerank_share():
    e = [(1, 9, 1, 1.0), (2, 9, 1, 1.0), (3, 9, 1, 1.0), (9, 4, 1, 1.0)]
    idx = _index(pairs(e))
    is_ex = np.array([a.decode() == addr(9) for a in idx[0]])
    f = ST.structure_features(idx, is_ex, CFG, seed=1)
    p = ST.pagerank(idx[1], idx[2], np.ones(len(idx[1])), len(idx[0]), 0.85, 1e-12, 1000)
    assert f['f4_pr_ex_share'] == pytest.approx(p[is_ex].sum() / p.sum())