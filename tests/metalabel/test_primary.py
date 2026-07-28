import numpy as np
import pandas as pd
import pytest

from tradingagents.metalabel.primary import (
    compute_votes, extract_events, extract_inbar_events, primary_positions,
)


def _ohlcv(closes):
    idx = pd.date_range("2023-01-01", periods=len(closes), freq="D")
    c = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame({
        "Date": idx, "Open": c.values, "High": c.values * 1.01,
        "Low": c.values * 0.99, "Close": c.values, "Volume": 1.0,
    })


def test_votes_uptrend_reach_one_downtrend_zero():
    up = _ohlcv(np.linspace(100, 400, 150))
    v = compute_votes(up)
    assert v.iloc[-1] == 1.0
    down = _ohlcv(np.linspace(400, 100, 150))
    assert compute_votes(down).iloc[-1] == 0.0


def test_votes_warmup_nan():
    v = compute_votes(_ohlcv(np.linspace(100, 200, 150)))
    assert v.iloc[:59].isna().all()


def test_event_on_upcross_only():
    # 80 bars down (vote 0), then strong reversal up -> exactly one entry event
    closes = np.concatenate([np.linspace(200, 100, 80), np.linspace(100, 300, 70)])
    df = _ohlcv(closes)
    v = compute_votes(df)
    ev = extract_events(v)
    assert len(ev) == 1
    assert v.loc[ev[0]] > 0.5
    prev = v.shift(1).loc[ev[0]]
    assert prev <= 0.5


def test_positions_match_votes():
    closes = np.concatenate([np.linspace(200, 100, 80), np.linspace(100, 300, 70)])
    v = compute_votes(_ohlcv(closes))
    pos = primary_positions(v)
    assert set(pos.dropna().unique()) <= {0.0, 1.0}
    assert (pos[v > 0.5] == 1.0).all()
    assert (pos[(v <= 0.5) & v.notna()] == 0.0).all()


def test_inbar_events_dense_superset_of_entries():
    from tradingagents.metalabel.primary import extract_inbar_events
    closes = np.concatenate([np.linspace(200, 100, 80), np.linspace(100, 300, 70)])
    df = _ohlcv(closes)
    v = compute_votes(df)
    dense = extract_inbar_events(v)
    entries = extract_events(v)
    assert set(entries) <= set(dense)
    assert len(dense) > len(entries)
    assert (v.loc[dense] > 0.5).all()
    # NaN warm-up bars never emit events
    assert not any(d in dense for d in v.index[v.isna()])
