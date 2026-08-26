"""Unit tests for predlab_nlst_lib — required before first registered use."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from predlab_nlst_lib import (  # noqa: E402
    concentration,
    event_cum_returns,
    listing_events,
    p0_stats,
    sign_test_p,
    v2_buy,
    v2_sell,
)


def _days(start, n):
    return pd.date_range(start, periods=n, freq="D", tz="UTC")


# ------------------------------------------------------------ event returns


def test_event_cum_price_only_matches_close_ratio():
    idx = _days("2022-01-01", 30)
    close = pd.Series(np.linspace(100, 129, 30), index=idx)
    out = event_cum_returns(close, pd.Series(dtype=float), horizons=(5,))
    # entry at close of bar1, exit close of bar 6
    expect = close.iloc[6] / close.iloc[1] - 1
    assert out["ret5"] == pytest.approx(expect)
    assert out["px5"] == pytest.approx(expect)
    assert out["fund5"] == 0.0


def test_event_cum_excludes_bar0_and_bar1_returns():
    idx = _days("2022-01-01", 30)
    c = pd.Series(100.0, index=idx)
    c.iloc[0] = 10.0   # +900% bar0->bar1 must NOT enter any horizon
    out = event_cum_returns(c, pd.Series(dtype=float), horizons=(5,))
    assert out["ret5"] == pytest.approx(0.0)


def test_event_cum_funding_reduces_long_return():
    idx = _days("2022-01-01", 30)
    close = pd.Series(100.0 * 1.01 ** np.arange(30), index=idx)
    fund = pd.Series(0.002, index=idx.floor("D"))  # longs pay 20bp/day
    out = event_cum_returns(close, fund, horizons=(5,))
    assert out["ret5"] == pytest.approx((1 + 0.01 - 0.002) ** 5 - 1)
    assert out["px5"] == pytest.approx(1.01 ** 5 - 1)
    assert out["fund5"] == pytest.approx(0.01)


def test_event_cum_nan_when_too_short():
    idx = _days("2022-01-01", 10)
    close = pd.Series(100.0, index=idx)
    out = event_cum_returns(close, pd.Series(dtype=float), horizons=(20,))
    assert np.isnan(out["ret20"])


def test_event_cum_negative_funding_adds_to_long():
    idx = _days("2022-01-01", 30)
    close = pd.Series(100.0, index=idx)  # flat price
    fund = pd.Series(-0.01, index=idx.floor("D"))  # shorts pay longs 1%/day
    out = event_cum_returns(close, fund, horizons=(5,))
    assert out["ret5"] == pytest.approx(1.01 ** 5 - 1)


# ------------------------------------------------------------ enumeration


def test_listing_events_first_bar_and_dev_clip(tmp_path):
    idx_a = _days("2022-06-01", 100)     # in-window, long enough
    idx_b = _days("2020-05-01", 900)     # pre-window listing -> excluded
    idx_c = _days("2025-03-20", 40)      # in-window but <22 dev bars -> excluded
    for name, idx in [("AAAUSDT", idx_a), ("BBBUSDT", idx_b), ("CCCUSDT", idx_c)]:
        pd.DataFrame({"close": np.ones(len(idx))}, index=idx).to_parquet(
            tmp_path / f"{name}.parquet")
    ev = listing_events(tmp_path, dev=("2021-01-01", "2025-03-31"), max_h=20)
    assert list(ev.index) == ["AAAUSDT"]
    assert ev.loc["AAAUSDT", "list_date"] == idx_a[0]


# ------------------------------------------------------------ stats


def test_sign_test_symmetric_is_one():
    assert sign_test_p(np.array([1.0, -1.0, 2.0, -2.0])) == pytest.approx(1.0)


def test_sign_test_all_positive_small():
    p = sign_test_p(np.ones(10))
    assert p == pytest.approx(2 * 0.5 ** 10)


def test_concentration_top_share():
    s = pd.Series([10.0, 1.0, 1.0], index=["A", "B", "C"])
    c = concentration(s)
    assert c["top_event"] == "A"
    assert c["top_share"] == pytest.approx(10 / 12)
    assert c["mean_ex_top"] == pytest.approx(1.0)


def test_p0_stats_recovers_known_mean():
    n = 200
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "list_date": _days("2021-01-01", n),
        "ret5": 0.05 + rng.normal(0, 0.01, n),
    })
    st = p0_stats(df, "ret5")
    assert st["n"] == n
    assert st["mean"] == pytest.approx(0.05, abs=0.005)
    assert st["nw_t"] > 10
    assert st["sign_p"] < 1e-6


# ------------------------------------------------------------ v2 amm math


def test_v2_roundtrip_costs_two_fees_when_deep():
    r_w, r_t = 1e9, 1e9  # effectively infinite depth -> impact ~ 0
    tok = v2_buy(1.0, r_w, r_t)
    back = v2_sell(tok, r_w, r_t)
    assert back == pytest.approx((1 - 0.003) ** 2, rel=1e-6)


def test_v2_buy_price_impact_direction():
    # spending 10% of the WETH reserve must yield much worse than spot
    tok_small = v2_buy(0.001, 100.0, 1000.0)
    tok_big = v2_buy(10.0, 100.0, 1000.0)
    assert tok_small / 0.001 > tok_big / 10.0
    # exact formula check
    eff = 10.0 * 0.997
    assert tok_big == pytest.approx(eff * 1000.0 / (100.0 + eff))


def test_v2_sell_into_thin_pool_bounded_by_reserve():
    out = v2_sell(1e12, 50.0, 1000.0)
    assert out < 50.0  # can never extract more than the WETH reserve
