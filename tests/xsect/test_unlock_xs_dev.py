"""Contract tests for scripts/unlock_xs_dev.py.

The load-bearing one is the STOP contract: a failing probe must write
probes.json AND exit 2 through main() itself — value_xs_t1 lost two review
rounds to a failure that was loud in a unit test but not wired into the
pipeline contract.
"""
import json

import pandas as pd
import pytest

import scripts.unlock_xs_dev as dev

ROOT = dev.ROOT


def test_grid_matches_registration():
    g = json.loads((ROOT / "data" / "rebuild" / "gates.json").read_text())
    reg = g["unlock_xs_t1"]["grid"]
    assert [(c["lookahead_days"], c["breadth"]) for c in reg] == dev.GRID
    assert g["unlock_xs_t1"]["dev_select"]["n_trials"] == len(dev.GRID)


def test_windows_match_registration():
    g = json.loads((ROOT / "data" / "rebuild" / "gates.json").read_text())
    assert list(dev.DEV) == g["unlock_xs_t1"]["dev_window"]
    assert dev.MAX_LOAD_END == dev.DEV[1]
    assert dev.MIN_MEDIAN_BREADTH == \
        g["unlock_xs_t1"]["universe"]["min_median_breadth"]


def test_gate_thresholds_match_registration():
    """GRID_GATE is imported from the sibling value_xs_dev — pin its numbers
    to unlock's own dev_select so drift in that file cannot silently change
    this experiment's bar."""
    g = json.loads((ROOT / "data" / "rebuild" / "gates.json").read_text())
    d = g["unlock_xs_t1"]["dev_select"]
    assert dev.GRID_GATE == {
        "net_sr_min": d["net_sr_min"],
        "placebo_p_max": d["placebo_p_max"],
        "dsr_min": d["dsr_min"],
        "delta_sr_vs_c1_min": d["delta_sr_vs_c1_min"],
        "delta_sr_vs_c2_min": d["delta_sr_vs_c2_min"],
    }


def test_verdict_semantics():
    ok = {"pass": True}
    bad = {"pass": False}
    assert dev.verdict_from_probes(ok, ok, ok) == "CONTINUE"
    for combo in ((bad, ok, ok), (ok, bad, ok), (ok, ok, bad)):
        assert dev.verdict_from_probes(*combo) == "NEGATIVE-at-probe"


def test_main_stop_contract_writes_probes_and_exits_2(tmp_path, monkeypatch):
    """A failing probe must produce probes.json + SystemExit(2) via main()."""
    monkeypatch.setattr(dev, "OUT_DIR", tmp_path)
    monkeypatch.setattr(dev, "_load_all", lambda: (None, {}, {}, [], {}, {}))
    monkeypatch.setattr(dev, "probe_p0_restatement",
                        lambda active_map: {"probe": "P0", "pass": False,
                                            "error": "synthetic"})
    monkeypatch.setattr(dev, "probe_p1_breadth",
                        lambda *a: {"probe": "P1", "pass": True})
    monkeypatch.setattr(dev, "probe_p2_event_study",
                        lambda *a: {"probe": "P2", "pass": True})
    ran = []
    monkeypatch.setattr(dev, "run_grid", lambda *a, **k: ran.append(1))
    with pytest.raises(SystemExit) as e:
        dev.main()
    assert e.value.code == 2
    assert ran == [], "grid must not run after a probe failure"
    out = json.loads((tmp_path / "probes.json").read_text())
    assert out["verdict"] == "NEGATIVE-at-probe"
    assert any(not p["pass"] for p in out["probes"])


def test_p0_missing_stamp_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(dev, "EMISSIONS_VINTAGE", tmp_path / "absent.json")
    r = dev.probe_p0_restatement({})
    assert r["pass"] is False
    assert "stamp" in r["error"]


def test_p0_divergence_growth_metric():
    idx = pd.date_range("2024-01-01", periods=400, freq="D", tz="UTC")
    ref = pd.Series(1000.0, index=idx)
    stable = pd.Series(1100.0, index=idx)   # constant 10% offset
    d = dev._divergence_growth(stable, ref)
    assert d is not None and abs(d["growth"]) < 1e-9   # offset != restatement
    drifting = pd.Series(1000.0 * pd.Series(range(400)).apply(
        lambda i: 1.0 + 0.001 * i).to_numpy(), index=idx)
    d2 = dev._divergence_growth(drifting, ref)
    assert d2["growth"] > 0.25   # divergence grows toward the present
    short = pd.Series(1.0, index=idx[:100])
    assert dev._divergence_growth(short, ref) is None


def test_p2_requires_negative_mean(monkeypatch):
    idx = pd.date_range("2020-06-01", "2021-06-01", freq="D", tz="UTC")
    close = pd.Series(100.0, index=idx)
    close.loc["2021-02-02":] = 90.0   # -10% after the cliff
    klines = {"AUSDT": pd.DataFrame({"close": close})}
    supply = pd.DataFrame({"AUSDT": pd.Series(1000.0, index=idx)})
    cliffs = {"AUSDT": pd.DataFrame(
        {"date": [pd.Timestamp("2021-02-01", tz="UTC")], "amount": [100.0]})}
    mats = {"supply": supply, "cliffs": cliffs}
    r = dev.probe_p2_event_study(mats, klines, idx, ["AUSDT"])
    assert r["n_events"] == 1 and r["pass"] is True
    # flip: price rises after the cliff -> wrong sign -> FAIL
    close2 = pd.Series(100.0, index=idx)
    close2.loc["2021-02-02":] = 110.0
    klines2 = {"AUSDT": pd.DataFrame({"close": close2})}
    r2 = dev.probe_p2_event_study(mats, klines2, idx, ["AUSDT"])
    assert r2["pass"] is False


def test_p2_ignores_small_cliffs_and_incomplete_windows():
    idx = pd.date_range("2020-06-01", "2021-06-01", freq="D", tz="UTC")
    klines = {"AUSDT": pd.DataFrame({"close": pd.Series(100.0, index=idx)})}
    supply = pd.DataFrame({"AUSDT": pd.Series(1000.0, index=idx)})
    cliffs = {"AUSDT": pd.DataFrame({
        "date": [pd.Timestamp("2021-02-01", tz="UTC"),      # 0.5% < floor
                 pd.Timestamp("2021-05-25", tz="UTC")],     # window past idx
        "amount": [5.0, 100.0]})}
    mats = {"supply": supply, "cliffs": cliffs}
    r = dev.probe_p2_event_study(mats, klines, idx, ["AUSDT"])
    # 2021-05-25 + 14d exceeds klines span -> incomplete -> dropped;
    # small cliff dropped by the 1% floor
    assert r["n_events"] == 0 and r["pass"] is False
