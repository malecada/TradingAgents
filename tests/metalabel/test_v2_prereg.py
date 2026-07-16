import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    return json.loads((ROOT / "experiments" / "metalabel_v2" / name).read_text())


def test_v2_freeze_deltas_and_inherited_values():
    f = _load("freeze.json")
    v1 = json.loads((ROOT / "experiments" / "metalabel" / "freeze.json").read_text())
    assert f["event_scheme"] == "inbar_dense"
    assert f["dev_window"] == ["2022-01-01", "2025-03-31"]
    assert f["wf"]["min_train_events"] == 75
    assert f["g1_bootstrap"] == "cluster"
    # everything else inherited verbatim
    for key in ("ma_pairs", "donchian", "barriers", "sigma_span", "tau_grid",
                "cost_bps_round_trip", "vol_target_ann", "coins",
                "holdout_window", "lgb_grid", "size_mult"):
        assert f[key] == v1[key], key
    assert f["wf"]["retrain_every_days"] == v1["wf"]["retrain_every_days"]
    assert f["wf"]["embargo_bars"] == v1["wf"]["embargo_bars"]


def test_v2_gates_match_v1_formulas():
    g = _load("gates.json")
    v1 = json.loads((ROOT / "experiments" / "metalabel" / "gates.json").read_text())
    assert g["G1"]["auc_ci_excludes"] == 0.5
    assert g["G1"]["bootstrap"] == "cluster_coin_month"
    assert g["G2"] == v1["G2"]
    assert g["G3"] == v1["G3"]
    assert g["holdout_start"] == "2025-04-01"
    assert g["experiment"] == "metalabel2-2026-07"
