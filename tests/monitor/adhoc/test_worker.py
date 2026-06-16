from __future__ import annotations

import pytest

from tradingagents.monitor.adhoc import store, worker


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("QUANT_DATA_DIR", raising=False)
    c = store.connect()
    yield c
    c.close()


def test_worker_runs_generator_and_marks_done(conn, monkeypatch):
    rid = store.create_run(conn, coin="bitcoin", date="2026-05-01",
                           strategy="quant", analysts=[], model="m")

    def fake_quant(*, coin, date, run_id):
        yield ("_p", "working", "progress", "")
        yield ("quant_signal", "Quant signal", "json", {"direction": "long"})
        yield ("final", "Final decision", "json", {"direction": "long"})

    monkeypatch.setattr("tradingagents.monitor.adhoc.service.run_quant", fake_quant)
    worker.execute(rid)

    run = store.get_run(conn, rid)
    assert run["status"] == "done"
    assert run["progress"] == 1.0
    outs = store.get_outputs(conn, rid)
    keys = [o["key"] for o in outs]
    assert keys == ["quant_signal", "final"]          # progress marker not stored


def test_worker_records_error(conn, monkeypatch):
    rid = store.create_run(conn, coin="bitcoin", date="2026-05-01",
                           strategy="quant", analysts=[], model="m")

    def boom(*, coin, date, run_id):
        raise RuntimeError("kaboom")
        yield  # pragma: no cover

    monkeypatch.setattr("tradingagents.monitor.adhoc.service.run_quant", boom)
    worker.execute(rid)

    run = store.get_run(conn, rid)
    assert run["status"] == "error"
    assert "kaboom" in run["error_msg"]
