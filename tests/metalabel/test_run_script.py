import pandas as pd
import pytest

import scripts.metalabel_run as run


def test_dev_end_inside_dev_window():
    from tradingagents.rebuild.ledger import assert_dev_window
    assert_dev_window(run.DEV_END)  # must not raise


def test_tau_selection_prefers_passing_then_delta_sr():
    rows = [
        {"tau": 0.45, "g2_pass": False, "delta_sr": 0.9},
        {"tau": 0.50, "g2_pass": True, "delta_sr": 0.3},
        {"tau": 0.55, "g2_pass": True, "delta_sr": 0.5},
    ]
    assert run.select_tau(rows) == 0.55


def test_tau_selection_none_pass_returns_none():
    rows = [{"tau": 0.45, "g2_pass": False, "delta_sr": 0.1}]
    assert run.select_tau(rows) is None


def test_fng_series_shape(monkeypatch):
    # query_fng wrapper must return a date-indexed float series
    calls = {}
    def fake_query(trade_date, lookback_days=7, **kw):
        calls["hit"] = True
        return pd.DataFrame({"value": [55]})
    monkeypatch.setattr(run, "query_fng", fake_query)
    s = run.fng_series(pd.date_range("2023-01-01", periods=3, freq="D"))
    assert isinstance(s, pd.Series) and len(s) == 3 and calls["hit"]
