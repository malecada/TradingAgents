import os
import sqlite3
from datetime import datetime, timezone

import pytest


@pytest.fixture
def journal(tmp_path):
    from tradingagents.execution.live.journal import Journal
    db_path = tmp_path / "j.db"
    j = Journal(str(db_path))
    yield j
    j.close()


def test_creates_all_tables(journal):
    cur = journal._conn.cursor()
    rows = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    names = {r[0] for r in rows}
    assert {"cycles", "predictions", "sizing", "risk_checks", "trades",
            "portfolio_snapshots", "feature_snapshots",
            "model_artifacts", "shadow_decisions"}.issubset(names)


def test_log_cycle_round_trip(journal):
    journal.log_cycle_start("2026-05-12", git_sha="abc1234")
    journal.log_cycle_end("2026-05-12", status="ok")

    rows = journal._conn.execute("SELECT cycle_id, status FROM cycles").fetchall()
    assert rows == [("2026-05-12", "ok")]


def test_log_prediction_round_trip(journal):
    journal.log_cycle_start("2026-05-12", git_sha="abc")
    journal.log_prediction(cycle_id="2026-05-12", coin="BTC",
                            horizon=7, model_path_sha="sha7",
                            pred_value=70000.0, ref_price=68000.0,
                            signal_h7=1, signal_h14=1, consensus_signal=1)
    rows = journal._conn.execute(
        "SELECT coin, horizon, pred_value, consensus_signal FROM predictions"
    ).fetchall()
    assert rows == [("BTC", 7, 70000.0, 1)]


def test_log_risk_check_passed_and_failed(journal):
    journal.log_cycle_start("2026-05-12", git_sha="abc")
    journal.log_risk_check("2026-05-12", "BTC", "leverage_cap", True, 2.0, 3.0, "OK")
    journal.log_risk_check("2026-05-12", "BTC", "daily_loss", False, -0.20, -0.15, "kill")
    rows = journal._conn.execute(
        "SELECT check_name, passed FROM risk_checks ORDER BY id"
    ).fetchall()
    assert rows == [("leverage_cap", 1), ("daily_loss", 0)]


def test_idempotent_cycle_start(journal):
    journal.log_cycle_start("2026-05-12", git_sha="abc")
    journal.log_cycle_start("2026-05-12", git_sha="abc")  # safe re-call
    rows = journal._conn.execute("SELECT COUNT(*) FROM cycles").fetchone()
    assert rows[0] == 1
