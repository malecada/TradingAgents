from __future__ import annotations

import types

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("QUANT_DATA_DIR", raising=False)
    monkeypatch.setenv("TA_MONITOR_PASSWORD", "pw")
    cfg = types.SimpleNamespace(coin_universe=["bitcoin"], routing={},
                                horizons=[7, 14], data_root=str(tmp_path))
    monkeypatch.setattr("tradingagents.execution.live.config.load_config", lambda: cfg)
    # minimal quant journal so create_app's StrategySource resolves
    import sqlite3
    jp = tmp_path / "trade_journal.db"
    sqlite3.connect(str(jp)).close()
    from tradingagents.monitor.app import create_app
    from tradingagents.monitor.sources import StrategySource
    src = StrategySource(name="quant", journal_path=str(jp),
                         snapshot=lambda: {"positions": [], "usdt_free": 0.0,
                                           "equity": 0.0, "income": None})
    return create_app(quant=src, hybrid=None, log_dir=str(tmp_path))


def test_adhoc_meta_reachable_with_auth(app):
    c = TestClient(app)
    r = c.get("/api/adhoc/meta", auth=("admin", "pw"))
    assert r.status_code == 200
    assert r.json()["coins"] == ["bitcoin"]


def test_adhoc_meta_requires_auth(app):
    c = TestClient(app)
    assert c.get("/api/adhoc/meta").status_code == 401
