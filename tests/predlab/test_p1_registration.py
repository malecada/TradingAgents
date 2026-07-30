"""Registration guard: the frozen Phase-1 battery content must not drift.

House pattern (tests/xsect/test_value_unlock_registration.py): the gates entry
is asserted field-by-field so silent edits fail CI. Amendments must be made
visible here AND declared inside gates.json.
"""
from __future__ import annotations

from tradingagents.predlab import registry


def _entry():
    return registry.get_experiment("predlab_p1_classical")


def test_windows_and_seal():
    e = _entry()
    assert e["dev_window"] == ["2021-01-01", "2025-03-31"]
    assert e["holdout_window"] == ["2025-04-01", "2026-07-01"]
    assert e["holdout_status"] == "sealed"
    assert e["spec"].endswith("prediction-lab-charter-design.md")


def test_cell_battery_shape():
    e = _entry()
    cells = e["cells"]
    assert len(cells) == 28
    ids = [c["cell"] for c in cells]
    assert len(set(ids)) == 28
    assert "BTCUSDT|24h|T3_rv" in ids
    assert "ETHUSDT|8h|T6_funding" in ids
    baselines = {c["target"]: c["strong_baseline"] for c in cells}
    assert baselines == {
        "T1_ret": "rw_zero",
        "T2_dir": "base_rate",
        "T3_rv": "har_levels",
        "T4_vol": "seasonal_naive",
        "T6_funding": "ar1",
    }


def test_effect_floors_frozen():
    f = _entry()["effect_floors"]
    assert f["T1_oos_r2"] == {"1h": 0.002, "24h": 0.005, "7d": 0.01}
    assert f["T2_edge_pp"] == 2.0
    assert f["T3_dqlike"] == 0.02
    assert f["T4_dmase"] == 0.05
    assert f["T6_dmse"] == 0.05
    assert f["T7_ic"] == 0.02 and f["T7_nw_t"] == 3.0


def test_amendments_declared():
    e = _entry()
    amds = e.get("amendments", [])
    assert len(amds) == 1
    a = amds[0]
    assert a["scope"] == "1h cells, arima/ets/garch models only"
    assert "4320" in a["change"]
    assert a["declared_before_first_result"] is True


def test_protocol_and_grids_frozen():
    e = _entry()
    p = e["protocol"]
    assert p["scheme"] == "rolling_origin_expanding"
    assert p["min_train"] == {"24h": 365, "1h": 2160, "7d": 365}
    assert p["loss"] == {"T1": "se", "T2": "brier", "T3": "qlike", "T4": "mase", "T6": "se"}
    g = e["model_grids"]
    assert g["arima_orders"] == [[1, 0, 0], [0, 0, 1], [1, 0, 1], [2, 0, 2]]
    assert g["har"] == ["har_levels", "log_har", "harq"]
    assert g["ewma_lambda"] == 0.94
    assert "stop_rule" in e and "holdout untouched" in e["stop_rule"]
