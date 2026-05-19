# tests/strategies/test_sltp_wf.py
"""Tests for V5 MIX TP/SL walk-forward orchestrator."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="module")
def smoke_dir(tmp_path_factory):
    """Run the orchestrator in smoke mode ONCE, shared across all fast tests.

    Smoke runs 4 small sweeps (each loads coin OHLC) so it's ~20-40s. Sharing
    via module scope keeps default test runtime tolerable.
    """
    out_dir = tmp_path_factory.mktemp("wf_smoke")
    if (out_dir / "wf_summary.json").exists():
        shutil.rmtree(out_dir)
        out_dir = tmp_path_factory.mktemp("wf_smoke")
    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "v5_sltp_wf_orchestrator.py"),
            "--smoke",
            "--output-dir", str(out_dir),
        ],
        cwd=str(PROJECT_ROOT),
        check=True,
    )
    return out_dir


def test_orchestrator_smoke_produces_expected_files(smoke_dir):
    """Smoke run must create all 4 sweep subdirs + 3 root artifacts."""
    out_dir = smoke_dir

    # 4 sweep subdirs
    for sub in ("co_train", "co_test", "ib_train", "ib_test"):
        assert (out_dir / sub / "results.csv").exists(), f"missing {sub}/results.csv"
        assert (out_dir / sub / "summary.json").exists(), f"missing {sub}/summary.json"

    # 3 root artifacts
    assert (out_dir / "wf_results.csv").exists()
    assert (out_dir / "wf_summary.json").exists()
    assert (out_dir / "wf_report.md").exists()


def test_orchestrator_train_test_windows_do_not_overlap(smoke_dir):
    """wf_summary.json train and test windows must be disjoint (test starts
    strictly after train ends)."""
    out_dir = smoke_dir
    s = json.loads((out_dir / "wf_summary.json").read_text())
    train_end = pd.Timestamp(s["windows"]["train"]["end"])
    test_start = pd.Timestamp(s["windows"]["test"]["start"])
    assert test_start > train_end, (
        f"train_end={train_end} must be < test_start={test_start}"
    )


def test_orchestrator_per_engine_verdict_present(smoke_dir):
    """wf_summary.json must contain close_only.verdict and intrabar.verdict,
    each in {pass, fail}."""
    out_dir = smoke_dir
    s = json.loads((out_dir / "wf_summary.json").read_text())

    for engine in ("close_only", "intrabar"):
        assert engine in s, f"missing engine block: {engine}"
        block = s[engine]
        assert block["engine"] == engine
        assert "verdict" in block
        assert block["verdict"] in ("pass", "fail"), (
            f"{engine}.verdict must be pass|fail, got {block['verdict']}"
        )
        assert "train_best" in block
        for k in ("sl", "ee", "tp", "is_sr", "oos_sr", "oos_dd", "oos_calmar"):
            assert k in block["train_best"], f"missing train_best.{k}"
        assert "baseline_oos_sr" in block


def test_orchestrator_cell_join_matches_source_csvs(smoke_dir):
    """A sampled cell in wf_results.csv must match the same cell looked up
    in the per-window per-engine source CSVs."""
    out_dir = smoke_dir

    wf = pd.read_csv(out_dir / "wf_results.csv")
    # Pick the close-only baseline cell (always in smoke grid).
    co_rows = wf[
        (wf["engine"] == "close_only")
        & (wf["sl"] == 0.03) & (wf["ee"] == 0.015) & (wf["tp"] == 0.0)
    ]
    assert len(co_rows) == 1, "expected exactly one CO baseline cell row"
    co = co_rows.iloc[0]

    co_train = pd.read_csv(out_dir / "co_train" / "results.csv")
    co_train_port = co_train[
        (co_train["scope"] == "portfolio")
        & (co_train["sl"] == 0.03) & (co_train["ee"] == 0.015) & (co_train["tp"] == 0.0)
    ].iloc[0]
    co_test = pd.read_csv(out_dir / "co_test" / "results.csv")
    co_test_port = co_test[
        (co_test["scope"] == "portfolio")
        & (co_test["sl"] == 0.03) & (co_test["ee"] == 0.015) & (co_test["tp"] == 0.0)
    ].iloc[0]

    assert abs(co["is_sr"] - co_train_port["sharpe"]) < 1e-9, (
        f"is_sr mismatch: wf_results={co['is_sr']} vs co_train={co_train_port['sharpe']}"
    )
    assert abs(co["oos_sr"] - co_test_port["sharpe"]) < 1e-9, (
        f"oos_sr mismatch: wf_results={co['oos_sr']} vs co_test={co_test_port['sharpe']}"
    )


@pytest.mark.slow
def test_orchestrator_full_wf_completes_and_populates_verdicts(tmp_path):
    """Full WF (378 cells × 4 sweeps) must complete in <300s and produce a
    valid wf_summary.json with both engine verdicts populated."""
    out_dir = tmp_path / "wf_full"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    import time as _time
    t0 = _time.time()
    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "v5_sltp_wf_orchestrator.py"),
            "--output-dir", str(out_dir),
        ],
        cwd=str(PROJECT_ROOT),
        check=True,
        timeout=300,
    )
    elapsed = _time.time() - t0
    assert elapsed < 300, f"WF took {elapsed:.1f}s, expected <300s"

    s = json.loads((out_dir / "wf_summary.json").read_text())
    for engine in ("close_only", "intrabar"):
        assert s[engine]["verdict"] in ("pass", "fail")
        assert s[engine]["baseline_oos_sr"] is not None
        assert s[engine]["train_best"]["is_sr"] > 0  # full sweep has a positive winner
