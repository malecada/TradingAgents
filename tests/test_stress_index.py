import numpy as np
import pandas as pd
import pytest
from tradingagents.stress.index import zscore_365, composite_warn


def _series(vals):
    idx = pd.date_range("2020-01-01", periods=len(vals), freq="D", tz="UTC")
    return pd.Series(vals, index=idx, dtype=float)


def test_zscore_needs_180_obs():
    s = _series(np.random.default_rng(0).normal(size=400))
    z = zscore_365(s)
    assert z.iloc[:179].isna().all()
    assert z.iloc[200:].notna().all()


def test_zscore_detects_shift():
    vals = [0.0] * 300 + [5.0] * 5
    z = zscore_365(_series(vals))
    assert z.iloc[-1] > 3  # 5-sigma-ish jump vs flat history


def test_composite_warn_hysteresis():
    idx = pd.date_range("2021-01-01", periods=6, freq="D", tz="UTC")
    comp = pd.DataFrame(
        {"z_fund": [0.0, 1.6, 1.4, 1.3, 1.1, 0.5],
         "z_oi":   [0.0, 1.6, 1.4, 1.3, 1.1, 0.5]},
        index=idx,
    )
    out = composite_warn(comp, ["z_fund", "z_oi"], k=1.5)
    # on at 1.6, stays on at 1.4 and 1.3 (>= k-0.25=1.25), off at 1.1
    assert out["warn"].tolist() == [False, True, True, True, False, False]


def test_composite_nan_when_component_missing():
    idx = pd.date_range("2021-01-01", periods=2, freq="D", tz="UTC")
    comp = pd.DataFrame({"z_fund": [1.0, np.nan], "z_oi": [1.0, 2.0]}, index=idx)
    out = composite_warn(comp, ["z_fund", "z_oi"], k=0.5)
    assert np.isnan(out["composite"].iloc[1])
    assert not out["warn"].iloc[1]
