import itertools
import math

import numpy as np

from tradingagents.research.onchain_b.matching import agreement as A
from tradingagents.research.onchain_b.matching import reference as R
from tradingagents.research.onchain_b.neighborhoods import Graph


def G(x, edges, ea=None):
    x = np.asarray(x, float)
    edges = np.asarray(edges, np.int64).reshape(2, -1)
    ea = np.zeros((edges.shape[1], 2)) if ea is None else np.asarray(ea, float)
    return Graph(x, edges, ea, np.arange(len(x)), 0)


CFG = A.MatchConfig(alpha=1.0, beta0=1.0, beta_final=30.0, beta_rate=0.075, max_iterations=50)


def test_agreement_values():
    assert A.node_agreement(np.zeros((1, 4)), np.zeros((1, 4)))[0, 0] == 1.0
    assert math.isclose(A.node_agreement(np.zeros((1, 4)), np.full((1, 4), 2.0))[0, 0], math.exp(-4.0))
    assert math.isclose(A.edge_agreement(np.array([[1.0, 3.0]]), np.array([[2.0, 1.0]]))[0, 0], math.exp(-2.5))


def test_score_identical_one_edge_graph_is_three_quarters():
    g = G([[0, 0, 0, 0], [1, 1, 1, 1]], [[0], [1]])
    hard = np.eye(2, dtype=bool)
    # edge term: 1/(2*sqrt(1*1)) = 0.5; node term: 2/sqrt(4) = 1; (0.5+1)/2 = 0.75  (paper Eq.1 literal)
    assert math.isclose(A.score(g, g, hard, 1.0), 0.75)


def test_zero_edge_graph():
    g1 = G([[0, 0, 0, 0]], np.zeros((2, 0)))
    g2 = G([[0, 0, 0, 0], [5, 5, 5, 5]], [[0], [1]])
    r = R.match(g1, g2, CFG)
    assert math.isfinite(r.score) and r.hard.sum() == 1 and r.hard[0, 0]


def test_schedule_has_48_temperatures():
    g = G([[0, 0, 0, 0]], np.zeros((2, 0)))
    assert R.match(g, g, CFG).iterations == 48


def test_reference_within_brute_force_bound():
    rng = np.random.default_rng(0)
    for _ in range(20):
        n1, n2 = int(rng.integers(2, 5)), int(rng.integers(2, 5))
        x1, x2 = rng.normal(size=(n1, 4)), rng.normal(size=(n2, 4))
        e1 = rng.permutation(n1 * n1)[: rng.integers(1, n1 * n1 + 1)]
        e2 = rng.permutation(n2 * n2)[: rng.integers(1, n2 * n2 + 1)]
        g1 = G(x1, [e1 // n1, e1 % n1], rng.normal(size=(len(e1), 2)))
        g2 = G(x2, [e2 // n2, e2 % n2], rng.normal(size=(len(e2), 2)))
        r = R.match(g1, g2, CFG)
        k = min(n1, n2)
        assert r.hard.sum() == k and r.hard.sum(0).max() <= 1 and r.hard.sum(1).max() <= 1
        best = -1.0
        for rows in itertools.combinations(range(n1), k):
            for perm in itertools.permutations(range(n2), k):
                h = np.zeros((n1, n2), bool)
                h[list(rows), list(perm)] = True
                best = max(best, A.score(g1, g2, h, 1.0))
        assert r.score <= best + 1e-12
        assert math.isclose(r.score, A.score(g1, g2, r.hard, 1.0))


def test_relabeling_invariance():
    rng = np.random.default_rng(1)
    n1, n2 = 5, 4
    x1, x2 = rng.normal(size=(n1, 4)), rng.normal(size=(n2, 4))
    e1 = np.array([[0, 1, 2, 3, 4, 0], [1, 2, 3, 4, 0, 2]])
    e2 = np.array([[0, 1, 2, 3], [1, 2, 3, 0]])
    g1 = G(x1, e1, rng.normal(size=(6, 2)))
    g2 = G(x2, e2, rng.normal(size=(4, 2)))
    p = rng.permutation(n1)
    inv = np.argsort(p)
    g1p = G(x1[p], inv[e1], g1.edge_attr)   # old node k becomes new node inv[k]
    a, b = R.match(g1, g2, CFG), R.match(g1p, g2, CFG)
    assert math.isclose(a.score, b.score, rel_tol=1e-9) and np.array_equal(a.hard[p], b.hard)
