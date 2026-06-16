# tradingagents/monitor/adhoc/store.py
"""Read-write SQLite store for ad-hoc prediction runs.

Isolated from the trade journals (its own db file). The worker writes; the
API reads. One row per run in `runs`, one row per partial/final in `outputs`.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY, created_ts REAL, coin TEXT, date TEXT, strategy TEXT,
  analysts_json TEXT, model TEXT, status TEXT, stage TEXT, progress REAL,
  error_msg TEXT, started_ts REAL, finished_ts REAL, est_cost REAL, heartbeat_ts REAL
);
CREATE TABLE IF NOT EXISTS outputs (
  run_id TEXT, key TEXT, label TEXT, kind TEXT, content TEXT, ordinal INTEGER, ts REAL
);
CREATE INDEX IF NOT EXISTS idx_outputs_run ON outputs(run_id, ordinal);
"""

_RUN_COLS = ("run_id", "created_ts", "coin", "date", "strategy", "analysts_json",
             "model", "status", "stage", "progress", "error_msg", "started_ts",
             "finished_ts", "est_cost", "heartbeat_ts")


def db_path() -> Path:
    data_dir = Path(os.environ.get("QUANT_DATA_DIR", os.environ.get("DATA_DIR", "data")))
    out = data_dir / "adhoc"
    out.mkdir(parents=True, exist_ok=True)
    return out / "adhoc_runs.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path()))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _run_to_dict(row: sqlite3.Row) -> dict:
    d = {k: row[k] for k in _RUN_COLS}
    d["analysts"] = json.loads(d.pop("analysts_json") or "[]")
    return d


def create_run(conn, *, coin, date, strategy, analysts, model, est_cost=0.0) -> str:
    run_id = uuid.uuid4().hex[:12]
    conn.execute(
        "INSERT INTO runs (run_id, created_ts, coin, date, strategy, analysts_json, "
        "model, status, stage, progress, est_cost) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', 'queued', 0.0, ?)",
        (run_id, time.time(), coin, date, strategy, json.dumps(analysts), model, est_cost),
    )
    conn.commit()
    return run_id


def set_status(conn, run_id, status, **fields) -> None:
    cols = ["status = ?"]
    vals = [status]
    for k, v in fields.items():
        cols.append(f"{k} = ?")
        vals.append(v)
    vals.append(run_id)
    conn.execute(f"UPDATE runs SET {', '.join(cols)} WHERE run_id = ?", vals)
    conn.commit()


def heartbeat(conn, run_id, *, stage, progress) -> None:
    conn.execute(
        "UPDATE runs SET stage = ?, progress = ?, heartbeat_ts = ? WHERE run_id = ?",
        (stage, progress, time.time(), run_id),
    )
    conn.commit()


def add_output(conn, run_id, *, key, label, kind, content, ordinal) -> None:
    stored = json.dumps(content) if kind == "json" else str(content)
    conn.execute(
        "INSERT INTO outputs (run_id, key, label, kind, content, ordinal, ts) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (run_id, key, label, kind, stored, ordinal, time.time()),
    )
    conn.commit()


def get_run(conn, run_id) -> dict | None:
    row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    return _run_to_dict(row) if row else None


def get_outputs(conn, run_id) -> list[dict]:
    rows = conn.execute(
        "SELECT key, label, kind, content, ordinal, ts FROM outputs "
        "WHERE run_id = ? ORDER BY ordinal", (run_id,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        if d["kind"] == "json":
            d["content"] = json.loads(d["content"])
        out.append(d)
    return out


def list_runs(conn, limit=50) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM runs ORDER BY created_ts DESC LIMIT ?", (limit,)).fetchall()
    return [_run_to_dict(r) for r in rows]


def active_run(conn) -> dict | None:
    row = conn.execute(
        "SELECT * FROM runs WHERE status IN ('queued', 'running') "
        "ORDER BY created_ts DESC LIMIT 1").fetchone()
    return _run_to_dict(row) if row else None
