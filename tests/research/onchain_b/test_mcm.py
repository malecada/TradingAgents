import numpy as np

from tradingagents.research.onchain_b import dictionary as D
from tradingagents.research.onchain_b import mcm
from tradingagents.research.onchain_b.matching import reference as R
from tradingagents.research.onchain_b.matching.agreement import MatchConfig
from tradingagents.research.onchain_b.neighborhoods import Adjacency
from tradingagents.research.onchain_b.weekly import WeekGraph

CFG = MatchConfig(1.0, 1.0, 30.0, 0.075, 50)


def _week(n, rng):
    ei = np.stack([rng.integers(0, n, 2 * n), rng.integers(0, n, 2 * n)]).astype(np.int32)
    cnt = rng.integers(1, 4, 2 * n)
    return WeekGraph('2022-01-03', np.array([f'{k:042x}'.encode() for k in range(n)]),
                     rng.normal(size=(n, 4)).astype(np.float32), ei,
                     np.stack([np.log1p(cnt), np.log1p(cnt)], 1).astype(np.float32), cnt, {})


def test_compute_week_matches_reference_per_cell():
    rng = np.random.default_rng(7)
    w = _week(25, rng)
    d = D.build({'2022-01-03': w}, CFG, n_samples=6, n_clusters=3, n_max=5, seed=11)
    F = mcm.compute_week(w, d, CFG, n_max=5, chunk=7)
    assert F.shape == (25, 3) and F.dtype == np.float32
    adj = Adjacency.from_week(w)
    for c in (0, 13, 24):
        for m, motif in enumerate(d.motifs):
            assert abs(float(F[c, m]) - R.match(adj.neighborhood(c, 5), motif, CFG).score) < 1e-6
