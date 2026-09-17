"""Invented Parquet and fake HTTP only; recovery never fetches real data."""
import importlib.util
import json
from pathlib import Path
import urllib.error

import pytest

ROOT = Path(__file__).resolve().parents[2]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

recovery = load("recovery_test_engine", ROOT/"research/onchain-graph-2026-09-16/comparison/recovery_graph.py")
fixtures = load("recovery_bulk_fixtures", Path(__file__).with_name("test_onchain_bulk_graph.py"))


def setup(monkeypatch):
    monkeypatch.setattr(fixtures, "bulk", recovery.bulk)
    return fixtures.setup(monkeypatch)


def reference(directory, count):
    return dict(directory=str(directory), receipt_count=count, files=[
        dict(path=p.name, bytes=p.stat().st_size, sha256=recovery.storage.sha(p.read_bytes()))
        for i in range(1, count+1) for suffix in ("-intent.json", ".json", ".body.zst")
        for p in [directory/f"request-{i:04d}{suffix}"]])


def test_prefix_replay_missing_one_http_and_exact_copy_accounting(tmp_path, monkeypatch):
    inventory, plan, requests, _ = setup(monkeypatch)
    old = tmp_path/"old"
    first = recovery.bulk.capture_day("2001-01-01", old, inventory, plan, fixtures.budget())
    prefix = reference(old, first["requests"]-1)
    requests.clear()
    shared = fixtures.budget()
    target = tmp_path/"new"
    result = recovery.recovery_day("2001-01-01", target, inventory, plan, shared, reuse_prefix=prefix)
    assert result["status"] == "complete", result
    assert result["bindings_valid"]
    assert len(requests) == result["actual_network_requests"] == 1
    assert result["reused_requests"] == first["requests"]-1
    assert result["logical_requests"] == first["requests"]
    assert result["logical_received_bytes"] == result["actual_network_received_bytes"]+result["reused_received_bytes"]
    for entry in prefix["files"]:
        assert (target/entry["path"]).read_bytes() == (old/entry["path"]).read_bytes()
    assert shared.new_raw_bytes == sum(p.stat().st_size for p in target.glob("*.zst"))
    assert shared.new_metadata_bytes == sum(recovery.bulk._allocated(p) for p in target.iterdir() if p.suffix != ".zst")
    manifest = json.loads((target/"manifest.json").read_bytes())
    assert {f["path"] for f in manifest["files"]} == {p.name for p in target.iterdir()}-{"manifest.json"}


@pytest.mark.parametrize("kind", ["hash", "headers", "failed", "symlink"])
def test_invalid_frozen_prefix_fails_before_http(tmp_path, monkeypatch, kind):
    inventory, plan, requests, _ = setup(monkeypatch)
    old = tmp_path/"old"
    recovery.bulk.capture_day("2001-01-01", old, inventory, plan, fixtures.budget())
    prefix = reference(old, 1)
    path = old/"request-0001.json"
    if kind == "hash":
        path.write_bytes(path.read_bytes()+b" ")
    elif kind == "symlink":
        raw = path.read_bytes()
        path.unlink()
        elsewhere = tmp_path/"elsewhere"
        elsewhere.write_bytes(raw)
        path.symlink_to(elsewhere)
    else:
        value = json.loads(path.read_bytes())
        if kind == "failed":
            value["error"] = "URLError: invented DNS failure"
        else:
            value["request_headers"] = {"If-Match": '"wrong"'}
            intent_path = old/"request-0001-intent.json"
            intent = json.loads(intent_path.read_bytes())
            intent["request_headers"] = value["request_headers"]
            intent_path.write_text(json.dumps(intent))
        path.write_text(json.dumps(value))
        prefix = reference(old, 1)
    requests.clear()
    with pytest.raises((ValueError, OSError)):
        recovery.recovery_day("2001-01-01", tmp_path/"new", inventory, plan, fixtures.budget(), reuse_prefix=prefix)
    assert not requests
    assert not (tmp_path/"new").exists()


