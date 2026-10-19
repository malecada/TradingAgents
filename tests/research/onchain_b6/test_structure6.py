# tests/research/onchain_b6/test_structure6.py
import numpy as np

from tradingagents.research.onchain_b6 import structure6 as S

u = lambda *x: np.array(x, np.uint64)


def test_structure_on_hand_built_hour():
    # exchanges 100 (entity 0), 101 (entity 1); users 1..6; triangle 1-2-3 (2-core), 4 pendant on 1, 5-6 isolated pair
    src = u(1, 2, 3, 4, 5, 1, 2, 100, 100)
    dst = u(2, 3, 1, 1, 6, 100, 101, 1, 101)
    usd = np.array([10.0, 20.0, 0.0, 5.0, 1.0, 40.0, 0.0, 4.0, 20.0])
    ex = lambda k: np.isin(k, [100, 101])
    ent = lambda k: np.where(k == 100, 0, np.where(k == 101, 1, -1))
    seen = lambda k: np.isin(k, [1, 2, 3, 100, 101])          # 4, 5, 6 are new
    r = S.hour_structure(src, dst, usd, ex(src), ex(dst), ent(src), ent(dst), seen, 10)
    assert r['gs_active'] == 8 and r['gs_edges'] == 9 and np.isclose(r['gs_edges_per_node'], 9 / 8)
    assert np.isclose(r['gs_new_share'], 3 / 8)
    out = {1: 50.0, 2: 20.0, 4: 5.0, 5: 1.0, 100: 24.0}                 # outgoing USD per address
    assert np.isclose(r['gs_top10_share'], 1.0) and r['gs_value_gini'] > 0.3
    assert np.isclose(r['gs_core2_share'], 5 / 8) and np.isclose(r['gs_giant_share'], 6 / 8)   # 2-core: 1,2,3 + cycle 1-100-101-2
    assert r['gs_ex_cp'] == 2 and np.isclose(r['gs_ex_cp_new_share'], 0.0)   # users 1 and 2 touch exchanges
    assert np.isclose(r['gs_cex_cex_usd'], 20.0)


def test_structure_degenerate_hours():
    empty = S.hour_structure(u(), u(), np.array([]), np.array([], bool), np.array([], bool),
                             np.array([], np.int32), np.array([], np.int32), lambda k: np.zeros(len(k), bool), 10)
    assert all(np.isfinite(v) for v in empty.values()) and empty['gs_active'] == 0
    one = S.hour_structure(u(1), u(2), np.array([3.0]), np.array([False]), np.array([False]),
                           np.array([-1]), np.array([-1]), lambda k: np.zeros(len(k), bool), 10)
    assert one['gs_active'] == 2 and one['gs_core2_share'] == 0.0 and one['gs_giant_share'] == 1.0
    assert set(empty) == set(S.NAMES)
