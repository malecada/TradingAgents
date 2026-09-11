import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11/carry_statistics.py"
spec = importlib.util.spec_from_file_location("carry_statistics", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_paired_bootstrap_preserves_constant_and_linear_relations():
    x = np.zeros((8, 91))
    x[0] = .0001
    x[1] = np.arange(91) / 1e6
    x[2] = 2 * x[1]
    results = module.paired_uncertainty(x)
    assert results[0]["annualized_lower"] == pytest.approx(.0365)
    assert results[0]["annualized_upper"] == pytest.approx(.0365)
    for field in ("annualized_lower", "annualized_upper", "bootstrap_standard_error"):
        assert results[2][field] == pytest.approx(2 * results[1][field])
    assert results[7]["annualized_point"] == 0


def test_planted_market_exposure_recovered_from_nav_quantities():
    rng = np.random.default_rng(2)
    btc, eth = rng.normal(0, .01, (2, 91))
    y = .0001 + .08 * btc - .03 * eth
    nav = 1000 * np.cumprod(1 + y)
    result = module.market_exposure(nav, 1000, btc, eth)
    assert result["status"] == "complete"
    assert result["btc_beta"] == pytest.approx(.08, abs=1e-12)
    assert result["eth_beta"] == pytest.approx(-.03, abs=1e-12)


def test_singular_design_and_nonpositive_nav_unavailable():
    assert module.market_exposure(np.ones(91), 1, np.zeros(91), np.zeros(91))["status"] == "unavailable"
    assert module.market_exposure(np.zeros(91), 1, np.arange(91), np.arange(91))["status"] == "unavailable"


def test_missing_or_nonfinite_days_cannot_disappear():
    with pytest.raises(ValueError):
        module.paired_uncertainty(np.zeros((8, 90)))
    x = np.zeros((8, 91)); x[0, 0] = np.nan
    with pytest.raises(ValueError):
        module.paired_uncertainty(x)


def test_last_day_negative_nav_cannot_enter_beta_regression():
    rng = np.random.default_rng(47)
    btc, eth = rng.normal(0, .01, (2, 91))
    nav = np.full(91, 1000.0)
    nav[-1] = -1
    result = module.market_exposure(nav, 1000, btc, eth)
    assert result["status"] == "unavailable"