def test_first_transport_failure_latches_later_days_and_counts(tmp_path, monkeypatch):
    inventory, plan, requests, _ = setup(monkeypatch)
    original = recovery.storage.BinaryCapture
    calls = []
    class Outage:
        def open(self, request, timeout):
            calls.append(request)
            raise urllib.error.URLError("invented DNS outage")
    def factory(spec, directory):
        capture = original(spec, directory)
        capture.opener = Outage()
        return capture
    monkeypatch.setattr(recovery.storage, "BinaryCapture", factory)
    shared = fixtures.budget()
    first = recovery.recovery_day("2001-01-01", tmp_path/"first", inventory, plan, shared)
    second = recovery.recovery_day("2001-01-02", tmp_path/"second", inventory, plan, shared)
    assert first["status"] == second["status"] == "unavailable"
    assert first["actual_network_requests"] == 1 and second["actual_network_requests"] == 0
    assert first["actual_network_received_bytes"] == 0
    assert first["bindings_valid"] and second["bindings_valid"]
    assert len(calls) == 1 and "transport failure" in shared.stopped
    assert shared.new_raw_bytes == sum(p.stat().st_size for p in tmp_path.rglob("*.zst"))


def test_prefix_after_reused_blocks_and_inherited_denial(tmp_path, monkeypatch):
    inventory, plan, requests, blocks = setup(monkeypatch)
    reused = dict(body=blocks, receipt=dict(status=200, sha256=recovery.storage.sha(blocks),
        url="https://example.invalid/blocks/2001-01-01.parquet", request_headers={"If-Match": '"fixture"'},
        response_headers={"etag": '"fixture"'}), provenance=dict(receipt_path="old/r.json",
        receipt_sha256="a"*64, blob_path="old/b.zst", stored_sha256="b"*64))
    old = tmp_path/"old"
    first = recovery.bulk.capture_day("2001-01-01", old, inventory, plan, fixtures.budget(), reused_blocks=reused)
    requests.clear()
    result = recovery.recovery_day("2001-01-01", tmp_path/"new", inventory, plan, fixtures.budget(),
        reused_blocks=reused, reuse_prefix=reference(old, first["requests"]-1))
    assert result["status"] == "complete", result
    assert result["actual_network_requests"] == len(requests) == 1
    shared = fixtures.budget()
    shared.stopped = "source denied; no subsequent acquisition"
    stopped = recovery.recovery_day("2001-01-01", tmp_path/"stopped", inventory, plan, shared,
        reused_blocks=reused, reuse_prefix=reference(old, 1))
    assert stopped["status"] == "unavailable" and stopped["requests"] == 0
    assert not list((tmp_path/"stopped").glob("*.zst"))
    assert len(requests) == 1


def test_short_eof_latches_transport_stop_and_retains_received_prefix(tmp_path, monkeypatch):
    import io
    inventory, plan, requests, _ = setup(monkeypatch)
    original = recovery.storage.BinaryCapture
    calls = []
    class ShortResponse:
        status = 200
        headers = {"content-length": "999", "etag": '"fixture"'}
        def __init__(self):
            self.body = io.BytesIO(b"short transport prefix")
        def read(self, size):
            return self.body.read(size)
        read1 = read
        def close(self):
            self.body.close()
    class ShortOpener:
        def open(self, request, timeout):
            calls.append(request)
            return ShortResponse()
    def factory(spec, directory):
        capture = original(spec, directory)
        capture.opener = ShortOpener()
        return capture
    monkeypatch.setattr(recovery.storage, "BinaryCapture", factory)
    shared = fixtures.budget()
    first = recovery.recovery_day("2001-01-01", tmp_path/"first", inventory, plan, shared)
    second = recovery.recovery_day("2001-01-02", tmp_path/"second", inventory, plan, shared)
    assert first["actual_network_received_bytes"] == len(b"short transport prefix")
    assert first["bindings_valid"] and first["status"] == second["status"] == "unavailable"
    assert second["actual_network_requests"] == 0 and len(calls) == 1
    assert "body length mismatch" in shared.stopped
