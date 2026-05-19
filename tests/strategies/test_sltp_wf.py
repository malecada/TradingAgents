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
