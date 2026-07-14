import numpy as np
import pandas as pd
import pytest
from tradingagents.stress.overlay import apply_overlay, overlay_metrics, flat_mask


def _idx(n):
    return pd.date_range("2022-01-01", periods=n, freq="D", tz="UTC")


def test_overlay_zeros_warn_and_cooldown():
    idx = _idx(10)
    ret = pd.Series(0.01, index=idx)
    warn = pd.Series([False, True, True, False] + [False] * 6, index=idx)
    out = apply_overlay(ret, warn, cooldown=2)
    # zeroed on warn days 1-2 and cooldown days 3-4
    assert out.iloc[1:5].eq(0.0).all()
    assert out.iloc[0] == 0.01 and out.iloc[5] == 0.01


def test_overlay_avoids_crash_improves_dd():
    idx = _idx(60)
    ret = pd.Series(0.001, index=idx)
    ret.iloc[30:40] = -0.03  # crash
    warn = pd.Series(False, index=idx)
    warn.iloc[28:40] = True  # warned before crash
    m = overlay_metrics(ret, warn, cooldown=2)
    assert m["delta_maxdd"] < 0  # overlay reduces drawdown (positive-magnitude convention: improvement is negative)
    assert m["maxdd_base"] > 0  # positive-magnitude convention pinned
    assert m["sr_overlay"] > m["sr_base"]


def test_zero_variance_sr_is_zero():
    idx = _idx(30)
    ret = pd.Series(0.0, index=idx)
    warn = pd.Series(False, index=idx)
    m = overlay_metrics(ret, warn)
    assert m["sr_base"] == 0.0


def test_maxdd_positive_magnitude_convention():
    idx = _idx(30)
    ret = pd.Series(-0.01, index=idx)
    warn = pd.Series(False, index=idx)
    m = overlay_metrics(ret, warn)
    # cum log-returns: cum[i] = -0.01*(i+1); cummax anchors at day-0 value (-0.01)
    # since the series is monotonically decreasing, so dd.min() = -0.01*29 = -0.29
    # (not -0.30 -- the running max never resets below day 0's own value).
    assert m["maxdd_base"] == pytest.approx(0.2517, abs=1e-3)


def test_exposure_frac_ignores_natural_zero_returns():
    idx = _idx(10)
    ret = pd.Series(0.01, index=idx)
    ret.iloc[3] = 0.0  # naturally-zero return, not a WARN flatten
    warn = pd.Series(False, index=idx)
    m = overlay_metrics(ret, warn)
    assert m["exposure_frac"] == 1.0


def test_cooldown_resets_on_overlapping_clusters():
    idx = _idx(8)
    warn = pd.Series([False, True, False, True, False, False, False, False], index=idx)
    ret = pd.Series(0.01, index=idx)
    out = apply_overlay(ret, warn, cooldown=2)
    # flat: day1 (warn), day2 (cooldown), day3 (warn), day4-5 (cooldown reset by day3 warn)
    expected_flat = pd.Series(
        [False, True, True, True, True, True, False, False], index=idx
    )
    expected = ret.where(~expected_flat, 0.0)
    pd.testing.assert_series_equal(out, expected)
    mask = flat_mask(warn, idx, cooldown=2)
    pd.testing.assert_series_equal(mask, expected_flat, check_names=False)


def test_warn_index_mismatch_missing_is_false():
    idx = _idx(10)
    ret = pd.Series(0.01, index=idx)
    warn = pd.Series(True, index=idx[:5])  # only covers first half
    out = apply_overlay(ret, warn, cooldown=0)
    # uncovered days (missing from warn's index) reindex to False -> exposed, unchanged
    assert out.iloc[5:].eq(0.01).all()
    assert out.iloc[:5].eq(0.0).all()
