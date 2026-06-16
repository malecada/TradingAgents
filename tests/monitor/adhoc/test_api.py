from __future__ import annotations

import types

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tradingagents.monitor.adhoc import api, store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("QUANT_DATA_DIR", raising=False)
    cfg = types.SimpleNamespace(
        coin_universe=["bitcoin", "ethereum"], routing={}, horizons=[7, 14],
        data_root=str(tmp_path))
    monkeypatch.setattr("tradingagents.execution.live.config.load_config", lambda: cfg)
    # never actually spawn a worker in API tests
    monkeypatch.setattr("tradingagents.monitor.adhoc.runner.launch",
                        lambda run_id: None)
    app = FastAPI()
    api.register_adhoc_routes(app)
    return TestClient(app)


def test_meta_lists_coins_and_defaults(client):
    body = client.get("/api/adhoc/meta").json()
    assert body["coins"] == ["bitcoin", "ethereum"]
    assert body["default_model"] == "gpt-4o-mini"
    assert "market" in body["default_analysts"]
    assert body["job_running"] is False


def test_run_creates_and_returns_id(client):
    r = client.post("/api/adhoc/run", json={
        "coin": "bitcoin", "date": "2026-05-01", "strategy": "quant"})
    assert r.status_code == 200
    rid = r.json()["run_id"]
    status = client.get(f"/api/adhoc/status/{rid}").json()
    assert status["status"] == "queued"


def test_run_rejects_unknown_coin(client):
    r = client.post("/api/adhoc/run", json={
        "coin": "dogecoin", "date": "2026-05-01", "strategy": "quant"})
    assert r.status_code == 400


def test_run_conflicts_when_job_active(client):
    client.post("/api/adhoc/run", json={
        "coin": "bitcoin", "date": "2026-05-01", "strategy": "quant"})
    r2 = client.post("/api/adhoc/run", json={
        "coin": "ethereum", "date": "2026-05-01", "strategy": "quant"})
    assert r2.status_code == 409


def test_result_returns_outputs(client):
    rid = client.post("/api/adhoc/run", json={
        "coin": "bitcoin", "date": "2026-05-01", "strategy": "quant"}).json()["run_id"]
    conn = store.connect()
    store.add_output(conn, rid, key="final", label="Final", kind="json",
                     content={"direction": "long"}, ordinal=0)
    conn.close()
    body = client.get(f"/api/adhoc/result/{rid}").json()
    assert body["run"]["coin"] == "bitcoin"
    assert body["outputs"][0]["content"] == {"direction": "long"}


def test_result_404_unknown(client):
    assert client.get("/api/adhoc/result/nope").status_code == 404
