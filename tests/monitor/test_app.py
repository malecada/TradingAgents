import base64

import pytest
from starlette.testclient import TestClient

from tradingagents.monitor.app import create_app

_PW = "testpw"


def _auth_header(user="admin", pw=_PW):
    raw = f"{user}:{pw}".encode()
    return {"Authorization": "Basic " + base64.b64encode(raw).decode()}


def _offline_provider():
    # Force the snapshot-fallback path deterministically — never touch Binance.
    raise RuntimeError("live unavailable")


@pytest.fixture
def client(journal_path, log_dir, monkeypatch):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", _PW)
    app = create_app(journal_path=journal_path, log_dir=log_dir,
                      start_capital=10000.0,
                      position_provider=_offline_provider)
    return TestClient(app)


@pytest.fixture
def empty_client(empty_journal_path, tmp_path, monkeypatch):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", _PW)
    app = create_app(journal_path=empty_journal_path, log_dir=str(tmp_path),
                      start_capital=10000.0,
                      position_provider=_offline_provider)
    return TestClient(app)


def test_create_app_requires_password(journal_path, log_dir, monkeypatch):
    monkeypatch.delenv("TA_MONITOR_PASSWORD", raising=False)
    with pytest.raises(RuntimeError):
        create_app(journal_path=journal_path, log_dir=log_dir)


def test_root_requires_auth(client):
    assert client.get("/").status_code == 401


def test_root_rejects_bad_password(client):
    r = client.get("/", headers=_auth_header(pw="wrong"))
    assert r.status_code == 401


def test_root_ok_with_auth(client):
    r = client.get("/", headers=_auth_header())
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_api_performance(client):
    r = client.get("/api/performance", headers=_auth_header())
    assert r.status_code == 200
    body = r.json()
    # Holdings come from the latest snapshot's position_qty_per_coin map;
    # usd values qty at the latest cycle's prediction ref_price.
    assert body["cards"]["open_positions"] == 2
    assert len(body["equity"]) == 2
    assert {h["coin"] for h in body["holdings"]} == {"bitcoin", "ethereum"}
    usd = {h["coin"]: h["usd"] for h in body["holdings"]}
    assert usd["bitcoin"] == 0.06 * 68000.0
    assert usd["ethereum"] == 1.4 * 3800.0
    assert body["holdings_usd_total"] == 0.06 * 68000.0 + 1.4 * 3800.0


def test_holdings_live_when_provider_succeeds(journal_path, log_dir, monkeypatch):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", _PW)
    provider = lambda: [
        {"symbol": "BTCUSDT", "qty": 0.001, "usd": 63.0},
        {"symbol": "SOLUSDT", "qty": 0.96, "usd": 64.06},
    ]
    app = create_app(journal_path=journal_path, log_dir=log_dir,
                     position_provider=provider)
    body = TestClient(app).get(
        "/api/performance", headers=_auth_header()).json()
    assert body["holdings_stale"] is False
    assert body["holdings_as_of"] is None
    assert body["holdings_live_error"] is None
    coins = {h["coin"]: h for h in body["holdings"]}
    assert set(coins) == {"bitcoin", "solana"}
    assert coins["bitcoin"]["qty"] == 0.001
    assert coins["solana"]["usd"] == 64.06
    assert body["cards"]["open_positions"] == 2
    assert body["holdings_usd_total"] == 63.0 + 64.06


def test_holdings_fall_back_to_snapshot_when_live_fails(
        journal_path, log_dir, monkeypatch):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", _PW)

    def boom():
        raise RuntimeError("ip banned")

    app = create_app(journal_path=journal_path, log_dir=log_dir,
                     position_provider=boom)
    body = TestClient(app).get(
        "/api/performance", headers=_auth_header()).json()
    assert body["holdings_stale"] is True
    assert body["holdings_as_of"] == "2026-05-20T07:05:00+00:00"
    assert "ip banned" in body["holdings_live_error"]
    # Falls back to the latest snapshot, valued at ref_price.
    assert {h["coin"] for h in body["holdings"]} == {"bitcoin", "ethereum"}
    usd = {h["coin"]: h["usd"] for h in body["holdings"]}
    assert usd["bitcoin"] == 0.06 * 68000.0


def test_live_positions_cached_within_ttl(journal_path, log_dir, monkeypatch):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", _PW)
    calls = {"n": 0}

    def provider():
        calls["n"] += 1
        return [{"symbol": "BTCUSDT", "qty": 0.001, "usd": 63.0}]

    now = {"t": 1000.0}
    app = create_app(journal_path=journal_path, log_dir=log_dir,
                     position_provider=provider,
                     position_cache_ttl=30.0, clock=lambda: now["t"])
    c = TestClient(app)
    c.get("/api/performance", headers=_auth_header())
    c.get("/api/performance", headers=_auth_header())
    assert calls["n"] == 1  # second read served from cache
    now["t"] += 31.0
    c.get("/api/performance", headers=_auth_header())
    assert calls["n"] == 2  # TTL expired, refetched


def test_api_trades(client):
    r = client.get("/api/trades", headers=_auth_header())
    assert r.status_code == 200
    body = r.json()
    assert len(body["executions"]) == 3
    assert body["executions"][0]["status"] == "FAILED"  # newest first


def test_api_cycles(client):
    r = client.get("/api/cycles", headers=_auth_header())
    assert r.status_code == 200
    assert [c["cycle_id"] for c in r.json()["cycles"]] == ["c2", "c1"]


def test_api_cycle_detail(client):
    r = client.get("/api/cycle/c2", headers=_auth_header())
    assert r.status_code == 200
    body = r.json()
    assert len(body["predictions"]) == 2
    assert len(body["risk_checks"]) == 2


def test_api_health(client):
    r = client.get("/api/health", headers=_auth_header())
    assert r.status_code == 200
    body = r.json()
    assert len(body["timeline"]) == 2
    assert len(body["steps"]) == 3
    assert len(body["errors"]) == 1
    assert len(body["retrains"]) == 1


def test_api_empty_db_returns_empty_states(empty_client):
    r = empty_client.get("/api/performance", headers=_auth_header())
    assert r.status_code == 200
    body = r.json()
    assert body["equity"] == []
    assert body["cards"]["open_positions"] == 0

    r = empty_client.get("/api/trades", headers=_auth_header())
    assert r.json()["executions"] == []


def test_api_missing_db_returns_503(log_dir, monkeypatch):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", _PW)
    app = create_app(journal_path="/nonexistent/trade_journal.db",
                      log_dir=log_dir, start_capital=10000.0)
    client = TestClient(app)
    r = client.get("/api/performance", headers=_auth_header())
    assert r.status_code == 503
    assert "error" in r.json()
