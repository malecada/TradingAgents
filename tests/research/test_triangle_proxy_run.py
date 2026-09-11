"""Invented complete source envelopes; no actual quotes, requests or orders."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

DIRECTORY = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11"
for name in ("options_metadata", "triangle_capture", "triangle_bound", "triangle_proxy_run"):
    spec = importlib.util.spec_from_file_location(name, DIRECTORY / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
runner = sys.modules["triangle_proxy_run"]


def replace_body(record, data):
    raw = json.dumps(data).encode()
    record.update(body_base64=base64.b64encode(raw).decode(), body_bytes=len(raw), body_sha256=hashlib.sha256(raw).hexdigest())


def synthetic_sources():
    spec = json.loads((DIRECTORY / "triangle-request-spec.json").read_text())
    records = []
    prices = {"BTCUSDT": "100", "ETHUSDT": "10", "ETHBTC": "0.1"}
    for index, request in enumerate(spec["requests"]):
        kind = request["kind"]
        if kind == "exchange-info":
            data = {"symbols": [{"symbol": symbol, "baseAsset": pair[0], "quoteAsset": pair[1], "status": "TRADING",
                                 "isSpotTradingAllowed": True, "filters": []} for symbol, pair in runner.triangle_capture.PAIRS.items()]}
        elif kind == "server-time":
            data = {"serverTime": 1800000000000}
        elif kind == "book-ticker":
            data = [{"symbol": symbol, "bidPrice": price, "askPrice": price, "bidQty": "1000000", "askQty": "1000000"}
                    for symbol, price in prices.items()]
        else:
            price = prices[request["symbol"]]
            data = {"lastUpdateId": 0, "bids": [[price, "1"]], "asks": [[price, "1"]]}
        record = {**request, "http_status": 200, "body_complete": True, "attempted": True, "error": None,
                  "request_utc": f"2020-01-01T00:00:0{index}+00:00", "retrieval_utc": f"2020-01-01T00:00:0{index}.1+00:00"}
        replace_body(record, data)
        records.append(record)
    cells = [{"id": row["id"], **runner.triangle_capture.parse_response(base64.b64decode(row["body_base64"]), request)}
             for row, request in zip(records, spec["requests"], strict=True)]
    return {"request_spec": spec, "requests": records}, {"cells": cells}


@pytest.mark.parametrize("field,value", [("body_complete", 1), ("body_complete", "true"),
                                         ("attempted", 1), ("attempted", False),
                                         ("http_status", 200.0), ("error", "")])
def test_success_receipt_requires_literal_typed_flags(field, value):
    capture, admission = synthetic_sources()
    capture["requests"][2][field] = value
    _, cells = runner.evaluate(capture, admission)
    assert len(cells) == 8 and all(cell["status"] == "unavailable" for cell in cells)


@pytest.mark.parametrize("source_index", [0, 2, 3])
def test_complete_parent_must_equal_entire_reparsed_normalization(source_index):
    capture, admission = synthetic_sources()
    admission["cells"][source_index]["invented_extra_field"] = "not from raw"
    proxy, cells = runner.evaluate(capture, admission)
    expected_status = "complete" if source_index == 3 else "unavailable"
    assert len(cells) == 8 and all(cell["status"] == expected_status for cell in cells)
    state = proxy["source_availability"][capture["requests"][source_index]["id"]]
    assert state["status"] == "unavailable"
    assert "normalized admission differs" in state["reason"]


def test_status_only_parent_and_float_body_size_are_not_complete_sources():
    capture, admission = synthetic_sources()
    admission["cells"][2] = {"id": "triangle-book-ticker", "status": "complete"}
    _, cells = runner.evaluate(capture, admission)
    assert all(cell["status"] == "unavailable" for cell in cells)
    capture, admission = synthetic_sources()
    capture["requests"][2]["body_bytes"] = float(capture["requests"][2]["body_bytes"])
    _, cells = runner.evaluate(capture, admission)
    assert all(cell["status"] == "unavailable" for cell in cells)


def test_normalized_boolean_cannot_be_replaced_by_equal_integer():
    capture, admission = synthetic_sources()
    admission["cells"][0]["symbols"]["BTCUSDT"]["isSpotTradingAllowed"] = 1
    proxy, cells = runner.evaluate(capture, admission)
    assert all(cell["status"] == "unavailable" for cell in cells)
    assert "normalized admission differs" in proxy["source_availability"]["triangle-exchange-info"]["reason"]


def test_parity_and_fees_full_pipeline_preserves_static_scope_and_clocks():
    capture, admission = synthetic_sources()
    proxy, cells = runner.evaluate(capture, admission)
    assert len(cells) == len(proxy["cases"]) == 8
    assert all(cell["status"] == "complete" for cell in cells)
    assert proxy["ticker_capture_clocks"]["request_utc"] == capture["requests"][2]["request_utc"]
    assert proxy["ticker_capture_clocks"]["retrieval_utc"] == capture["requests"][2]["retrieval_utc"]
    assert proxy["all_six_source_cells_available"] is True
    for result in proxy["cases"].values():
        capital, fee = result["initial_capital_usdt"], result["received_asset_fee_rate_per_leg"]
        assert result["status"] == "conditional_full_notional_proxy"
        assert result["terminal_usdt"] == pytest.approx(capital * (1 - fee)**3)
        assert result["terminal_wallets"]["BTC"] == result["terminal_wallets"]["ETH"] == 0
        assert result["execution"]["status"] == "unavailable"
        assert result["graduation"] is False
        assert all(item["status"] == "unavailable" for item in result["inference_limits"].values())


@pytest.mark.parametrize("failure", ["hash", "metadata", "ticker", "parent_admission", "identity"])
def test_required_failures_keep_all_eight_unavailable(failure):
    capture, admission = synthetic_sources()
    if failure == "hash":
        capture["requests"][2]["body_sha256"] = "0" * 64
    elif failure == "metadata":
        data = json.loads(base64.b64decode(capture["requests"][0]["body_base64"]))
        data["symbols"][0]["status"] = "BREAK"
        replace_body(capture["requests"][0], data)
    elif failure == "ticker":
        data = json.loads(base64.b64decode(capture["requests"][2]["body_base64"]))
        data[0]["bidQty"] = "0"
        replace_body(capture["requests"][2], data)
    elif failure == "parent_admission":
        admission["cells"][2].update(status="unavailable", reason="invented parent failure")
    else:
        capture["requests"][2]["url"] = "https://other.invalid/"
    proxy, cells = runner.evaluate(capture, admission)
    assert len(cells) == 8 and all(cell["status"] == "unavailable" for cell in cells)
    assert all(result["status"] == "unavailable" for result in proxy["cases"].values())


@pytest.mark.parametrize("failure", ["schema", "hash", "parent_admission", "incomplete"])
def test_optional_depth_failure_keeps_proxy_without_implying_fills(failure):
    capture, admission = synthetic_sources()
    record = capture["requests"][3]
    if failure == "schema":
        replace_body(record, {"lastUpdateId": 0, "bids": [["200", "1"]], "asks": [["100", "1"]]})
    elif failure == "hash":
        record["body_sha256"] = "0" * 64
    elif failure == "parent_admission":
        admission["cells"][3].update(status="unavailable", reason="invented source failure")
    else:
        record["body_complete"] = False
    proxy, cells = runner.evaluate(capture, admission)
    assert all(cell["status"] == "complete" for cell in cells)
    assert proxy["all_six_source_cells_available"] is False
    assert proxy["source_availability"][record["id"]]["status"] == "unavailable"
    assert all(case["execution"]["status"] == "unavailable" for case in proxy["cases"].values())
    assert proxy["cases"]["btc-eth-1000-zero-fee"]["terminal_usdt"] == pytest.approx(1000)


def test_frozen_spec_denominator_and_optional_clock_failures():
    capture, admission = synthetic_sources()
    replace_body(capture["requests"][1], {"serverTime": True})
    proxy, cells = runner.evaluate(capture, admission)
    assert all(cell["status"] == "complete" for cell in cells)
    assert proxy["source_availability"]["triangle-server-time"]["status"] == "unavailable"
    capture["request_spec"]["requests"].pop()
    _, cells = runner.evaluate(capture, admission)
    assert len(cells) == 8 and all(cell["status"] == "unavailable" for cell in cells)


def test_cli_rejects_actual_pretty_serialized_output_before_write(monkeypatch):
    capture, admission = synthetic_sources()
    writes = []
    class FakeRun:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read_input(self, name):
            return json.dumps(capture if name == 'capture' else admission).encode()
        def write_json(self, name, output):
            writes.append(name)
        def finish(self, cells):
            pytest.fail('oversized output cannot finish a successful claim')
    monkeypatch.setattr(runner.ResearchRun, 'start', lambda **kwargs: FakeRun())
    monkeypatch.setattr(sys, 'argv', ['triangle_proxy_run.py', '--source', 'synthetic'])
    # Compact JSON fits, but actual lifecycle pretty encoding exceeds the cap.
    oversized = {'values': [0] * 350000}
    assert len(json.dumps(oversized, separators=(',', ':')).encode()) < runner.MAX_OUTPUT_BYTES
    assert len(runner.lifecycle_bytes(oversized)) > runner.MAX_OUTPUT_BYTES
    monkeypatch.setattr(runner, 'evaluate', lambda *_: (oversized, []))
    with pytest.raises(ValueError, match='serialized limit'):
        runner.main()
    assert writes == []
