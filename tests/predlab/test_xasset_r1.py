"""Unit tests for the xasset_equity_r1 runner (engine-port pieces only;
the crypto parity pin itself runs inside `probes` against the real store)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from predlab_xasset_r1 import (  # noqa: E402
    ANN_EQ, overlay_o4, with_borrow, quarters,
)


def _base(n=60, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC")
    net = pd.Series(rng.normal(0.001, 0.01, n), index=idx)
    return pd.DataFrame({"net": net, "gross": net + 0.0001,
                         "turnover": 0.25, "carry": 0.0})


def test_overlay_matches_champion_formula_at_365():
    """Byte-for-byte re-derivation of the O4 formula (predlab_champion_backtest.py:59-68)."""
    base = _base()
    breadth = pd.Series(200, index=base.index)
    got, s_got = overlay_o4(base, breadth, 0.15, ann=365.0)
    net = base["net"]
    sh = net.rolling(20).std().shift(1) * np.sqrt(365.0)
    s = (0.15 / sh).clip(0.0, 2.0).fillna(0.0)
    s = s.where(breadth >= 100, 0.0)
    cost = 5.0 / 1e4 * (s * base["turnover"] + s.diff().abs().fillna(0.0) * 2.0)
    pd.testing.assert_series_equal(got, s * net - cost)
    pd.testing.assert_series_equal(s_got, s)


def test_overlay_breadth_guard_zeroes_scale():
    base = _base()
    breadth = pd.Series(200, index=base.index)
    breadth.iloc[30:35] = 50
    _, s = overlay_o4(base, breadth, 0.15)
    assert (s.iloc[30:35] == 0.0).all()
    assert s.iloc[36] > 0.0  # stateless: re-arms immediately


def test_with_borrow_daily_charge():
    idx = pd.date_range("2020-01-01", periods=3, freq="D", tz="UTC")
    net = pd.Series([0.01, 0.01, 0.01], index=idx)
    scale = pd.Series([1.0, 2.0, 0.0], index=idx)
    out = with_borrow(net, scale, 0.0252)
    exp = net - (0.0252 / ANN_EQ) * scale
    pd.testing.assert_series_equal(out, exp)
    assert out.iloc[2] == net.iloc[2]  # no charge while flat


def test_quarters_cover_window_in_order():
    qs = quarters(("2017-01-03", "2026-08-14"))
    assert len(qs) == 4
    assert qs[0][1] == "2017-01-03"
    assert qs[-1][2] == "2026-08-14"
    for (_, _, hi), (_, lo, _) in zip(qs, qs[1:]):
        assert hi == lo


def test_gap_segmentation_rule():
    """Mirror of the loader's >90d gap split on a synthetic frame."""
    dates = (list(pd.date_range("2020-01-01", periods=10)) +
             list(pd.date_range("2020-06-01", periods=10)))
    d = pd.DataFrame({"x": 1.0}, index=pd.DatetimeIndex(dates))
    gaps = d.index.to_series().diff() > pd.Timedelta(days=90)
    seg_id = gaps.cumsum()
    assert seg_id.nunique() == 2
    assert (seg_id.iloc[:10] == 0).all() and (seg_id.iloc[10:] == 1).all()
