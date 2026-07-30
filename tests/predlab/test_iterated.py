from __future__ import annotations

import numpy as np

from tradingagents.predlab import tier1
from tradingagents.predlab.iterated import iterate_forecast


def _fitted_ar1(phi=0.5):
    f = tier1.Ar1()
    f._c, f._phi = 0.0, phi
    return f


def test_iterated_ar1_sum_known_value():
    # y_T = 1.0, phi = 0.5: step forecasts 0.5, 0.25, ... sum_{k=1..7} 0.5^k
    y = np.array([0.0, 0.0, 1.0])
    out = iterate_forecast(_fitted_ar1(), y, h=7, agg="sum")
    assert np.isclose(out, sum(0.5**k for k in range(1, 8)))  # 0.9921875


def test_iterated_last_aggregation():
    y = np.array([1.0])
    out = iterate_forecast(_fitted_ar1(), y, h=3, agg="last")
    assert np.isclose(out, 0.125)


def test_iterated_h1_equals_single_step():
    y = np.array([0.3, -0.2, 0.7])
    f = _fitted_ar1(phi=0.4)
    assert np.isclose(iterate_forecast(f, y, h=1, agg="sum"), f.predict(y))
