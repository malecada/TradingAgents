import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    return json.loads((ROOT / "experiments" / "metalabel" / name).read_text())


def test_gates_json_complete():
    g = _load("gates.json")
    assert g["G1"]["auc_ci_excludes"] == 0.5
    assert g["G1"]["must_beat"] == ["constant_base_rate", "logistic"]
    assert g["G2"]["delta_sr_p_pos_min"] == 0.90
    assert g["G2"]["max_dd_ratio_max"] == 1.1
    assert g["G3"]["one_shot"] is True
    assert g["holdout_start"] == "2025-04-01"


def test_freeze_json_pins_all_frozen_params():
    f = _load("freeze.json")
    assert f["ma_pairs"] == [[5, 20], [10, 40], [20, 60]]
    assert f["donchian"] == {"entry": 20, "exit": 10}
    assert f["barriers"] == {"pt_mult": 2.0, "sl_mult": 1.5, "vertical_bars": 15}
    assert f["sigma_span"] == 20
    assert f["tau_grid"] == [0.45, 0.50, 0.55, 0.60]
    assert f["cost_bps_round_trip"] == 10
    assert f["vol_target_ann"] == 0.30
    assert f["coins"] == [
        "bitcoin", "ethereum", "binancecoin", "solana",
        "ripple", "dogecoin", "cardano", "tron",
    ]
    assert f["dev_window"] == ["2021-07-01", "2025-03-31"]
    assert f["holdout_window"] == ["2025-04-01", "2026-06-30"]


def test_holdout_guard_blocks_dev_run_into_holdout():
    from tradingagents.rebuild.ledger import assert_dev_window
    with pytest.raises(ValueError):
        assert_dev_window("2025-04-01")
    assert_dev_window("2025-03-31")  # must not raise
