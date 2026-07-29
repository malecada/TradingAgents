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
