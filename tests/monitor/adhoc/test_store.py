from __future__ import annotations

import time

import pytest

from tradingagents.monitor.adhoc import store


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("QUANT_DATA_DIR", raising=False)
    c = store.connect()
    yield c
    c.close()


def test_create_and_get_run(conn):
    rid = store.create_run(conn, coin="bitcoin", date="2026-05-01",
                           strategy="quant", analysts=["market"], model="gpt-4o-mini")
    run = store.get_run(conn, rid)
    assert run["coin"] == "bitcoin"
    assert run["strategy"] == "quant"
    assert run["status"] == "queued"
    assert run["analysts"] == ["market"]  # decoded from analysts_json


def test_add_and_get_outputs(conn):
    rid = store.create_run(conn, coin="bitcoin", date="2026-05-01",
                           strategy="quant", analysts=[], model="m")
    store.add_output(conn, rid, key="quant_signal", label="Quant signal",
                     kind="json", content={"direction": "long"}, ordinal=0)
    store.add_output(conn, rid, key="note", label="Note", kind="text",
                     content="hello", ordinal=1)
    outs = store.get_outputs(conn, rid)
    assert [o["key"] for o in outs] == ["quant_signal", "note"]
    assert outs[0]["content"] == {"direction": "long"}   # json decoded
    assert outs[1]["content"] == "hello"


def test_set_status_and_heartbeat(conn):
    rid = store.create_run(conn, coin="b", date="d", strategy="quant",
                           analysts=[], model="m")
    store.set_status(conn, rid, "running", started_ts=time.time())
    store.heartbeat(conn, rid, stage="working", progress=0.5)
    run = store.get_run(conn, rid)
    assert run["status"] == "running"
    assert run["stage"] == "working"
    assert run["progress"] == 0.5
    assert run["heartbeat_ts"] is not None


def test_active_run_lock(conn):
    assert store.active_run(conn) is None
    rid = store.create_run(conn, coin="b", date="d", strategy="quant",
                           analysts=[], model="m")
    assert store.active_run(conn)["run_id"] == rid
    store.set_status(conn, rid, "done")
    assert store.active_run(conn) is None


def test_list_runs_newest_first(conn):
    r1 = store.create_run(conn, coin="b", date="d", strategy="quant",
                          analysts=[], model="m")
    r2 = store.create_run(conn, coin="e", date="d", strategy="hybrid",
                          analysts=[], model="m")
    runs = store.list_runs(conn, limit=10)
    assert [r["run_id"] for r in runs[:2]] == [r2, r1]
