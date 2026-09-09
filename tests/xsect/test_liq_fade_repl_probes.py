"""Probe plumbing for liq_fade_r1. The completeness guard matters most: a
partial fetch must never produce a smoke:false probes.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def test_event_forward_sum_aligns_to_trigger_bar():
    """sum(R[t+1..t+H]) at the triggering bar t. Non-constant returns so a
    shift(-H) vs shift(-H+1) mutation is caught."""
    from liq_fade_repl import event_forward_sum
    idx = pd.date_range("2021-01-01", periods=10, freq="1h", tz="UTC")
    R = pd.DataFrame({"A": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]}, index=idx)
    trig = pd.DataFrame({"A": [False] * 10}, index=idx)
    trig.iloc[2, 0] = True
    vals = event_forward_sum(R, trig, H=3)
    # trigger at row 2 -> R[3] + R[4] + R[5] = 3 + 4 + 5 = 12
    assert vals.tolist() == [12.0]


def test_event_forward_sum_drops_truncated_windows():
    from liq_fade_repl import event_forward_sum
    idx = pd.date_range("2021-01-01", periods=5, freq="1h", tz="UTC")
    R = pd.DataFrame({"A": [1.0] * 5}, index=idx)
    trig = pd.DataFrame({"A": [False, False, False, True, False]}, index=idx)
    vals = event_forward_sum(R, trig, H=3)   # only 1 bar of forward data
    assert len(vals) == 0


def test_completeness_guard_rejects_partial_universe(tmp_path, monkeypatch):
    import liq_fade_repl as m
    syms = tmp_path / "syms.txt"
    syms.write_text("AAAUSDT\nBBBUSDT\nCCCUSDT\n")
    klines = tmp_path / "klines_1h"
    klines.mkdir()
    (klines / "AAAUSDT.parquet").touch()
    monkeypatch.setattr(m, "SYMBOLS_FILE", syms)
    monkeypatch.setattr(m, "KLINES_1H_DIR", klines)
    with pytest.raises(RuntimeError, match="2/3 symbols"):
        m.assert_band_data_complete()


def test_probes_guard_rejects_smoke_verdict(tmp_path):
    import liq_fade_repl as m
    p = tmp_path / "probes.json"
    p.write_text(json.dumps({"smoke": True, "p3": {"pass": True},
                             "p1": {"pass": True}, "p2": {"pass": True}}))
    with pytest.raises(RuntimeError, match="not a passing registered verdict"):
        m.assert_probes_passed(p)


def test_probes_guard_rejects_failed_p3(tmp_path):
    import liq_fade_repl as m
    p = tmp_path / "probes.json"
    p.write_text(json.dumps({"smoke": False, "p3": {"pass": False},
                             "p1": {"pass": True}, "p2": {"pass": True}}))
    with pytest.raises(RuntimeError, match="not a passing registered verdict"):
        m.assert_probes_passed(p)


def test_probes_guard_accepts_full_pass(tmp_path):
    import liq_fade_repl as m
    p = tmp_path / "probes.json"
    payload = {"smoke": False, "p3": {"pass": True}, "p0": {"pass": True},
               "p1": {"pass": True}, "p2": {"pass": True}}
    p.write_text(json.dumps(payload))
    assert m.assert_probes_passed(p) == payload


def test_probes_guard_rejects_missing_file(tmp_path):
    import liq_fade_repl as m
    with pytest.raises(RuntimeError, match="not found"):
        m.assert_probes_passed(tmp_path / "nope.json")


@pytest.mark.parametrize("p3_pass,p1_pass,p2_pass,expected_stop", [
    (True, True, True, False),      # all pass -> no stop
    (False, True, True, True),      # P3 fails -> stop
    (True, False, True, True),      # P1 fails -> stop
    (True, True, False, True),      # P2 fails -> stop
    (None, True, True, True),       # P3 indeterminate -> STOP (not silently pass-through)
    (True, None, True, True),       # P1 indeterminate -> STOP
    (True, True, None, True),       # P2 indeterminate (e.g. no dev triggers) -> STOP
])
def test_probes_should_stop_treats_indeterminate_as_stop(p3_pass, p1_pass, p2_pass, expected_stop):
    """A probe returning pass=None (indeterminate) must STOP, not silently
    continue as if it passed. `assert_probes_passed` already refuses a
    primary run on None, but the --probes-only CLI's own STOP/exit-code
    reporting must agree, rather than checking `pass is False` only (which
    treats None the same as True)."""
    from liq_fade_repl import probes_should_stop
    p3, p1, p2 = {"pass": p3_pass}, {"pass": p1_pass}, {"pass": p2_pass}
    assert probes_should_stop(p3, p1, p2) is expected_stop


def test_probe_p2_bounds_both_dev_lo_and_dev_hi(monkeypatch):
    """probe_p2's row_sel must bound BOTH dev_lo and dev_hi, matching
    probe_p3 -- otherwise a trigger dated after the dev window would still be
    counted if it happened to fall within the panel's loaded index. Harmless
    in production today (load_hourly_panel always caps at DEV[1]), but this
    is an implicit invariant in a holdout-discipline codebase, so it is
    tested directly rather than relying on the loader to paper over it."""
    import liq_fade_repl as m
    idx = pd.date_range("2021-01-01", periods=10, freq="1D", tz="UTC")
    close = pd.DataFrame({"A": [100.0] * 10}, index=idx)
    qvol = pd.DataFrame({"A": [1.0] * 10}, index=idx)
    mask = pd.DataFrame({"A": [True] * 10}, index=idx)

    trig_full = pd.DataFrame({"A": [False] * 10}, index=idx)
    trig_full.iloc[2, 0] = True   # 2021-01-03 -- inside the dev window
    trig_full.iloc[8, 0] = True   # 2021-01-09 -- after dev_hi, must be excluded

    monkeypatch.setattr(m, "cascade_triggers", lambda close, qvol, thr: trig_full)
    monkeypatch.setattr(m, "DEV", ("2021-01-01", "2021-01-03"))

    p2 = m.probe_p2(close, qvol, mask)
    assert p2["n_events"] == 1, (
        "trigger dated after dev_hi leaked into the count -- probe_p2 must "
        "bound row_sel at both dev_lo and dev_hi")
