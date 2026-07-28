import numpy as np
import pandas as pd
import pytest

from tradingagents.metalabel.labeler import triple_barrier_labels, uniqueness_weights


def _flat_ohlcv(n=60, px=100.0):
    idx = pd.date_range("2023-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "Date": idx, "Open": px, "High": px, "Low": px,
        "Close": px, "Volume": 1.0,
    }), idx


def test_pt_touch_labels_one():
    df, idx = _flat_ohlcv()
    ev = pd.DatetimeIndex([idx[30]])
    # entry exec at bar 31 open=100; force sigma with tiny noise then a +25% spike at bar 33
    df.loc[:30, "Close"] = 100 + np.sin(np.arange(31))  # nonzero sigma
    df.loc[33, "High"] = 130.0
    out = triple_barrier_labels(df, ev)
    assert len(out) == 1
    r = out.iloc[0]
    assert r["touch_type"] == "pt"
    assert r["label"] == 1
    assert r["touch_date"] == idx[33]
    assert r["entry_px"] == 100.0


def test_same_bar_pt_and_sl_resolves_sl_first():
    df, idx = _flat_ohlcv()
    df.loc[:30, "Close"] = 100 + np.sin(np.arange(31))
    ev = pd.DatetimeIndex([idx[30]])
    df.loc[32, "High"] = 200.0   # PT touched
    df.loc[32, "Low"] = 50.0     # SL touched same bar -> SL wins
    out = triple_barrier_labels(df, ev)
    assert out.iloc[0]["touch_type"] == "sl"
    assert out.iloc[0]["label"] == 0


def test_vertical_sign_of_return():
    df, idx = _flat_ohlcv()
    df.loc[:30, "Close"] = 100 + np.sin(np.arange(31))
    # drift +0.1/day, never touching 2-sigma barriers
    for i in range(31, 60):
        for col in ("Open", "High", "Low", "Close"):
            df.loc[i, col] = 100 + 0.01 * (i - 31)
    ev = pd.DatetimeIndex([idx[30]])
    out = triple_barrier_labels(df, ev)
    r = out.iloc[0]
    assert r["touch_type"] == "vertical"
    assert r["touch_date"] == idx[31 + 15]
    assert r["label"] == 1  # positive drift at vertical


def test_event_too_close_to_end_dropped():
    df, idx = _flat_ohlcv(n=35)
    df.loc[:30, "Close"] = 100 + np.sin(np.arange(31))
    ev = pd.DatetimeIndex([idx[33]])  # no t+1 vertical window
    out = triple_barrier_labels(df, ev)
    assert len(out) == 0


def test_sigma_uses_only_past_data():
    df, idx = _flat_ohlcv()
    df.loc[:30, "Close"] = 100 + np.sin(np.arange(31))
    ev = pd.DatetimeIndex([idx[30]])
    base = triple_barrier_labels(df, ev).iloc[0]["sigma"]
    df2 = df.copy()
    df2.loc[45:, "Close"] = 500.0  # future changes must not move sigma at t=30
    assert triple_barrier_labels(df2, ev).iloc[0]["sigma"] == pytest.approx(base)


def test_uniqueness_weights_overlap():
    df, idx = _flat_ohlcv(n=80)
    df["Close"] = 100 + np.sin(np.arange(80))
    ev = pd.DatetimeIndex([idx[30], idx[32]])  # heavy overlap
    labels = triple_barrier_labels(df, ev)
    w = uniqueness_weights(labels, pd.DatetimeIndex(df["Date"]))
    assert len(w) == len(labels)
    assert (w > 0).all() and (w <= 1).all()
    assert w.iloc[0] < 1.0  # overlapping events are down-weighted
