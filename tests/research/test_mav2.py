"""Consolidation layer of the second multi-agent framework: registry, pin check, replay comparison."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest

from tradingagents.mav2 import pins, registry, replay
from tradingagents.mav2.registry import Run

ROOT = registry.ROOT


# --- guard on the real checkout ----------------------------------------------------------------------------------

def test_no_pinned_file_changed():
    """Every file a receipt pins keeps its bytes; edit by adding new files instead (see docs/multiagent_v2)."""
    reports = pins.check_all(ROOT)
    assert {r.label for r in reports} >= {"V1", "V1b", "V2", "V3", "V4", "V5"}
    assert {r.label: r.drifted for r in reports if r.drifted} == {}


def test_expected_drift_is_still_drift():
    """A documented exception that no longer differs from its pin should be removed from EXPECTED_DRIFT."""
    for label, files in pins.EXPECTED_DRIFT.items():
        report = pins.check_run(registry.get(label), ROOT)
        assert sorted(report.expected) == sorted(files), label


def test_status_reads_every_completed_verdict():
    rows = {r["label"]: r for r in registry.status(ROOT)}
    assert [r.label for r in registry.RUNS] == list(rows)
    for label in replay.ADAPTERS:
        row = rows[label]
        assert row["receipt"] == "complete" and row["verdict"] in ("PASS", "FAIL")
        assert isinstance(row["value"], float) and math.isfinite(row["value"])
        assert row["sample"]
    assert rows["V1"]["receipt"] == "failed" and rows["V1"]["verdict"] == "interrupted"
    assert rows["V3"]["cost_usd"] == rows["V4"]["cost_usd"] == 0.0


def test_charter_paths_exist():
    for run in registry.RUNS:
        assert (ROOT / run.charter()).is_file(), run.label
        assert (ROOT / run.registration()).is_file(), run.label


def test_get_unknown():
    assert registry.get("V2").run_id == "llm-v2c2-reader-dev-run-20261112"
    with pytest.raises(KeyError):
        registry.get("V9")


# --- pin check on a synthetic checkout ---------------------------------------------------------------------------

def _fake_run(tmp_path: Path, files: dict[str, bytes], inputs: dict[str, bytes] | None = None) -> Run:
    for rel, data in {**files, **{f"in/{n}": d for n, d in (inputs or {}).items()}}.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(data)
    sha = {rel: hashlib.sha256(data).hexdigest() for rel, data in files.items()}
    claim = {"registration": "reg/gates.json", "registration_sha256": None, "experiment_id": "x",
             "experiment": {"source_files": sha, "charter": {"path": "charter.md", "sha256": sha.get("charter.md")},
                            "inputs": {name: {"path": f"in/{name}", "sha256": hashlib.sha256(data).hexdigest()}
                                       for name, data in (inputs or {}).items()}}}
    run = Run("T1", "fake-run", None, "synthetic")
    run.run_dir(tmp_path).mkdir(parents=True)
    (run.run_dir(tmp_path) / "claim.json").write_text(json.dumps(claim))
    return run


def test_pin_check_detects_change_and_removal(tmp_path):
    run = _fake_run(tmp_path, {"pkg/a.py": b"a = 1\n", "pkg/b.py": b"b = 2\n", "charter.md": b"# c\n"})
    assert pins.check_run(run, tmp_path).ok
    (tmp_path / "pkg/a.py").write_bytes(b"a = 2\n")
    (tmp_path / "pkg/b.py").unlink()
    report = pins.check_run(run, tmp_path)
    assert not report.ok and report.drifted == ["pkg/a.py", "pkg/b.py"] and report.pinned == 3


def test_registered_reader_checks_bytes(tmp_path):
    run = _fake_run(tmp_path, {"charter.md": b"# c\n"}, inputs={"cards": b"one"})
    read = replay.registered_reader(run, tmp_path)
    assert read("cards") == b"one"
    with pytest.raises(replay.ReplayError, match="unregistered"):
        read("other")
    (tmp_path / "in/cards").write_bytes(b"two")
    with pytest.raises(replay.ReplayError, match="differs"):
        read("cards")
    (tmp_path / "in/cards").unlink()
    assert replay.missing_inputs(run, tmp_path) == ["in/cards"]


# --- comparison ----------------------------------------------------------------------------------------------------

def test_diff_tolerates_float_noise_only():
    stored = {"t": 1.0, "n": 104, "nan": float("nan"), "by_year": {"2023": -0.02}, "rows": [1, 2]}
    assert replay.diff(stored, {"t": 1.0 + 1e-13, "n": 104, "nan": float("nan"), "by_year": {"2023": -0.02}, "rows": [1, 2]}) == []
    out = replay.diff(stored, {"t": 1.001, "n": 105, "nan": 0.0, "by_year": {}, "rows": [1]})
    assert len(out) == 5
    assert any(".by_year.2023: only in stored" in d for d in out)
    assert any("length 2 != 1" in d for d in out)


def test_diff_bool_is_not_number():
    assert replay.diff({"pass": True}, {"pass": 1}) != []


def test_replay_rejects_runs_without_verdict():
    for label in ("C0", "V1"):
        with pytest.raises(replay.ReplayError):
            replay.replay(label)


# --- full replay on the real data (data/ is synced separately; skipped when absent) -------------------------------

@pytest.mark.slow
@pytest.mark.parametrize("label", sorted(replay.ADAPTERS))
def test_replay_reproduces_stored_outputs(label):
    run = registry.get(label)
    if replay.missing_inputs(run, ROOT):
        pytest.skip(f"{label}: registered inputs not on this machine")
    result = replay.replay(label, ROOT)
    assert result.verdict_replay == result.verdict_stored
    assert {k: v for k, v in result.compared.items() if v} == {}
