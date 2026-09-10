"""HTTP contract for /api/predlab/* (auth, shapes, degradation)."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from tradingagents.monitor.app import create_app
from tradingagents.monitor.predlab import PredlabSource
from tradingagents.monitor.sources import StrategySource

# Follows the pattern in tests/monitor/test_app.py: monkeypatch the auth
# env var, build a StrategySource with a failing snapshot, call create_app
# directly (no shared fixture needed since predlab is the only variable).
AUTH = ("admin", "testpw")


def _quant_source(tmp_path):
    return StrategySource(
        name="quant", journal_path=str(tmp_path / "missing.db"),
        snapshot=lambda: (_ for _ in ()).throw(RuntimeError("no exchange")))


def _client(tmp_path, monkeypatch, predlab):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", "testpw")
    app = create_app(quant=_quant_source(tmp_path), hybrid=None,
                     log_dir=str(tmp_path), predlab=predlab)
    return TestClient(app)


def _mk_predlab(tmp_path):
    s1 = tmp_path / "pl" / "predlab" / "s1_paper"
    s1.mkdir(parents=True)
    row = {"asof": "2026-08-04", "written_utc": "2026-08-04T00:20:00+00:00",
           "n_universe": 500, "membership_hash": "abc",
           "weights": {"BTCUSDT": 0.025, "AKEUSDT": -0.025},
           "realized_book_ret": None, "est_turnover": 0.1,
           "est_cost": 0.00005, "vt15_b100_scale": None, "breadth": 200}
    (s1 / "journal_champion.jsonl").write_text(json.dumps(row) + "\n")
    return PredlabSource(str(tmp_path / "pl"))


def test_endpoints_require_auth(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, _mk_predlab(tmp_path))
    assert c.get("/api/predlab/performance").status_code == 401


def test_performance_shape(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, _mk_predlab(tmp_path))
    r = c.get("/api/predlab/performance", auth=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["books"]["champion"] is None
    assert body["measurement"]["status"] == "legacy_only"
    assert body["measurement"]["books"]["champion"]["journal"] == "journal_champion.jsonl"
    assert body["books"]["vt10"] is None
    assert body["reference"] is None
    assert body["nav"]["champion"] is None
    assert body["nav"]["vt10"] is None
    assert body["account"] == {"testnet": None, "live": None}


def test_book_endpoint_and_unknown_book(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, _mk_predlab(tmp_path))
    r = c.get("/api/predlab/book?book=champion", auth=AUTH)
    assert r.json()["detail"]["asof"] == "2026-08-04"
    assert c.get("/api/predlab/book?book=nope", auth=AUTH).status_code == 400


def test_gate_and_health(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, _mk_predlab(tmp_path))
    g = c.get("/api/predlab/gate", auth=AUTH).json()
    assert g["informational"] is True
    assert g["status"] == "suspended_after_audit"
    assert g["threshold_sr"] is None
    assert g["running"]["sr"] is None
    h = c.get("/api/predlab/health", auth=AUTH).json()
    assert h["books"]["champion"]["rows"] == 1


def test_malformed_asof_rows_skipped_not_fatal(tmp_path, monkeypatch):
    # One good row plus two valid-JSON rows with unparseable ``asof``
    # (non-string, and non-ISO string) must be skipped and counted, never
    # crash the four /api/predlab endpoints (parse_journal / book_health
    # robustness contract).
    s1 = tmp_path / "pl" / "predlab" / "s1_paper"
    s1.mkdir(parents=True)
    good = {"asof": "2026-08-04", "written_utc": "2026-08-04T00:20:00+00:00",
            "n_universe": 500, "membership_hash": "abc",
            "weights": {"BTCUSDT": 0.025, "AKEUSDT": -0.025},
            "realized_book_ret": None, "est_turnover": 0.1,
            "est_cost": 0.00005, "vt15_b100_scale": None, "breadth": 200}
    bad_int_asof = {**good, "asof": 123}
    bad_str_asof = {**good, "asof": "not-a-date"}
    lines = "\n".join(json.dumps(r) for r in
                       (good, bad_int_asof, bad_str_asof))
    (s1 / "journal_champion.jsonl").write_text(lines + "\n")
    predlab = PredlabSource(str(tmp_path / "pl"))
    c = _client(tmp_path, monkeypatch, predlab)
    for path in ("/api/predlab/performance", "/api/predlab/book",
                 "/api/predlab/gate", "/api/predlab/health"):
        assert c.get(path, auth=AUTH).status_code == 200
    h = c.get("/api/predlab/health", auth=AUTH).json()
    assert h["books"]["champion"]["malformed"] == 2
    assert h["books"]["champion"]["rows"] == 1


def test_no_predlab_source_degrades(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, None)
    r = c.get("/api/predlab/performance", auth=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["books"] == {"champion": None, "vt10": None}
    assert body["nav"] == {"champion": None, "vt10": None}
    assert body["account"] == {"testnet": None, "live": None}
    assert body["measurement"]["status"] == "missing"
    assert set(body["measurement"]["books"]) == {"champion", "vt10"}
    assert all(d["status"] == "missing" for d in body["measurement"]["books"].values())
    g = c.get("/api/predlab/gate", auth=AUTH)
    assert g.status_code == 200 and g.json()["informational"] is True


def test_corrected_net_v2_http_contract(tmp_path, monkeypatch):
    from .test_predlab_v2 import v2_rows, write_rows, paper_path
    write_rows(paper_path(tmp_path), v2_rows())
    c = _client(tmp_path, monkeypatch, PredlabSource(str(tmp_path)))
    response = c.get('/api/predlab/performance', auth=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert body['measurement']['books']['champion']['status'] == 'corrected_v2'
    assert body['books']['champion']['cards']['cum_return'] == pytest.approx(-.01)
    assert body['nav']['champion']['cards']['nav_cum_return'] == pytest.approx(-.0112)
    assert body['reference'] is None and body['backtest_yearly'] is None
