import json
from pathlib import Path

import pandas as pd
import pytest

from scripts import audit_reeval_common as common


@pytest.fixture
def setup_run(tmp_path, monkeypatch):
    gate = {
        "development_window": ["2021-01-01", "2025-03-31"],
        "families": {
            "momentum": {"cells": [{"id": "a"}, {"id": "b"}]},
            "nlst4": {"cells": [{"id": "dex"}],
                      "settlement_fx_end_exclusive": "2025-04-15T09:20:00Z"},
        },
    }
    monkeypatch.setattr(common.registry, "get_experiment", lambda key: gate)
    monkeypatch.setattr(common.registry, "preflight", lambda *args: {"git_commit": "test"})
    rows = []
    monkeypatch.setattr(common.registry, "log_trial", lambda **kwargs: rows.append(kwargs))
    return tmp_path, rows


def test_refuses_existing_run_before_repeating_work(setup_run):
    root, _ = setup_run
    common.RunContext("momentum", root=root)
    with pytest.raises(FileExistsError):
        common.RunContext("momentum", root=root)


def test_committed_preflight_precedes_output_creation(setup_run, monkeypatch):
    root, _ = setup_run
    def fail(*args):
        raise RuntimeError("uncommitted executable")
    monkeypatch.setattr(common.registry, "preflight", fail)
    with pytest.raises(RuntimeError, match="uncommitted"):
        common.RunContext("momentum", root=root)
    assert not (root / "data/predlab" / common.KEY).exists()


def test_filtered_read_excludes_holdout_before_materialization(setup_run, monkeypatch):
    root, _ = setup_run
    path = root / "BTCUSDT.parquet"
    frame = pd.DataFrame({"close": [10., 999.]}, index=pd.to_datetime(
        ["2025-03-31", "2025-04-01"], utc=True))
    frame.to_parquet(path)
    calls = []
    original = pd.read_parquet
    def capture(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)
    monkeypatch.setattr(pd, "read_parquet", capture)
    ctx = common.RunContext("momentum", root=root)
    got = ctx.read_market(path)
    assert got.close.tolist() == [10.]
    assert calls[0]["filters"]
    with pytest.raises(ValueError, match="bound"):
        ctx.read_market(path, end_exclusive="2025-04-02")


def test_settlement_exception_is_limited_to_nlst4_eth(setup_run):
    root, _ = setup_run
    path = root / "ETHUSDT.parquet"
    pd.DataFrame({"close": [10., 20.]}, index=pd.to_datetime(
        ["2025-04-15T09:15Z", "2025-04-15T09:20Z"], utc=True)).to_parquet(path)
    ctx = common.RunContext("nlst4", root=root)
    got = ctx.read_market(path, end_exclusive="2025-04-15T09:20:00Z")
    assert got.close.tolist() == [10.]
    with pytest.raises(ValueError, match="bound"):
        ctx.read_market(path, end_exclusive="2025-04-15T09:25:00Z")


def test_changed_input_cannot_produce_completed_evidence(setup_run):
    root, rows = setup_run
    source = root / "source.json"
    source.write_text("original")
    ctx = common.RunContext("momentum", root=root)
    ctx.track(source)
    source.write_text("changed")
    cells = [{"id": x, "config": {}, "metrics": {}} for x in ("a", "b")]
    with pytest.raises(RuntimeError, match="changed"):
        ctx.finish({}, cells)
    assert not (ctx.output_dir / "result.json").exists()
    assert not rows


def test_unregistered_input_root_cannot_replace_frozen_sources(setup_run):
    root, _ = setup_run
    path = root / "alternative.json"
    path.write_text("not a registered source")
    ctx = common.RunContext("momentum", root=root)
    ctx.gate["source_roots"] = [str(root / "allowed")]
    with pytest.raises(ValueError, match="registered source"):
        ctx.track(path)


def test_unserializable_result_cannot_partially_append_ledger(setup_run):
    root, rows = setup_run
    ctx = common.RunContext("momentum", root=root)
    cells = [{"id": x, "config": {}, "metrics": {}} for x in ("a", "b")]
    with pytest.raises(TypeError):
        ctx.finish({"unsupported": object()}, cells)
    assert rows == []
    assert not (ctx.output_dir / "result.json").exists()


@pytest.mark.parametrize("ids", [["a"], ["a", "a"], ["a", "b", "c"]])
def test_missing_duplicate_or_extra_cells_cannot_shrink_denominator(setup_run, ids):
    root, rows = setup_run
    ctx = common.RunContext("momentum", root=root)
    with pytest.raises(ValueError, match="cells"):
        ctx.finish({}, [{"id": x, "config": {}, "metrics": {}} for x in ids])
    assert not rows


def test_finish_preserves_blocked_cells_and_safe_parquet_attributes(setup_run):
    root, rows = setup_run
    ctx = common.RunContext("momentum", root=root)
    frame = pd.DataFrame({"net": [0., .1]})
    frame.attrs["book_inputs"] = pd.DataFrame({"unserializable": [1]})
    ctx.write_frame("daily.parquet", frame)
    cells = [{"id": "a", "config": {}, "metrics": {"status": "blocked", "sr": float("nan")}},
             {"id": "b", "config": {}, "metrics": {"status": "fail", "sr": .1}}]
    ctx.finish({"status": "completed_with_blocked_cells"}, cells)
    result = json.loads((ctx.output_dir / "result.json").read_text())
    assert len(result["cells"]) == len(rows) == 2
    assert result["cells"][0]["metrics"]["sr"] is None
    assert result["input_unchanged_after_run"]
    assert "daily.parquet" in result["output_sha256"]
    assert frame.attrs  # writing the archive must not mutate caller state
