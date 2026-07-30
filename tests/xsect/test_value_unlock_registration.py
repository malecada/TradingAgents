# tests/xsect/test_value_unlock_registration.py
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATES = ROOT / "data" / "rebuild" / "gates.json"


def _entry(name):
    return json.loads(GATES.read_text())[name]


def test_both_experiments_registered():
    g = json.loads(GATES.read_text())
    assert "value_xs_t1" in g and "unlock_xs_t1" in g


def test_windows_frozen():
    for name in ("value_xs_t1", "unlock_xs_t1"):
        e = _entry(name)
        assert e["dev_window"] == ["2021-01-01", "2025-03-31"]
        assert e["holdout_window"] == ["2025-04-01", "2026-07-01"]
        assert e["holdout_status"] == "sealed"


def test_gate_bars_frozen():
    for name in ("value_xs_t1", "unlock_xs_t1"):
        d = _entry(name)["dev_select"]
        assert d["net_sr_min"] == 1.0
        assert d["placebo_p_max"] == 0.05
        assert d["dsr_min"] == 0.9
        assert d["delta_sr_vs_c1_min"] == 0.0
        assert d["delta_sr_vs_c2_min"] == 0.0
        assert d["conventions"].startswith("sqrt(365)")


def test_dsr_denominator_amendment_declared():
    for name, n in (("value_xs_t1", 4), ("unlock_xs_t1", 2)):
        d = _entry(name)["dev_select"]
        assert d["n_trials"] == n
        assert "amendment" in d["n_trials_rationale"].lower()
        assert "reported_not_gated" in _entry(name)


def test_frozen_grid_sizes():
    assert len(_entry("value_xs_t1")["grid"]) == 4
    assert len(_entry("unlock_xs_t1")["grid"]) == 2


def test_universe_and_breadth_frozen():
    for name in ("value_xs_t1", "unlock_xs_t1"):
        e = _entry(name)
        assert e["universe"]["liquidity_floor_rank"] == 150
        assert e["universe"]["min_median_breadth"] == 20
        assert e["rebalance"] == "weekly_monday"
        assert e["costs"]["bps_per_side"] == 10.0
        assert e["costs"]["rf_annual"] == 0.045
