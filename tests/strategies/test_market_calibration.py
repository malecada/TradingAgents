import os
import tempfile

import numpy as np
import pytest

from tradingagents.strategies.market_calibration import (
    MARKET_CALIBRATOR_FILENAME,
    fit_market_calibrator,
    load_market_calibrator,
)


def test_filename_template_includes_coin():
    assert "{coin}" in MARKET_CALIBRATOR_FILENAME


def test_fit_then_load_roundtrip(tmp_path):
    rng = np.random.default_rng(0)
    raw = rng.uniform(0.0, 1.0, 200)
    realised = (raw > 0.55).astype(int)
    fit_market_calibrator(raw, realised, coin="bitcoin", root=str(tmp_path))
    c = load_market_calibrator("bitcoin", root=str(tmp_path))
    assert 0.0 <= c.transform(0.9) <= 1.0
    assert 0.0 <= c.transform(0.1) <= 1.0


def test_load_unfit_coin_returns_identity(tmp_path):
    c = load_market_calibrator("nonexistent", root=str(tmp_path))
    assert c.transform(0.42) == pytest.approx(0.42)


def test_fit_rejects_too_few_samples(tmp_path):
    with pytest.raises(ValueError):
        fit_market_calibrator(
            np.array([0.1, 0.5, 0.9]),
            np.array([0, 1, 1]),
            coin="bitcoin",
            root=str(tmp_path),
        )
