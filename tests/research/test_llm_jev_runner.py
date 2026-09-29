"""Runner guards and registration structure (no network, no run claims)."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import llm_jev_event_p0 as p0  # noqa: E402
import llm_jev_register as reg  # noqa: E402
from llm_jev_client import JevError  # noqa: E402


def test_label_refuses_without_pinned_model(monkeypatch, tmp_path):
    monkeypatch.setattr(p0, "PINNED_MODEL", None)
    with pytest.raises(SystemExit, match="PINNED_MODEL"):
        p0.run_label(tmp_path, "gates.json", "0" * 40)


class RecordingClient:
    def __init__(self):
        self.calls = []

    def decide(self, state, questions):
        self.calls.append((state, questions))
        return {}


def test_preflight_covers_worst_case_shapes():
    from llm_jev_smoke import preflight

    client = RecordingClient()
    preflight(client)
    assert len(client.calls) == 2

    state1, questions1 = client.calls[0]
    assert "asset" in questions1 and len(questions1["asset"]["criteria"]) == 31
    assert len(state1["content"]) == 4000
    assert any(ord(ch) > 127 for ch in state1["content"])

    state2, questions2 = client.calls[1]
    assert "asset" not in questions2
    assert sum(1 for k in questions2 if k.startswith("ev_")) == 6


def test_label_preflight_failure_creates_no_claim(monkeypatch, tmp_path):
    monkeypatch.setattr(p0, "PINNED_MODEL", "m")
    monkeypatch.setattr(p0, "load_api_key", lambda root: "k")
    monkeypatch.setattr(p0, "preflight", lambda client: (_ for _ in ()).throw(JevError("boom")))
    with pytest.raises(SystemExit, match="preflight failed"):
        p0.run_label(tmp_path, "gates.json", "0" * 40)
    assert not (tmp_path / "research_runs").exists()


def test_render_refuses_overwrite(tmp_path):
    outputs = tmp_path / "research_runs" / p0.E1 / "outputs"
    outputs.mkdir(parents=True)
    (outputs / "review_sheet.json").write_text(json.dumps({"rows": []}))
    first = p0.run_render(tmp_path)
    assert first.read_text().startswith("# Jev P0 blind review")
    with pytest.raises(SystemExit, match="refusing"):
        p0.run_render(tmp_path)


def test_build_e1_structure(monkeypatch):
    monkeypatch.setattr(reg, "CHARTER",
                        "docs/superpowers/specs/2026-09-29-llm-jev-event-probe-design.md")
    spec = reg.build_e1(ROOT)
    assert spec["schema_version"] == 1 and spec["program_id"] == "llm-jev-event-2026-09-29"
    family = spec["families"][reg.FAMILY_KEY]
    assert family["attempt_budget"] == 12 and family["prior_attempts"] == 2
    exp = spec["experiments"][p0.E1]
    assert exp["parent"] is None and exp["stage"] == "development"
    assert exp["reuse"] == "exploratory" and exp["selection"] is None
    assert exp["outputs"] == list(p0.E1_OUTPUTS) and exp["cells"] == list(p0.E1_CELLS)
    assert set(exp["source_files"]) == set(reg.SOURCE_FILES)
    assert len(exp["inputs"]) == 12
    for item in exp["inputs"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) and item["dataset"] == reg.DATASET
        assert item["path"].startswith("data/llm_event_xs/")
    assert exp["windows"] == [reg.WINDOW]
    assert all(e.endswith(".json") for e in exp["outputs"])


def test_write_refuses_overwrite(tmp_path):
    reg.write(tmp_path, "gates.json", {"a": 1})
    with pytest.raises(SystemExit, match="never overwritten"):
        reg.write(tmp_path, "gates.json", {"a": 2})
