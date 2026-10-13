import math
from datetime import date, timedelta

import pytest

from tradingagents.research.onchain_b2 import targets as T

D0 = date(2020, 1, 1)


def _series(f, n=80):
    return {D0 + timedelta(days=i): f(i) for i in range(n)}


def test_directions_and_return():
    p = _series(lambda i: 100.0 * 1.01 ** i)
    m = D0 + timedelta(days=40)
    assert T.t1(p, m) == 1 and T.t2(p, m) == 1
    assert T.t3(p, m) == pytest.approx(7 * math.log(1.01))
    flat = _series(lambda i: 100.0)
    assert T.t1(flat, m) == 0 and T.t2(flat, m) == 0


def test_realised_volatility():
    p = _series(lambda i: 100.0 * (1.02 if i % 2 else 1.0))     # alternating ±log(1.02)
    m = D0 + timedelta(days=40)
    assert T.t4(p, m) == pytest.approx(math.log(math.sqrt(7) * math.log(1.02)))


def test_volume_target_and_missing():
    v = _series(lambda i: 10.0)
    m = D0 + timedelta(days=40)
    assert T.t5(v, m) == pytest.approx(math.log(70.0))
    assert T.t5(v, D0 + timedelta(days=75)) is None


def test_f0_values_and_missing_history():
    p = _series(lambda i: 100.0 * 1.01 ** i)
    v = _series(lambda i: 10.0 if i < 60 else 20.0)
    d = D0 + timedelta(days=66)
    f = T.f0(p, v, d)
    assert f['f0_r1'] == pytest.approx(math.log(1.01)) and f['f0_r7'] == pytest.approx(7 * math.log(1.01))
    assert f['f0_rv7'] == pytest.approx(math.sqrt(7) * math.log(1.01))
    assert f['f0_lvol7'] == pytest.approx(math.log(140.0))
    assert f['f0_volratio'] == pytest.approx(math.log(140.0 / ((7 * 20 + 21 * 10) * 7 / 28)))
    assert T.f0(p, v, D0 + timedelta(days=20)) is None