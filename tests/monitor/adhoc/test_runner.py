from __future__ import annotations

import time

import pytest

from tradingagents.monitor.adhoc import runner, store


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("QUANT_DATA_DIR", raising=False)
    c = store.connect()
    yield c
    c.close()


def test_can_start_when_idle(conn):
    ok, blocker = runner.can_start(conn)
    assert ok is True and blocker is None


def test_blocked_when_active(conn):
    rid = store.create_run(conn, coin="b", date="d", strategy="quant",
                           analysts=[], model="m")
    store.set_status(conn, rid, "running", heartbeat_ts=time.time())
    ok, blocker = runner.can_start(conn)
    assert ok is False and blocker == rid


def test_stale_running_reaped(conn):
    rid = store.create_run(conn, coin="b", date="d", strategy="quant",
                           analysts=[], model="m")
    store.set_status(conn, rid, "running",
                     heartbeat_ts=time.time() - runner.STALE_SECONDS - 1)
    ok, blocker = runner.can_start(conn)
    assert ok is True and blocker is None
    assert store.get_run(conn, rid)["status"] == "error"


def test_stale_queued_reaped(conn):
    # a queued run whose worker never started (created long ago, no heartbeat)
    rid = store.create_run(conn, coin="b", date="d", strategy="quant",
                           analysts=[], model="m")
    # backdate created_ts beyond the stale window
    conn.execute("UPDATE runs SET created_ts = ? WHERE run_id = ?",
                 (time.time() - runner.STALE_SECONDS - 1, rid))
    conn.commit()
    ok, blocker = runner.can_start(conn)
    assert ok is True and blocker is None
    assert store.get_run(conn, rid)["status"] == "error"


def test_stale_running_without_heartbeat_reaped(conn):
    # running but heartbeat_ts never written; falls back to started_ts anchor
    rid = store.create_run(conn, coin="b", date="d", strategy="quant",
                           analysts=[], model="m")
    store.set_status(conn, rid, "running",
                     started_ts=time.time() - runner.STALE_SECONDS - 1)
    ok, blocker = runner.can_start(conn)
    assert ok is True and blocker is None
    assert store.get_run(conn, rid)["status"] == "error"


def test_fresh_queued_not_reaped(conn):
    rid = store.create_run(conn, coin="b", date="d", strategy="quant",
                           analysts=[], model="m")
    ok, blocker = runner.can_start(conn)
    assert ok is False and blocker == rid  # just-created queued run still blocks


def test_launch_spawns_worker(conn, monkeypatch):
    calls = {}
    monkeypatch.setattr(runner.subprocess, "Popen",
                        lambda argv, **kw: calls.setdefault("argv", argv))
    runner.launch("abc123")
    assert "tradingagents.monitor.adhoc.worker" in calls["argv"]
    assert "abc123" in calls["argv"]
