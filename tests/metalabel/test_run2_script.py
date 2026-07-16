import pandas as pd
import scripts.metalabel2_run as run2


def test_v2_freeze_wiring():
    assert run2.DEV_START == "2022-01-01"
    assert run2.DEV_END == "2025-03-31"
    assert run2.FREEZE["wf"]["min_train_events"] == 75
    assert run2.OUT_DIR.name == "metalabel_v2"


def test_dev_end_inside_dev_window():
    from tradingagents.rebuild.ledger import assert_dev_window
    assert_dev_window(run2.DEV_END)


def test_tau_selection_same_rule_as_v1():
    rows = [
        {"tau": 0.45, "g2_pass": False, "delta_sr": 0.9},
        {"tau": 0.50, "g2_pass": True, "delta_sr": 0.3},
        {"tau": 0.55, "g2_pass": True, "delta_sr": 0.5},
    ]
    assert run2.select_tau(rows) == 0.55
    assert run2.select_tau([{"tau": 0.45, "g2_pass": False, "delta_sr": 0.1}]) is None
