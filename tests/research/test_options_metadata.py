"""Fake options metadata only; fixed request configuration is not market input."""
import base64
import copy
import importlib.util
import json
from pathlib import Path

import pytest

DIRECTORY = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11"
spec = importlib.util.spec_from_file_location("options_metadata", DIRECTORY / "options_metadata.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def request_spec():
    return json.loads((DIRECTORY / "options-request-spec.json").read_text())


def symbol(**changes):
    row = {"symbol": "INVENTED", "underlying": "BTCUSDT", "underlyingType": "UNINTERPRETED", "contractType": "LITERAL",
           "expiryDate": 1800000000000, "side": "CALL", "unit": "1", "minQty": "0.01", "maxQty": "10",
           "status": "LITERAL", "initialMargin": "0", "maintenanceMargin": "0.1", "minInitialMargin": "0", "minMaintenanceMargin": "0",
           "nakedSell": True, "filters": [{"filterType": "LOT_SIZE", "minQty": "0.01", "maxQty": "10", "stepSize": "0.01"}]}
    row.update(changes)
    return row


def listing(request, *, truncated="true", key=None):
    common = ("<CommonPrefixes><Prefix>data/option/daily/invented/</Prefix></CommonPrefixes>" if "delimiter" in request else
              "<Contents><Key>" + (key or "data/option/daily/invented/example.zip") + "</Key><LastModified>2026-01-01T00:00:00Z</LastModified><Size>0</Size><ETag>literal</ETag></Contents>")
    return (f'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Prefix>{request["prefix"]}</Prefix>'
            f'<MaxKeys>{request["max_keys"]}</MaxKeys>' + ("<Delimiter>/</Delimiter>" if "delimiter" in request else "") +
            f'<IsTruncated>{truncated}</IsTruncated>{common}<NextMarker>not-followed</NextMarker></ListBucketResult>').encode()


def response(raw, status=200, complete=True, error=None):
    return {"body": raw, "http_status": status, "headers": {"Date": "synthetic"}, "body_complete": complete,
            "error": error if error else (None if status == 200 else f"HTTP {status}")}


def test_actual_quantities_partial_classification_no_account_claim():
    data = {"optionSymbols": [symbol(), symbol(symbol="SECOND", underlying="ETHUSDT"),
                              symbol(symbol="BTC-NAME-ONLY", underlying=None)],
            "optionContracts": [{"underlying": "BTCUSDT", "unknownNewField": 1}]}
    result = module.parse_exchange_info(json.dumps(data).encode())
    assert result["explicit_btc_eth_target_count"] == 2
    assert result["target_row_indices"] == [0, 1]
    assert len(result["normalized_symbol_rows"]) == 3
    row = result["normalized_symbol_rows"][0]
    assert row["quantity_rule_status"] == "complete"
    assert row["crypto_classification"]["status"] == "ambiguous"
    assert "unavailable" in row["account_seller_permission"]
    assert result["optionContracts"]["literal_value"] == data["optionContracts"]


@pytest.mark.parametrize("mutation", ["missing", "boolean", "conflict", "duplicate_symbol", "duplicate_lot", "inverted"])
def test_quantity_ambiguities_remain_visible(mutation):
    row = symbol()
    rows = [row]
    if mutation == "missing":
        row.pop("unit")
    elif mutation == "boolean":
        row["unit"] = True
    elif mutation == "conflict":
        row["minQty"] = "0.1"
    elif mutation == "duplicate_symbol":
        rows.append(copy.deepcopy(row))
    elif mutation == "duplicate_lot":
        row["filters"].append(copy.deepcopy(row["filters"][0]))
    else:
        row["minQty"] = "100"
    result = module.parse_exchange_info(json.dumps({"optionSymbols": rows}).encode())
    assert result["status"] == "complete"
    assert result["normalized_symbol_rows"][0]["quantity_rule_status"] == "ambiguous"
    assert result["normalized_symbol_rows"][0]["ambiguities"]


@pytest.mark.parametrize("raw", [b'{"optionSymbols":[],"optionSymbols":[]}', b'{"optionSymbols":[],"x":NaN}',
                                 b'{"optionSymbols":[],"x":1e999}', b'[]', b'{"code":-1,"msg":"error"}', b'{"optionSymbols":{}}'])
def test_json_schema_failures_are_not_empty_successes(raw):
    with pytest.raises(ValueError):
        module.parse_exchange_info(raw)


def test_truncated_listing_retains_objects_and_continuation_without_absence_claim():
    request = request_spec()["requests"][-1]
    result = module.parse_listing(listing(request), request)
    assert result["partial_listing"] is True
    assert result["contents"][0]["Size"] == 0
    assert result["continuation_metadata"]["NextMarker"] == "not-followed"
    assert "No global absence" in result["scope"]
    assert "ETag is not SHA256" in result["provenance_limits"]


@pytest.mark.parametrize("mutation", ["dtd", "entity", "prefix", "maxkeys", "delimiter", "truncation", "outside"])
def test_xml_scope_and_expansion_fail_closed(mutation):
    request = request_spec()["requests"][-1]
    raw = listing(request)
    if mutation in ("dtd", "entity"):
        raw = (b'<!DOCTYPE x []>' if mutation == "dtd" else b'<!ENTITY x SYSTEM "https://never.invalid/">') + raw
    elif mutation == "prefix":
        raw = raw.replace(b"<Prefix>data/option/daily/</Prefix>", b"<Prefix>other/</Prefix>")
    elif mutation == "maxkeys":
        raw = raw.replace(b"<MaxKeys>20</MaxKeys>", b"<MaxKeys>21</MaxKeys>")
    elif mutation == "delimiter":
        raw = raw.replace(b"<IsTruncated>", b"<Delimiter>/</Delimiter><IsTruncated>")
    elif mutation == "truncation":
        raw = raw.replace(b"<IsTruncated>true", b"<IsTruncated>1")
    else:
        raw = listing(request, key="outside/file.zip")
    with pytest.raises(ValueError):
        module.parse_listing(raw, request)


def test_four_receipts_immediate_and_host_denials_independent():
    calls, published = [], []
    def denied(url):
        calls.append(url)
        return response(b"partial denial", status=403)
    raw, _, cells = module.capture(request_spec(), denied, lambda name, row: published.append(name))
    assert len(calls) == 2
    assert len(published) == len(cells) == 4
    assert all(row["status"] == "unavailable" for row in cells)
    assert base64.b64decode(raw["requests"][0]["body_base64"]) == b"partial denial"


def test_successful_fake_pipeline_preserves_all_four_cells():
    frozen = request_spec()
    payloads = [json.dumps({"optionSymbols": [symbol()]}).encode(), b'{"serverTime":1800000000000}',
                listing(frozen["requests"][2]), listing(frozen["requests"][3])]
    count = 0
    def fake(url):
        nonlocal count
        raw = payloads[count]
        count += 1
        return response(raw)
    _, admission, cells = module.capture(frozen, fake)
    assert count == len(cells) == 4
    assert all(row["status"] == "complete" for row in cells)
    assert admission["cells"][2]["partial_listing"] is True


def test_resource_stop_preserves_all_unattempted_cells(monkeypatch):
    values = iter([0, 101, 101, 101, 101, 101, 101, 101, 101])
    monkeypatch.setattr(module.time, "monotonic", lambda: next(values))
    raw, _, cells = module.capture(request_spec(), lambda url: pytest.fail("resource-stopped request attempted"))
    assert len(cells) == 4
    assert all(not row["attempted"] and "resource budget" in row["error"] for row in raw["requests"])


def test_recoverable_parser_failure_retains_all_receipts_and_cells(monkeypatch, tmp_path):
    def crash(*args, **kwargs):
        raise RuntimeError("unexpected parser crash")
    def persist(name, row):
        with (tmp_path / name).open("x") as stream:
            json.dump(row, stream)
    monkeypatch.setattr(module, "parse_response", crash)
    _, _, cells = module.capture(request_spec(), lambda url: response(b"{}"), persist)
    saved = list(tmp_path.iterdir())
    assert len(saved) == len(cells) == 4
    assert all(row["status"] == "unavailable" and "unexpected parser crash" in row["reason"] for row in cells)
    assert base64.b64decode(json.loads(saved[0].read_text())["body_base64"]) == b"{}"


def test_lifecycle_byte_count_matches_frozen_encoder():
    from tradingagents.research.lifecycle import _encode
    value = {"cells": [{"normalized_symbol_rows": [symbol()]}], "non_ascii": "é"}
    assert module.lifecycle_bytes(value) == _encode(value)


def test_memory_error_is_not_claimed_recoverable(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise MemoryError("synthetic resource failure")
    published = []
    monkeypatch.setattr(module, "parse_response", fail)
    with pytest.raises(MemoryError):
        module.capture(request_spec(), lambda url: response(b"{}"), lambda name, row: published.append(name))
    assert len(published) == 1


def test_spec_mutation_stops_before_any_request():
    frozen = request_spec()
    frozen["requests"][0]["url"] = "https://other.invalid/"
    with pytest.raises(ValueError, match="exact frozen"):
        module.capture(frozen, lambda url: pytest.fail("mutated request attempted"))
