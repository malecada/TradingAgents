"""liq_fade_r1 pre-registration is a contract, not documentation. These
assertions pin the exact gate values so a later edit shows up as a test
failure rather than a silent goalpost move."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GATES = ROOT / "data" / "rebuild" / "gates.json"


@pytest.fixture(scope="module")
def entry():
    g = json.loads(GATES.read_text())
    assert "liq_fade_r1" in g, "liq_fade_r1 not registered in gates.json"
    return g["liq_fade_r1"]


def test_other_experiments_untouched():
    g = json.loads(GATES.read_text())
    for key in ("xs_mom_p1", "fg_beta_d1", "stress_ews", "trend_wide_t1",
                "carry_xs_t1", "liq_mr_t1", "llm_p5_hybrid", "liq_fade_i1"):
        assert key in g, f"{key} disappeared from gates.json"


def test_windows_and_seal(entry):
    assert entry["dev_window"] == ["2021-01-01", "2025-03-31"]
    assert entry["holdout_window"] == ["2025-04-01", "2026-07-01"]
    assert entry["holdout_status"] == "sealed"


def test_config_is_frozen_single(entry):
    assert entry["grid"] is None, "liq_fade_r1 must have NO grid"
    cfg = entry["primary_config"]
    assert cfg == {"thr": 3.5, "H": 48, "w_per": 0.1, "cap": 1.0,
                   "cost_bps": 20.0, "rf_annual": 0.045}


def test_gate_thresholds(entry):
    ds = entry["dev_select"]
    assert ds["net_sr_min"] == 1.0
    assert ds["placebo_p_max"] == 0.05
    assert ds["dsr_min"] == 0.9
    assert ds["n_trials"] == 1
    assert "confirmatory" in ds["n_trials_rationale"].lower()


def test_p3_control_is_blocking(entry):
    p3 = entry["probes"]["P3"]
    assert p3["blocking"] is True
    assert p3["control_max_net_sr"] == 0.5
    assert p3["min_separation"] == 0.75
    assert p3["fail_verdict"] == "NEGATIVE-confounded"


def test_non_gating_reports_declared(entry):
    ng = entry["reported_not_gated"]
    assert 10.0 in ng["cost_bps_sensitivities"]
    assert 30.0 in ng["cost_bps_sensitivities"]
    assert ng["dsr_alt_denominators"] == [13, 121]
    assert {"thr": 2.5, "H": 24} in ng["secondary_configs"]
    assert {"thr": 3.5, "H": 24} in ng["secondary_configs"]
    assert ng["never_top50_subset"] is True
