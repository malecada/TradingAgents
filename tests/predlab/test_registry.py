from __future__ import annotations

import json

import pytest

from tradingagents.predlab import registry


def test_assert_dev_window_blocks_holdout(monkeypatch, tmp_path):
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path))
    registry.assert_dev_window("2025-03-31")  # ok
    with pytest.raises(RuntimeError):
        registry.assert_dev_window("2025-04-01")
    with pytest.raises(RuntimeError):
        registry.assert_dev_window("2026-01-01")
    registry.assert_dev_window("2026-01-01", allow_holdout=True)  # explicit only


def test_log_trial_appends_hash_and_commit(monkeypatch, tmp_path):
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path))
    row = registry.log_trial(
        "predlab_p1_classical", "BTCUSDT|24h|T3_rv", "har_levels",
        {"a": 1}, ("2021-01-01", "2025-03-31"), {"qlike": 0.31},
    )
    assert len(row["config_hash"]) == 12
    assert row["git_commit"]
    assert row["experiment"] == "predlab_p1_classical"
    registry.log_trial("predlab_p1_classical", "c", "m", {"a": 2}, ("x", "y"), {})
    assert registry.trial_count() == 2
    assert registry.trial_count("predlab_p1_classical") == 2
    assert registry.trial_count("other") == 0
    # append-only jsonl, one object per line
    lines = (tmp_path / "predlab" / "trial_ledger.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2 and all(json.loads(ln) for ln in lines)


def test_same_config_same_hash(monkeypatch, tmp_path):
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path))
    r1 = registry.log_trial("e", "c", "m", {"b": 2, "a": 1}, ("x", "y"), {})
    r2 = registry.log_trial("e", "c2", "m2", {"a": 1, "b": 2}, ("x", "y"), {})
    assert r1["config_hash"] == r2["config_hash"]  # canonical json, key order irrelevant
    assert registry.trial_count() == 1  # unique hashes


def test_load_gates_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path))
    (tmp_path / "predlab").mkdir(parents=True)
    (tmp_path / "predlab" / "gates.json").write_text(json.dumps({"k": {"x": 1}}))
    assert registry.load_gates() == {"k": {"x": 1}}
    assert registry.get_experiment("k") == {"x": 1}
    with pytest.raises(KeyError):
        registry.get_experiment("missing")
