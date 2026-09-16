"""Independent checker on synthetic raw captures only; no external endpoints."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
COMPARISON = ROOT / "research/onchain-graph-2026-09-16/comparison"
PREFIX = "research/onchain-graph-2026-09-16/comparison"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixtures = load_module("bulk_check_synthetic_fixtures", ROOT / "tests/research/test_onchain_bulk_graph.py")


@pytest.fixture
def checker(monkeypatch):
    monkeypatch.syspath_prepend(str(COMPARISON))
    return load_module("independent_bulk_check_test", COMPARISON / "check_bulk.py")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def prepare(tmp_path, monkeypatch, date="2001-01-01", status=200):
    inventory, plan, requests, blocks = fixtures.setup(monkeypatch, dates=(date,), status=status)
    own = tmp_path / PREFIX
    directory = own / "bulk-artifacts" / date
    directory.parent.mkdir(parents=True)
    write_json(own / "capture-plan.json", plan)
    write_json(own / "bulk-cohort.json", dict(dates=[date]))
    write_json(tmp_path / "research_runs/eth-panel-readiness-20260916/outputs/inventory.json", inventory)
    return own, directory, inventory, plan, requests, blocks


def test_complete_ordinary_day_is_independently_verified(tmp_path, monkeypatch, checker):
    own, directory, inventory, plan, requests, _ = prepare(tmp_path, monkeypatch)
    cell = fixtures.bulk.capture_day("2001-01-01", directory, inventory, plan, fixtures.budget())
    assert cell["status"] == "complete"
    result = checker.check_day(tmp_path, "2001-01-01", cell)
    assert result["status"] == "verified" and result["source_status"] == "complete"
    assert result["received_bytes"] == cell["received_bytes"]
    assert result["graph_rows_decoded"] is result["price_fields_parsed"] is False
    assert len(requests) == 21


def test_complete_reused_jan9_blocks_bind_real_synthetic_receipt_blob(tmp_path, monkeypatch, checker):
    date = "2024-01-09"
    own, directory, inventory, plan, requests, _ = prepare(tmp_path, monkeypatch, date=date)
    retained = tmp_path / "retained-blocks"
    capture = fixtures.bulk.storage.BinaryCapture(dict(plan["limits"], base_url=plan["base_url"]), retained)
    body, receipt = capture.get(plan["base_url"]+f"blocks/{date}.parquet", {"If-Match": '"fixture"'})
    receipt_path, blob_path = retained / "request-0001.json", retained / receipt["blob"]["path"]
    reference = dict(receipt_path=str(receipt_path.relative_to(tmp_path)),
                     receipt_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                     blob_path=str(blob_path.relative_to(tmp_path)),
                     stored_sha256=receipt["blob"]["stored_sha256"], raw_sha256=hashlib.sha256(body).hexdigest())
    write_json(own / "bulk-reuse.json", dict(jan9_blocks=reference))
    cell = fixtures.bulk.capture_day(date, directory, inventory, plan, fixtures.budget(),
                                    reused_blocks=dict(body=body, receipt=receipt,
                                                       provenance={k:v for k,v in reference.items() if k != "raw_sha256"}))
    assert cell["status"] == "complete", cell
    assert cell["requests"] == 20  # Retained block request belongs to its original capture.
    result = checker.check_day(tmp_path, date, cell)
    assert result["status"] == "verified" and result["source_status"] == "complete"
    assert len(requests) == 21


@pytest.mark.parametrize("kind", ["raw", "manifest"])
def test_tampered_retained_evidence_fails(tmp_path, monkeypatch, checker, kind):
    _, directory, inventory, plan, _, _ = prepare(tmp_path, monkeypatch)
    cell = fixtures.bulk.capture_day("2001-01-01", directory, inventory, plan, fixtures.budget())
    path = directory / ("request-0001.body.zst" if kind == "raw" else "manifest.json")
    original = path.read_bytes()
    path.write_bytes(bytes([original[0] ^ 1])+original[1:])
    with pytest.raises(ValueError, match="hash"):
        checker.check_day(tmp_path, "2001-01-01", cell)


def test_denial_evidence_verified_but_source_remains_unavailable(tmp_path, monkeypatch, checker):
    _, directory, inventory, plan, requests, _ = prepare(tmp_path, monkeypatch, status=403)
    cell = fixtures.bulk.capture_day("2001-01-01", directory, inventory, plan, fixtures.budget())
    assert cell["status"] == "unavailable" and cell["denied"]
    result = checker.check_day(tmp_path, "2001-01-01", cell)
    assert result["status"] == "verified" and result["source_status"] == "unavailable"
    assert len(requests) == 1
