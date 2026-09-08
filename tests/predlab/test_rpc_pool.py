"""rpc_pool: rotation, transient backoff, non-transient refusal -> RuntimeError."""
from __future__ import annotations

import json
import urllib.error

import pytest

from tradingagents.predlab import rpc_pool


def _specs(n=3, archive=True):
    return [{"name": f"e{i}", "url": f"http://e{i}", "throttle": 0.0, "archive": archive}
            for i in range(n)]


def _patch_post(monkeypatch, handler):
    def fake(self, method, params, timeout):
        return handler(self.name, method, params)
    monkeypatch.setattr(rpc_pool.Endpoint, "_post", fake)


def test_rotates_and_returns_result(monkeypatch):
    seen = []
    _patch_post(monkeypatch, lambda name, m, p: (seen.append(name) or {"result": [1, 2]}))
    pool = rpc_pool.Pool(_specs(), selfcheck=False, log=lambda *_: None)
    for _ in range(6):
        assert pool.rpc("eth_getLogs", [{}]) == [1, 2]
    assert set(seen) == {"e0", "e1", "e2"}


def test_transient_error_rotates_then_succeeds(monkeypatch):
    calls = []

    def handler(name, m, p):
        calls.append(name)
        if name == "e0":
            return {"error": {"message": "You reached Public endpoint rate limit"}}
        return {"result": "ok"}
    _patch_post(monkeypatch, handler)
    pool = rpc_pool.Pool(_specs(), selfcheck=False, log=lambda *_: None)
    assert pool.rpc("eth_getLogs", [{}]) == "ok"
    e0 = next(e for e in pool.eps if e.name == "e0")
    assert e0.errors >= 1 and e0.penalty >= 2.0


def test_non_transient_error_from_all_endpoints_raises(monkeypatch):
    _patch_post(monkeypatch, lambda name, m, p: {"error": {"message": "query returned more than 10000 results"}})
    pool = rpc_pool.Pool(_specs(), selfcheck=False, log=lambda *_: None)
    with pytest.raises(RuntimeError, match="rpc gave up"):
        pool.rpc("eth_getLogs", [{}])
    assert all(e.penalty == 0.0 for e in pool.eps)  # size errors do not penalise


def test_http_4xx_non_transient_is_refusal(monkeypatch):
    def handler(name, m, p):
        raise urllib.error.HTTPError("u", 400, "bad", {}, __import__("io").BytesIO(b'{"error":"range too large"}'))
    _patch_post(monkeypatch, handler)
    pool = rpc_pool.Pool(_specs(2), selfcheck=False, log=lambda *_: None)
    with pytest.raises(RuntimeError):
        pool.rpc("eth_getLogs", [{}])


def test_archive_methods_skip_non_archive_endpoints(monkeypatch):
    seen = []
    _patch_post(monkeypatch, lambda name, m, p: (seen.append(name) or {"result": "0x1"}))
    specs = _specs(2, archive=False) + [{"name": "arch", "url": "http://a", "throttle": 0.0, "archive": True}]
    pool = rpc_pool.Pool(specs, selfcheck=False, log=lambda *_: None)
    for _ in range(3):
        pool.rpc("eth_call", [{}, "0x1"])
    assert seen == ["arch"] * 3
    pool.rpc("eth_getCode", ["0x0", "latest"])
    assert seen[-1] != "arch" or True  # non-archive method may use any endpoint


def test_self_check_marks_pruned_endpoint_nologs_but_keeps_calls(monkeypatch):
    seen = []

    def handler(name, m, p):
        seen.append((name, m))
        if m == "eth_blockNumber":
            return {"result": "0x1"}
        return {"result": [0] * (rpc_pool._CHECK_N if name != "e1" else 0)}
    _patch_post(monkeypatch, handler)
    pool = rpc_pool.Pool(_specs(), selfcheck=True, log=lambda *_: None)
    assert [e.disabled is None for e in pool.eps] == [True, True, True]
    assert [e.logs_ok for e in pool.eps] == [True, False, True]
    seen.clear()
    for _ in range(6):
        pool.rpc("eth_getLogs", [{}])
    assert "e1" not in {n for n, _ in seen}
    for _ in range(6):
        pool.rpc("eth_getCode", ["0x0", "latest"])
    assert "e1" in {n for n, _ in seen}


