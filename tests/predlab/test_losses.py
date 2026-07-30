from __future__ import annotations

import numpy as np

from tradingagents.predlab import losses


def test_qlike_zero_at_perfect_forecast():
    rv = np.array([0.5, 1.0, 2.0])
    assert np.allclose(losses.qlike(rv, rv), 0.0)


def test_qlike_known_value():
    # r = rv/var = 2: qlike = 2 - ln(2) - 1 = 0.30685281944005469
    out = losses.qlike(np.array([1.0]), np.array([2.0]))
    assert np.isclose(out[0], 0.30685281944005469)


def test_qlike_asymmetric_penalizes_underforecast_more():
    # under-forecast (var=0.5 for rv=1) must cost more than over-forecast (var=2)
    under = losses.qlike(np.array([0.5]), np.array([1.0]))[0]
    over = losses.qlike(np.array([2.0]), np.array([1.0]))[0]
    assert under > over > 0


def test_qlike_nonpositive_gives_nan():
    out = losses.qlike(np.array([1.0, 0.0, -1.0]), np.array([0.0, 1.0, 1.0]))
    assert np.isnan(out).all()


def test_mase_scale_seasonal():
    y = np.array([1.0, 2.0, 3.0, 5.0])
    # m=1 diffs |1,1,2| -> mean 4/3
    assert np.isclose(losses.mase_scale(y, m=1), 4.0 / 3.0)
    # m=2 diffs |2,3| -> mean 2.5
    assert np.isclose(losses.mase_scale(y, m=2), 2.5)


def test_mase_uses_train_scale():
    scale = losses.mase_scale(np.array([0.0, 1.0]), m=1)  # 1.0
    out = losses.mase(np.array([2.0]), np.array([0.5]), scale)
    assert np.isclose(out[0], 1.5)


def test_brier_and_se_ae():
    assert np.isclose(losses.brier(np.array([0.8]), np.array([1.0]))[0], 0.04)
    assert np.isclose(losses.se(np.array([1.0]), np.array([3.0]))[0], 4.0)
    assert np.isclose(losses.ae(np.array([1.0]), np.array([3.0]))[0], 2.0)
