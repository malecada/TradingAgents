import numpy as np

from tradingagents.research.onchain_b.matching import agreement as A
from tradingagents.research.onchain_b.matching import batched as B
from tradingagents.research.onchain_b.matching import reference as R
from tradingagents.research.onchain_b.neighborhoods import Graph

CFG = A.MatchConfig(1.0, 1.0, 30.0, 0.075, 50)


def rand_graph(rng, n, l):
    e = rng.integers(0, n, size=(2, l)) if l else np.zeros((2, 0), np.int64)
    return Graph(rng.normal(size=(n, 4)), e.astype(np.int64), rng.normal(size=(l, 2)), np.arange(n), 0)


def _check(pairs, scores, hards):
    for (g1, g2), s, h in zip(pairs, scores, hards):
        r = R.match(g1, g2, CFG)
        assert abs(s - r.score) <= 1e-9, (s, r.score)
        assert np.array_equal(h, r.hard)


def test_batched_matches_reference_single_bucket():
    rng = np.random.default_rng(2)
    pairs = [(rand_graph(rng, 4, 5), rand_graph(rng, 3, 4)) for _ in range(6)]
    scores, hards = B.match_many(pairs, CFG)
    _check(pairs, scores, hards)


def test_batched_mixed_edge_counts():
    rng = np.random.default_rng(3)
    pairs = [(rand_graph(rng, 5, l1), rand_graph(rng, 5, l2)) for l1, l2 in [(0, 3), (7, 0), (12, 9), (1, 1), (20, 20)]]
    scores, hards = B.match_many(pairs, CFG)
    _check(pairs, scores, hards)


def test_many_buckets_and_chunking():
    rng = np.random.default_rng(4)
    pairs = [(rand_graph(rng, int(rng.integers(1, 7)), int(rng.integers(0, 10))),
              rand_graph(rng, int(rng.integers(1, 7)), int(rng.integers(0, 10)))) for _ in range(60)]
    scores, hards = B.match_many(pairs, CFG, max_products=50)   # forces many tiny chunks
    _check(pairs, scores, hards)


def test_score_matrix_shape_and_values():
    rng = np.random.default_rng(5)
    L = [rand_graph(rng, 3, 2) for _ in range(3)]
    Rr = [rand_graph(rng, 4, 3) for _ in range(2)]
    S = B.score_matrix(L, Rr, CFG)
    assert S.shape == (3, 2)
    assert abs(S[1, 0] - R.match(L[1], Rr[0], CFG).score) <= 1e-9