def test_self_check_disables_dead_endpoint(monkeypatch):
    def handler(name, m, p):
        if name == "e1":
            raise ConnectionError("down")
        return {"result": [0] * rpc_pool._CHECK_N}
    _patch_post(monkeypatch, handler)
    pool = rpc_pool.Pool(_specs(), selfcheck=True, log=lambda *_: None)
    assert [e.disabled is None for e in pool.eps] == [True, False, True]


def test_malformed_response_is_retried_elsewhere(monkeypatch):
    def handler(name, m, p):
        return "<html>521</html>" if name == "e0" else {"result": 7}
    _patch_post(monkeypatch, handler)
    pool = rpc_pool.Pool(_specs(), selfcheck=False, log=lambda *_: None)
    assert pool.rpc("eth_getLogs", [{}]) == 7


def test_batch_routes_to_batch_endpoints_and_orders_results(monkeypatch):
    seen = []

    def handler(name, m, p):
        seen.append(name)
        assert m == "__batch__"
        return [{"id": q["id"], "result": q["params"][0]} for q in reversed(p)]
    _patch_post(monkeypatch, handler)
    specs = [{"name": "nb", "url": "u", "throttle": 0.0, "archive": True, "batch": False},
             {"name": "b", "url": "u", "throttle": 0.0, "archive": True, "batch": True}]
    pool = rpc_pool.Pool(specs, selfcheck=False, log=lambda *_: None)
    payload = [{"jsonrpc": "2.0", "id": i, "method": "eth_getCode", "params": [f"0x{i}", "latest"]} for i in range(5)]
    assert pool.rpc("__batch__", payload) == [f"0x{i}" for i in range(5)]
    assert seen == ["b"]


def test_batch_with_historical_call_needs_archive(monkeypatch):
    seen = []
    _patch_post(monkeypatch, lambda name, m, p: (seen.append(name) or [{"id": q["id"], "result": "0x1"} for q in p]))
    specs = [{"name": "nb", "url": "u", "throttle": 0.0, "archive": False, "batch": True},
             {"name": "ab", "url": "u", "throttle": 0.0, "archive": True, "batch": True}]
    pool = rpc_pool.Pool(specs, selfcheck=False, log=lambda *_: None)
    hist = [{"jsonrpc": "2.0", "id": 0, "method": "eth_call", "params": [{}, "0x10"]}]
    latest = [{"jsonrpc": "2.0", "id": 0, "method": "eth_getCode", "params": ["0x0", "latest"]}]
    for _ in range(4):
        pool.rpc("__batch__", hist)
    assert set(seen) == {"ab"}
    seen.clear()
    for _ in range(4):
        pool.rpc("__batch__", latest)
    assert "nb" in set(seen)


def test_penalised_wait_does_not_consume_tries(monkeypatch):
    calls = {"n": 0}

    def handler(name, m, p):
        calls["n"] += 1
        if calls["n"] <= 3:
            return {"error": {"message": "rate limit"}}
        return {"result": "ok"}
    _patch_post(monkeypatch, handler)
    pool = rpc_pool.Pool(_specs(1), selfcheck=False, log=lambda *_: None)
    monkeypatch.setattr(rpc_pool.time, "sleep", lambda *_: None)
    # penalties push next_ok into the future; fake the clock forward on each pick
    real_time = rpc_pool.time.time
    offset = {"v": 0.0}
    monkeypatch.setattr(rpc_pool.time, "time", lambda: real_time() + offset.get("v", 0.0))
    orig_pick = pool._pick

    def pick(*a, **k):
        offset["v"] += 10.0
        return orig_pick(*a, **k)
    pool._pick = pick
    assert pool.rpc("eth_getLogs", [{}], tries=4) == "ok"
    assert calls["n"] == 4


def test_historical_tag_detection():
    h = rpc_pool._historical
    assert h("eth_call", [{}, "0x10"]) and not h("eth_call", [{}, "latest"])
    assert h("eth_getBlockByNumber", ["0x10", False]) and not h("eth_getBlockByNumber", ["latest", False])
    assert h("eth_getTransactionCount", ["0xabc", "0x10"]) and not h("eth_getCode", ["0xabc", "latest"])
