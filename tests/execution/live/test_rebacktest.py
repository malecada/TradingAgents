from pathlib import Path
import json
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest


def test_compute_weekly_report_writes_json(tmp_path):
    from tradingagents.execution.live import rebacktest

    fake_live = {"sharpe": 2.4, "return_pct": 0.04, "max_dd": 0.03,
                  "n_trades": 18, "win_rate": 0.61}
    fake_bt = {"sharpe": 2.6, "return_pct": 0.05, "max_dd": 0.025,
                "n_trades": 18, "win_rate": 0.67}

    with patch.object(rebacktest, "compute_live_metrics", return_value=fake_live), \
         patch.object(rebacktest, "compute_backtest_metrics", return_value=fake_bt):
        report_path = rebacktest.run_weekly_report(
            week_end="2026-W18",
            live_start_date="2026-04-29",
            live_end_date="2026-05-12",
            output_dir=tmp_path,
        )
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert data["week_end"] == "2026-W18"
    assert data["live"]["sharpe"] == 2.4
    assert data["backtest"]["sharpe"] == 2.6
    assert data["delta"]["sharpe"] == pytest.approx(-0.2)


def test_compute_backtest_metrics_uses_sys_executable():
    """Regression: the subprocess must launch via sys.executable, not bare
    "python" — under systemd the service user has no venv on PATH and bare
    "python" raised FileNotFoundError, killing ta-rebacktest.service."""
    from tradingagents.execution.live import rebacktest

    captured = {}

    def fake_run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        return SimpleNamespace(
            stdout="Sharpe : 2.50\nReturn : 12.0%\nMax DD : 3.0%\n",
            returncode=0,
        )

    with patch.object(rebacktest.subprocess, "run", side_effect=fake_run):
        rebacktest.compute_backtest_metrics("2026-05-13", "2026-05-20")

    assert captured["cmd"][0] == sys.executable
    assert captured["cmd"][0] != "python"


def test_verdict_diverging_when_sharpe_delta_large():
    from tradingagents.execution.live import rebacktest
    delta = {"sharpe": -0.7}
    assert rebacktest.classify_verdict(delta) == "DIVERGING"


def test_verdict_converging_when_close():
    from tradingagents.execution.live import rebacktest
    delta = {"sharpe": -0.1}
    assert rebacktest.classify_verdict(delta) == "CONVERGING"
