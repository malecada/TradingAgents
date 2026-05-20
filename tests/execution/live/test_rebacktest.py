import json
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest


def _seed_journal(db_path):
    """Two portfolio snapshots so compute_live_metrics returns real numbers."""
    from tradingagents.execution.live.journal import Journal
    j = Journal(str(db_path))
    j.log_cycle_start("2026-05-13", git_sha="abc")
    for day, val in [("2026-05-13", 10000), ("2026-05-20", 10300)]:
        j._conn.execute(
            "INSERT INTO portfolio_snapshots (cycle_id, ts, total_value, "
            "usdt_balance, position_qty_per_coin, unrealized_pnl) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (day, f"{day}T00:05:00+00:00", val, val, "{}", 0),
        )
    j._conn.commit()
    j.close()


def test_run_weekly_parity_parses_verdict(tmp_path, monkeypatch):
    """run_weekly_parity captures the parity script's VERDICT line."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    _seed_journal(tmp_path / "trade_journal.db")
    from tradingagents.execution.live import rebacktest

    captured = {}

    def fake_run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        return SimpleNamespace(
            stdout="...\nVERDICT: PASS\nREPORT: /tmp/sandbox/parity_report.md\n",
            stderr="", returncode=0,
        )

    with patch.object(rebacktest.subprocess, "run", side_effect=fake_run):
        out = rebacktest.run_weekly_parity(
            week_end="2026-W21",
            live_start_date="2026-05-13", live_end_date="2026-05-20",
            output_dir=tmp_path / "reports",
        )

    data = json.loads(out.read_text())
    assert data["week_end"] == "2026-W21"
    assert data["verdict"] == "PASS"
    assert data["parity_report"] == "/tmp/sandbox/parity_report.md"
    assert data["live"]["return_pct"] == pytest.approx(0.03)


def test_run_weekly_parity_uses_sys_executable_and_cycle_ids(tmp_path, monkeypatch):
    """Subprocess launches via sys.executable; ISO dates → YYYYMMDD cycles."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from tradingagents.execution.live import rebacktest

    captured = {}

    def fake_run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        return SimpleNamespace(stdout="VERDICT: PASS\n", stderr="", returncode=0)

    with patch.object(rebacktest.subprocess, "run", side_effect=fake_run):
        rebacktest.run_weekly_parity(
            week_end="2026-W21",
            live_start_date="2026-05-13", live_end_date="2026-05-20",
            output_dir=tmp_path / "reports",
        )

    cmd = captured["cmd"]
    assert cmd[0] == sys.executable
    assert cmd[0] != "python"
    assert "parity_refetch_and_replay.py" in cmd[1]
    assert "--start-cycle" in cmd and "20260513" in cmd
    assert "--end-cycle" in cmd and "20260520" in cmd


def test_run_weekly_parity_writes_error_summary_on_failure(tmp_path, monkeypatch):
    """A failed parity subprocess still produces a JSON summary with ERROR."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from tradingagents.execution.live import rebacktest

    err = rebacktest.subprocess.CalledProcessError(
        returncode=1, cmd=["x"], output="partial out", stderr="boom",
    )
    with patch.object(rebacktest.subprocess, "run", side_effect=err):
        out = rebacktest.run_weekly_parity(
            week_end="2026-W21",
            live_start_date="2026-05-13", live_end_date="2026-05-20",
            output_dir=tmp_path / "reports",
        )

    data = json.loads(out.read_text())
    assert data["verdict"] == "ERROR"
    assert "boom" in data["stdout_tail"]
