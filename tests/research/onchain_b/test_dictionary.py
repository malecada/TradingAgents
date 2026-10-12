import numpy as np

from tradingagents.research.onchain_b import dictionary as D
from tradingagents.research.onchain_b.matching.agreement import MatchConfig
from tradingagents.research.onchain_b.weekly import WeekGraph

CFG = MatchConfig(1.0, 1.0, 30.0, 0.075, 50)


def _week(week, n, rng):
    ei = np.stack([rng.integers(0, n, 3 * n), rng.integers(0, n, 3 * n)]).astype(np.int32)
    cnt = rng.integers(1, 5, 3 * n)
    ea = np.stack([np.log1p(cnt), np.log1p(cnt)], 1).astype(np.float32)
    return WeekGraph(week, np.array([f'{k:042x}'.encode() for k in range(n)]),
                     rng.normal(size=(n, 4)).astype(np.float32), ei, ea, cnt, {})


def test_sampling_reproducible_and_without_replacement():
    rng = np.random.default_rng(0)
    weeks = {'2022-01-03': _week('2022-01-03', 30, rng), '2022-01-10': _week('2022-01-10', 30, rng)}
    a = D.sample_centers(weeks, 12, 8, seed=11)
    b = D.sample_centers(weeks, 12, 8, seed=11)
    c = D.sample_centers(weeks, 12, 8, seed=23)
    assert a == b and a != c and len(set(a)) == 12


def test_overlap_halving_changes_weights():
    # two-node week: drawing node 0 (neighborhood {0,1}) must halve node 1's weight and zero node 0's
    ei = np.array([[0], [1]], np.int32)
    w = WeekGraph('2022-01-03', np.array([b'0', b'1']), np.zeros((2, 4), np.float32), ei,
                  np.zeros((1, 2), np.float32), np.array([1]), {})
    weights = D._initial_weights({'2022-01-03': w})
    D._halve_inside({'2022-01-03': w}, weights, ('2022-01-03', 0), 8)
    assert weights[1] == 0.5 and weights[0] == 0.0


def test_cluster_medoids_exact_count_and_rule():
    D_ = np.array([[0, .1, .9, .95], [.1, 0, .9, .95], [.9, .9, 0, .2], [.95, .95, .2, 0]])
    med = D.cluster_medoids(D_, 2)
    assert sorted(med) == [0, 2]      # ties by smallest index inside cluster


def test_build_small_dictionary_and_roundtrip(tmp_path):
    rng = np.random.default_rng(1)
    weeks = {'2022-01-03': _week('2022-01-03', 40, rng)}
    d = D.build(weeks, CFG, n_samples=10, n_clusters=3, n_max=6, seed=11)
    assert len(d.motifs) == 3 and all(m.x.shape[0] <= 6 for m in d.motifs) and len(d.centers) == 10
    D.save(d, tmp_path / 'dict')
    e = D.load(tmp_path / 'dict')
    assert e.medoids == d.medoids and e.centers == d.centers and e.n_max == 6
    assert all(np.array_equal(a.x, b.x) and np.array_equal(a.edge_index, b.edge_index) for a, b in zip(d.motifs, e.motifs))
