"""Invented in-memory Parquet objects and fake opener; no network or row decode."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import urllib.parse

import pyarrow as pa
import pyarrow.parquet as pq
import pytest


PATH = Path(__file__).resolve().parents[2] / "research/onchain-graph-2026-09-16/comparison/bulk_graph.py"
SPEC = importlib.util.spec_from_file_location("onchain_bulk_graph", PATH)
bulk = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bulk)


def parquet(columns, rows=2):
    arrays = {}
    for name, kind in columns.items():
        dtype = {"string": pa.string(), "int64": pa.int64(), "double": pa.float64(),
                 "timestamp[ns]": pa.timestamp("ns")}[kind]
        values = ["invented"]*rows if kind == "string" else list(range(rows))
        arrays[name] = pa.array(values, type=dtype)
    stream = io.BytesIO()
    pq.write_table(pa.table(arrays), stream, row_group_size=1)
    return stream.getvalue()


def setup(monkeypatch, dates=("2001-01-01", "2001-01-02"), groups=2, status=200):
    blocks, transactions = parquet(bulk.BLOCK_TYPES), parquet(bulk.TRANSACTION_TYPES, groups)
    bodies, rows = {}, []
    for date in dates:
        for table, body in (("blocks", blocks), ("transactions", transactions)):
            key = f"{table}/{date}.parquet"
            bodies[key] = body
            rows.append(dict(date=date, table=table, status="complete", objects=[dict(key=key, size=len(body), etag='"fixture"')]))
    inventory = dict(inventories=[dict(dates=rows)])
    plan = dict(base_url="https://example.invalid/", required_types=bulk.TRANSACTION_TYPES,
                block_required_types=bulk.BLOCK_TYPES,
                limits=dict(max_logical_bytes=8*bulk.GIB, max_footer_bytes=4*bulk.MIB,
                            max_projection_bytes=256*bulk.MIB, max_response_bytes=32*bulk.MIB,
                            max_block_bytes=16*bulk.MIB, timeout_seconds=30))
    requests = []

    class Response:
        def __init__(self, body, response_status, headers):
            self.status, self.headers, self.stream = response_status, headers, io.BytesIO(body)

        def read(self, size):
            return self.stream.read(size)

        read1 = read

        def close(self):
            self.stream.close()

    class Opener:
        def open(self, request, timeout):
            requests.append(request)
            key = urllib.parse.unquote(urllib.parse.urlsplit(request.full_url).path.lstrip("/"))
            body = bodies[key]
            headers = {"etag": '"fixture"'}
            span = request.headers.get("Range")
            response_status = status
            if span and status == 200:
                first, last = map(int, span.removeprefix("bytes=").split("-"))
                headers["content-range"] = f"bytes {first}-{last}/{len(body)}"
                body = body[first:last+1]
                response_status = 206
            if status != 200:
                body = b"invented denial"
            headers["content-length"] = str(len(body))
            return Response(body, response_status, headers)

    original = bulk.storage.BinaryCapture

    def capture(spec, directory):
        result = original(spec, directory)
        result.opener = Opener()
        return result

    monkeypatch.setattr(bulk.storage, "BinaryCapture", capture)
    return inventory, plan, requests, blocks


def budget(**kwargs):
    return bulk.Budget(existing_raw_bytes=12345, existing_metadata_bytes=8192,
                       disk_usage=lambda _: SimpleNamespace(free=200*bulk.GIB), **kwargs)


def test_full32group_day_exact291requests_and_incremental_two_day_accounting(tmp_path, monkeypatch):
    inventory, plan, requests, _ = setup(monkeypatch, groups=32)
    shared = budget()
    for date in ("2001-01-01", "2001-01-02"):
        result = bulk.capture_day(date, tmp_path/date, inventory, plan, shared)
        assert result["status"] == "complete", result
        assert result["requests"] == 291
        assert result["projected_rows"] == 32
        assert len(result["row_groups"]) == 32
        assert result["bindings_valid"] is True
        manifest = tmp_path/date/"manifest.json"
        assert result["manifest_sha256"] == hashlib.sha256(manifest.read_bytes()).hexdigest()
        listed = json.loads(manifest.read_bytes())["files"]
        assert {f["path"] for f in listed} == {p.name for p in (tmp_path/date).iterdir()}-{"manifest.json"}
        for entry in listed:
            assert entry["sha256"] == hashlib.sha256((tmp_path/date/entry["path"]).read_bytes()).hexdigest()
    assert len(requests) == 582
    actual_raw = sum(p.stat().st_size for p in tmp_path.rglob("*.zst"))
    actual_meta = sum(bulk._allocated(p) for p in tmp_path.rglob("*") if p.is_file() and p.suffix != ".zst")
    assert shared.new_raw_bytes == actual_raw
    assert shared.new_metadata_bytes == actual_meta
    assert shared.snapshot()["total_raw_bytes"] == 12345+actual_raw


def test_denial_latches_all_later_days_and_never_retries(tmp_path, monkeypatch):
    inventory, plan, requests, _ = setup(monkeypatch, status=403)
    shared = budget()
    first = bulk.capture_day("2001-01-01", tmp_path/"first", inventory, plan, shared)
    second = bulk.capture_day("2001-01-02", tmp_path/"second", inventory, plan, shared)
    assert first["status"] == second["status"] == "unavailable"
    assert first["denied"] and first["bindings_valid"]
    assert first["requests"] == 1 and second["requests"] == 0
    assert len(requests) == 1
    assert "source denied" in shared.stopped
    assert (tmp_path/"first"/"manifest.json").is_file()


def test_lowdisk_latch_survives_recovery(tmp_path, monkeypatch):
    inventory, plan, requests, _ = setup(monkeypatch)
    shared = budget()
    shared.disk_usage = lambda _: SimpleNamespace(free=(200*bulk.GIB if not requests else bulk.FREE_FLOOR+bulk.WORKING_RESERVE-1))
    first = bulk.capture_day("2001-01-01", tmp_path/"first", inventory, plan, shared)
    shared.disk_usage = lambda _: SimpleNamespace(free=200*bulk.GIB)
    second = bulk.capture_day("2001-01-02", tmp_path/"second", inventory, plan, shared)
    assert first["requests"] == 1 and second["requests"] == 0
    assert "disk reserve" in shared.stopped and len(requests) == 1


@pytest.mark.parametrize("kind", ["raw", "metadata"])
def test_aggregate_caps_reserve_before_first_request(tmp_path, monkeypatch, kind):
    inventory, plan, requests, _ = setup(monkeypatch)
    # Raw fits day admission, but not 33MiB per-response expansion reservation.
    shared = budget(**({"raw_ceiling": 12345+bulk.WORKING_RESERVE} if kind == "raw" else
                        {"metadata_ceiling": 8192+bulk.REQUEST_METADATA_RESERVE}))
    result = bulk.capture_day("2001-01-01", tmp_path/"first", inventory, plan, shared)
    assert result["status"] == "unavailable" and not requests
    assert kind in shared.stopped


def test_existing_path_and_prior_files_never_overwritten(tmp_path, monkeypatch):
    inventory, plan, requests, _ = setup(monkeypatch)
    own = tmp_path/"old"
    own.mkdir()
    previous = own/"receipt.json"
    previous.write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        bulk.capture_day("2001-01-01", own, inventory, plan, budget())
    assert previous.read_bytes() == b"preserve" and not requests


def test_reused_blocks_remove_only_block_request_and_retain_provenance(tmp_path, monkeypatch):
    inventory, plan, requests, blocks = setup(monkeypatch)
    provenance = dict(receipt_path="retained/receipt.json", receipt_sha256="a"*64,
                      blob_path="retained/body.zst", stored_sha256="b"*64)
    reference = dict(body=blocks, receipt=dict(status=200, sha256=hashlib.sha256(blocks).hexdigest(),
                                             url="https://example.invalid/blocks/2001-01-01.parquet",
                                             request_headers={"If-Match": '"fixture"'},
                                             response_headers={"etag": '"fixture"'}), provenance=provenance)
    result = bulk.capture_day("2001-01-01", tmp_path/"new", inventory, plan, budget(), reused_blocks=reference)
    assert result["status"] == "complete", result
    assert len(requests) == result["requests"] == 20
    assert all("/transactions/" in r.full_url for r in requests)
    assert result["reused_blocks"] == provenance
    assert json.loads((tmp_path/"new"/"reused-blocks.json").read_bytes())["provenance"] == provenance


def test_reused_block_wrong_identity_never_contacts_source(tmp_path, monkeypatch):
    inventory, plan, requests, blocks = setup(monkeypatch)
    reference = dict(body=blocks, receipt=dict(status=200, sha256=hashlib.sha256(blocks).hexdigest(),
                                             url="https://example.invalid/wrong-date.parquet",
                                             request_headers={"If-Match": '"fixture"'},
                                             response_headers={"etag": '"fixture"'}), provenance={})
    result = bulk.capture_day("2001-01-01", tmp_path/"new", inventory, plan, budget(), reused_blocks=reference)
    assert result["status"] == "unavailable" and not requests
    assert "request identity mismatch" in result["reason"]


def test_retained_receipt_tamper_forces_unavailable(tmp_path, monkeypatch):
    inventory, plan, requests, _ = setup(monkeypatch)
    original = bulk._verify

    def tamper(directory, capture):
        path = directory/"request-0001-intent.json"
        value = json.loads(path.read_bytes())
        value["url"] += "changed"
        path.write_text(json.dumps(value))
        return original(directory, capture)

    monkeypatch.setattr(bulk, "_verify", tamper)
    result = bulk.capture_day("2001-01-01", tmp_path/"new", inventory, plan, budget())
    assert result["status"] == "unavailable"
    assert not result["bindings_valid"]
    assert "binding changed" in result["reason"]


def test_schema_cannot_drop_hash_column(tmp_path, monkeypatch):
    inventory, plan, requests, _ = setup(monkeypatch)
    plan["required_types"] = {k:v for k,v in plan["required_types"].items() if k != "hash"}
    with pytest.raises(ValueError, match="nine-column"):
        bulk.capture_day("2001-01-01", tmp_path/"new", inventory, plan, budget())
    assert not requests and not (tmp_path/"new").exists()
