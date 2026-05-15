"""V5 schema migration tests."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from tradingagents.execution.live.journal import Journal


def _v1_schema_sqls() -> list[str]:
    """The v1 schema columns (pre-V5). Used to seed an old-shape DB."""
    return [
        """CREATE TABLE cycles (cycle_id TEXT PRIMARY KEY, start_ts TEXT, end_ts TEXT,
            status TEXT, n_trades INTEGER, notes TEXT)""",
        """CREATE TABLE retrains (retrain_id TEXT PRIMARY KEY, cycle_id TEXT,
            checkpoint_path TEXT, checkpoint_sha TEXT, n_train_rows INTEGER,
            train_window_start TEXT, train_dir_acc REAL, status TEXT)""",
        """CREATE TABLE predictions (cycle_id TEXT, coin TEXT, horizon INTEGER,
            prediction REAL, ref_price REAL)""",
    ]


def test_migrate_adds_v5_columns(tmp_path: Path) -> None:
    db = tmp_path / "j.db"
    conn = sqlite3.connect(db)
    for sql in _v1_schema_sqls():
        conn.execute(sql)
    conn.commit()
    conn.close()

    j = Journal(str(db))
    j.migrate()

    cols = lambda t: {r[1] for r in sqlite3.connect(db).execute(f"PRAGMA table_info({t})").fetchall()}
    assert "bundle_route" in cols("predictions")
    assert "routes" in cols("retrains")
    assert "critical_data_fail_sources" in cols("cycles")
    assert "supplementary_stale_sources" in cols("cycles")


def test_migrate_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "j.db"
    conn = sqlite3.connect(db)
    for sql in _v1_schema_sqls():
        conn.execute(sql)
    conn.commit()
    conn.close()

    j = Journal(str(db))
    j.migrate()
    j.migrate()  # second call must not raise


def test_v1_rows_backward_compatible(tmp_path: Path) -> None:
    db = tmp_path / "j.db"
    conn = sqlite3.connect(db)
    for sql in _v1_schema_sqls():
        conn.execute(sql)
    conn.execute("INSERT INTO predictions (cycle_id, coin, horizon, prediction, ref_price) "
                 "VALUES ('20260101', 'bitcoin', 7, 50000.0, 49500.0)")
    conn.commit()
    conn.close()

    Journal(str(db)).migrate()

    row = sqlite3.connect(db).execute(
        "SELECT cycle_id, coin, horizon, prediction, ref_price, bundle_route "
        "FROM predictions WHERE cycle_id='20260101'"
    ).fetchone()
    assert row == ("20260101", "bitcoin", 7, 50000.0, 49500.0, None)
