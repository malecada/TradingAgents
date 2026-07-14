import numpy as np
import pandas as pd
from tradingagents.stress.overlay import apply_overlay, overlay_metrics


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
    assert m["delta_maxdd"] > 0  # overlay reduces drawdown (maxdd_overlay > maxdd_base when both negative)
    assert m["sr_overlay"] > m["sr_base"]


def test_zero_variance_sr_is_zero():
    idx = _idx(30)
    ret = pd.Series(0.0, index=idx)
    warn = pd.Series(False, index=idx)
    m = overlay_metrics(ret, warn)
    assert m["sr_base"] == 0.0
