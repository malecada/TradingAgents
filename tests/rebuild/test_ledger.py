import json
from pathlib import Path

import pytest

from tradingagents.rebuild.ledger import (
    HOLDOUT_START, assert_dev_window, log_trial, trial_count,
)


def test_log_trial_appends_jsonl(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    row = log_trial(
        experiment="factor_floor",
        config={"kind": "tsmom", "lookback": 30},
        window=("2021-11-07", "2025-03-31"),
        metrics={"sharpe": 0.83, "max_drawdown": -0.06},
        ledger_path=ledger,
    )
    lines = ledger.read_text().strip().splitlines()
    assert len(lines) == 1
    loaded = json.loads(lines[0])
    assert loaded["experiment"] == "factor_floor"
    assert loaded["config"]["lookback"] == 30
    assert loaded["metrics"]["sharpe"] == 0.83
    assert loaded["window"] == ["2021-11-07", "2025-03-31"]
    assert "ts" in loaded and "git_commit" in loaded and "config_hash" in loaded
    assert row["config_hash"] == loaded["config_hash"]


def test_trial_count_total_and_per_experiment(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    for lb in (7, 14, 30):
        log_trial("factor_floor", {"kind": "tsmom", "lookback": lb},
                  ("2021-11-07", "2025-03-31"), {"sharpe": 0.1}, ledger_path=ledger)
    log_trial("axis_target", {"target_mode": "logret"},
              ("2021-11-07", "2025-03-31"), {"sharpe": 0.2}, ledger_path=ledger)
    assert trial_count(ledger_path=ledger) == 4
    assert trial_count(ledger_path=ledger, experiment="factor_floor") == 3


def test_log_trial_rejects_holdout_window(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    with pytest.raises(ValueError, match="holdout"):
        log_trial("factor_floor", {}, ("2021-11-07", "2026-06-01"),
                  {"sharpe": 9.9}, ledger_path=ledger)


def test_assert_dev_window():
    assert_dev_window("2025-03-31")  # ok
    with pytest.raises(ValueError, match="holdout"):
        assert_dev_window("2025-04-01")
    with pytest.raises(ValueError, match="holdout"):
        assert_dev_window(HOLDOUT_START)
    assert_dev_window("2026-07-01", allow_holdout=True)  # one-shot escape hatch
