import numpy as np
import pytest

from tradingagents.research.onchain_b.weekly import WeekGraph
from tradingagents.research.onchain_b2.motiffeat import motif_features

A, B, C = ('0x' + c * 40 for c in 'abc')


def _graph():
    x = np.zeros((3, 4), np.float32)
    x[0, 2] = np.log1p(1.0)          # node 0: 1 ETH in
    x[1, 3] = np.log1p(3.0)          # node 1: 3 ETH out
    return WeekGraph('2019-06-03', np.array([A, B, C], dtype='S42'), x, np.zeros((2, 0), np.int32),
                     np.zeros((0, 2), np.float32), np.zeros(0, np.int64), {})


def test_motif_features():
    F = np.array([[0.1, 0.9], [0.8, 0.2], [0.5, 0.5]], np.float32)
    f = motif_features(F, _graph(), exchanges={B}, whales={A, C})
    assert f['f2_hist_0'] == pytest.approx(2 / 3) and f['f2_hist_1'] == pytest.approx(1 / 3)   # tie → motif 0
    assert f['f2_mean_0'] == pytest.approx(1.4 / 3) and f['f2_mean_1'] == pytest.approx(1.6 / 3)
    assert f['f2_vw_0'] == pytest.approx(0.625, abs=1e-6) and f['f2_vw_1'] == pytest.approx(0.375, abs=1e-6)
    assert f['f3b_ex_0'] == pytest.approx(0.8) and f['f3b_ex_n'] == 1
    assert f['f3b_wh_0'] == pytest.approx(0.3) and f['f3b_wh_1'] == pytest.approx(0.7) and f['f3b_wh_n'] == 2


def test_absent_roles_give_zeros():
    F = np.array([[0.1, 0.9], [0.8, 0.2], [0.5, 0.5]], np.float32)
    f = motif_features(F, _graph(), exchanges=set(), whales=set())
    assert f['f3b_ex_n'] == 0 and f['f3b_ex_0'] == 0.0 and f['f3b_wh_1'] == 0.0