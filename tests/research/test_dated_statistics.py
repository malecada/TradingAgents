import importlib.util
from pathlib import Path
import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[2] / 'research/strategy-search-2026-09-11/dated_statistics.py'
spec = importlib.util.spec_from_file_location('dated_statistics', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_joint_planted_betas_and_final_day_negative_nav():
    rng = np.random.default_rng(7)
    btc, eth = rng.normal(0, .01, (2, 56))
    nav = 1000 * np.cumprod(1 + .0001 + .07 * btc - .04 * eth)
    result = m.market_exposure(nav, 1000, btc, eth)
    assert result['btc_beta'] == pytest.approx(.07, abs=1e-12)
    assert result['eth_beta'] == pytest.approx(-.04, abs=1e-12)
    nav[-1] = -1
    assert m.market_exposure(nav, 1000, btc, eth)['status'] == 'unavailable'


def test_singular_missing_and_nonfinite_observations_retained_unavailable():
    z = np.zeros(56)
    assert m.market_exposure(np.ones(56), 1, z, z)['status'] == 'unavailable'
    assert m.market_exposure(np.ones(55), 1, z, z)['status'] == 'unavailable'
    z[0] = np.nan
    assert m.market_exposure(np.ones(56), 1, z, z)['status'] == 'unavailable'


def test_spot_first_day_uses_open_later_days_previous_close():
    rows = [[m.START+i*m.DAY, 100, 210, 90, 200, 1, m.START+(i+1)*m.DAY-1, 1, 1, 1, 1, 0] for i in range(56)]
    assert m.spot_returns(rows).tolist() == [1] + [0]*55
    rows[-1][0] += m.DAY
    with pytest.raises(ValueError):
        m.spot_returns(rows)


def test_unavailable_benchmark_preserves_all_cases_and_no_expected_profit_inference():
    result = m.exposure_statistics({'btc-1000-base': {'status':'unavailable'}, 'eth-1000-base': {'status':'unavailable'}}, {})
    assert len(result) == 2
    for row in result.values():
        assert row['market_exposure']['status'] == 'unavailable'
        assert row['expected_return_confidence']['status'] == 'unavailable'
        assert row['power']['status'] == 'unavailable'


def test_fractional_benchmark_clock_cannot_be_truncated():
    rows = [[m.START+i*m.DAY, 100, 210, 90, 200, 1, m.START+(i+1)*m.DAY-1, 1, 1, 1, 1, 0] for i in range(56)]
    rows[0][0] += 0.5
    with pytest.raises(ValueError):
        m.spot_returns(rows)
