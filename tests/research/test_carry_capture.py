"""Fake-transport coverage and retention tests; never contact any public host."""
import base64
import hashlib
import importlib.util
import json
import io
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11/carry_capture.py"
spec = importlib.util.spec_from_file_location("carry_capture", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def body_for(request):
    kind = request["kind"]
    if kind == "funding":
        data = [{"symbol": request["parameters"]["symbol"],
                 "fundingTime": module.START_MS + index * module.DAY_MS // 3,
                 "fundingRate": "0.0001", "markPrice": "100"} for index in range(273)]
    elif kind in {"spot", "perp", "mark"}:
        data = [[module.START_MS + index * module.DAY_MS, "100", "110", "90", "105", "1",
                 module.START_MS + (index + 1) * module.DAY_MS - 1, "0", 1, "0", "0", "0"]
                for index in range(91)]
    elif kind == "exchange-info":
        data = {"symbols": [{"symbol": asset + "USDT", "contractType": "PERPETUAL",
                             "quoteAsset": "USDT", "marginAsset": "USDT", "status": "TRADING"}
                            for asset in ("BTC", "ETH")]}
    else:
        data = {"serverTime": 1800000000000}
    return json.dumps(data).encode()


def response(body, status=200, error=None, complete=True):
    return {"body": body, "http_status": status, "headers": {"Date": "synthetic", "X-Discard": "x"},
            "error": error, "body_complete": complete}


def test_fixed_request_spec_and_exact_raw_retention(monkeypatch):
    monkeypatch.setattr(module, "_utc", lambda: module.datetime.fromtimestamp(1800000000, module.timezone.utc).isoformat())
    frozen = module.frozen_request_spec()
    calls = []
    def fake(url):
        request = frozen["requests"][len(calls)]
        calls.append(url)
        return response(body_for(request))
    raw, admission, cells = module.capture(frozen, fake)
    assert len(calls) == len(cells) == 10
    assert all(cell["status"] == "complete" for cell in cells)
    assert raw["total_body_bytes"] <= 50 * 1024 * 1024
    for request, receipt in zip(frozen["requests"], raw["requests"]):
        expected = body_for(request)
        assert base64.b64decode(receipt["body_base64"]) == expected
        assert receipt["body_sha256"] == hashlib.sha256(expected).hexdigest()
        assert receipt["headers"] == {"Date": "synthetic"}
        assert receipt["request_utc"].endswith("+00:00")
    assert "not historical calendar proof" in admission["cells"][0]["schedule"]
    assert "not historical product state" in admission["cells"][-2]["limitation"]


@pytest.mark.parametrize("status", [403, 418, 429, 451])
def test_denial_suppresses_same_host_only_and_keeps_ten_cells(status):
    calls = []
    def fake(url):
        calls.append(url)
        return response(b'{"msg":"denied"}', status=status, error=f"HTTP {status}")
    raw, _, cells = module.capture(module.frozen_request_spec(), fake)
    assert len(calls) == 2  # One denial on each independent host.
    assert len(cells) == 10
    assert all(cell["status"] == "unavailable" for cell in cells)
    assert sum(row["attempted"] for row in raw["requests"]) == 2


def test_spec_mutation_rejected_before_transport():
    frozen = module.frozen_request_spec()
    frozen["requests"][0]["url"] = "https://unregistered.invalid/"
    def forbidden(url):
        pytest.fail("transport called before exact spec admission")
    with pytest.raises(ValueError, match="exact frozen"):
        module.capture(frozen, forbidden)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "schedule", "nonfinite", "mark", "symbol"])
def test_funding_bad_coverage_is_unavailable(mutation):
    request = module.frozen_request_spec()["requests"][0]
    data = json.loads(body_for(request))
    if mutation == "missing":
        data.pop()
    elif mutation == "duplicate":
        data[1]["fundingTime"] = data[0]["fundingTime"]
    elif mutation == "schedule":
        data[1]["fundingTime"] += 5001
    elif mutation == "nonfinite":
        data[0]["fundingRate"] = "NaN"
    elif mutation == "mark":
        data[0]["markPrice"] = "0"
    else:
        data[0]["symbol"] = "OTHERUSDT"
    with pytest.raises(ValueError):
        module.admit_response(request, json.dumps(data).encode())


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "close_time", "negative", "ordering"])
def test_bar_bad_coverage_is_unavailable(mutation):
    request = module.frozen_request_spec()["requests"][2]
    data = json.loads(body_for(request))
    if mutation == "missing":
        data.pop()
    elif mutation == "duplicate":
        data[1][0] = data[0][0]
    elif mutation == "close_time":
        data[0][6] += 1
    elif mutation == "negative":
        data[0][4] = "-1"
    else:
        data[0][2] = "99"
    with pytest.raises(ValueError):
        module.admit_response(request, json.dumps(data).encode())


def test_current_metadata_must_not_admit_inactive_or_wrong_product():
    request = module.frozen_request_spec()["requests"][-2]
    data = json.loads(body_for(request))
    data["symbols"][0]["status"] = "SETTLING"
    with pytest.raises(ValueError):
        module.admit_response(request, json.dumps(data).encode())


def test_oversize_and_timeout_preserve_prefix_and_unavailable_denominator():
    requests = module.frozen_request_spec()
    calls = []
    prefix = b"received prefix"
    def fake(url):
        calls.append(url)
        if len(calls) == 1:
            return response(b"x" * (module.MAX_BYTES + 1))
        return response(prefix, error="TimeoutError", complete=False)
    raw, _, cells = module.capture(requests, fake)
    assert len(calls) == len(cells) == 10
    assert raw["requests"][0]["body_bytes"] == module.MAX_BYTES
    assert raw["requests"][0]["body_complete"] is False
    assert base64.b64decode(raw["requests"][1]["body_base64"]) == prefix
    assert all(cell["status"] == "unavailable" for cell in cells)


def test_redirect_handler_refuses_redirect():
    assert module._NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://example.invalid") is None


def test_funding_tolerance_boundary_and_raw_invalid_json_retained():
    request = module.frozen_request_spec()["requests"][0]
    data = json.loads(body_for(request))
    data[1]["fundingTime"] += 5000
    assert module.admit_response(request, json.dumps(data).encode())["maximum_schedule_offset_ms"] == 5000
    raw, _, cells = module.capture(module.frozen_request_spec(), lambda url: response(b"not json"))
    assert len(cells) == 10 and all(cell["status"] == "unavailable" for cell in cells)
    assert base64.b64decode(raw["requests"][0]["body_base64"]) == b"not json"


@pytest.mark.parametrize("failure", ["timeout", "incomplete"])
def test_transport_failure_preserves_received_bytes_and_restores_alarm(monkeypatch, failure):
    timer_calls, handler_calls, requests = [], [], []
    class FakeResponse:
        code = 200
        headers = {"Date": "synthetic"}
        reads = 0

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read1(self, limit):
            self.reads += 1
            if self.reads == 1:
                return b"partial bytes"
            if failure == "incomplete":
                raise module.http.client.IncompleteRead(b" plus fragment", 100)
            module._deadline(None, None)

    class FakeOpener:
        def open(self, request, timeout):
            requests.append((request, timeout))
            return FakeResponse()

    def fake_build(*handlers):
        assert handlers[0].proxies == {}
        assert isinstance(handlers[1], module._NoRedirect)
        return FakeOpener()

    monkeypatch.setattr(module.urllib.request, "build_opener", fake_build)
    monkeypatch.setattr(module.signal, "getsignal", lambda *args: "previous")
    monkeypatch.setattr(module.signal, "getitimer", lambda *args: (0.0, 0.0))
    monkeypatch.setattr(module.signal, "signal", lambda *args: handler_calls.append(args))
    monkeypatch.setattr(module.signal, "setitimer", lambda *args: timer_calls.append(args))
    result = module.public_get("https://fapi.binance.com/fapi/v1/time")
    assert result["body"] == b"partial bytes" + (b" plus fragment" if failure == "incomplete" else b"")
    assert result["http_status"] == 200
    assert result["body_complete"] is False
    assert ("20-second" if failure == "timeout" else "IncompleteRead") in result["error"]
    assert len(requests) == 1 and requests[0][1] == 20
    assert timer_calls[0] == (module.signal.ITIMER_REAL, 20)
    assert timer_calls[-1] == (module.signal.ITIMER_REAL, 0.0, 0.0)
    assert handler_calls[-1] == (module.signal.SIGALRM, "previous")


def test_funding_failure_preserves_missing_unexpected_and_duplicate_identities():
    request = module.frozen_request_spec()["requests"][0]
    data = json.loads(body_for(request))
    missing_stamp = data.pop()["fundingTime"]
    data[1]["fundingTime"] = data[0]["fundingTime"]
    data[2]["fundingTime"] += 5001
    raw = json.dumps(data).encode()
    _, admission, cells = module.capture(module.frozen_request_spec(), lambda url: response(raw))
    coverage = admission["cells"][0]["coverage"]
    assert cells[0]["status"] == "unavailable"
    assert coverage["expected_events"] == 273 and coverage["observed_events"] == 272
    assert coverage["missing_slot_count"] == 3
    assert missing_stamp in coverage["missing_canonical_slots_ms"]
    assert coverage["unexpected_timestamps_ms"] == [data[2]["fundingTime"]]
    assert coverage["duplicate_timestamps_ms"] == [module.START_MS]
    assert coverage["maximum_schedule_offset_ms"] == 5001


@pytest.mark.parametrize("offset, status", [(5000, "complete"), (5001, "unavailable"), (-5001, "unavailable")])
def test_server_clock_plausibility_uses_capture_interval(monkeypatch, offset, status):
    monkeypatch.setattr(module, "_utc", lambda: module.datetime.fromtimestamp(1800000000, module.timezone.utc).isoformat())
    _, admission, cells = module.capture(module.frozen_request_spec(),
        lambda url: response(json.dumps({"serverTime": 1800000000000 + offset}).encode()))
    clock = admission["cells"][-1]
    assert clock["status"] == cells[-1]["status"] == status
    assert clock["clock_check"]["server_minus_request_ms"] == offset


def test_published_receipts_survive_later_unexpected_failure(tmp_path):
    calls = []
    def transport(url):
        calls.append(url)
        if len(calls) == 2:
            raise RuntimeError("unexpected later failure")
        return response(b"first exact raw bytes")

    def persist(name, receipt):
        with (tmp_path / name).open("x") as stream:
            json.dump(receipt, stream)

    with pytest.raises(RuntimeError, match="later failure"):
        module.capture(module.frozen_request_spec(), transport, persist)
    receipt = json.loads((tmp_path / "btc-funding-receipt.json").read_text())
    assert base64.b64decode(receipt["body_base64"]) == b"first exact raw bytes"
    assert len(list(tmp_path.iterdir())) == 1


def test_incomplete_read_retains_partial_and_all_receipts(tmp_path):
    def transport(url):
        raise module.http.client.IncompleteRead(b"framing partial", 100)

    names = []
    def persist(name, receipt):
        names.append(name)
        with (tmp_path / name).open("x") as stream:
            json.dump(receipt, stream)

    raw, _, cells = module.capture(module.frozen_request_spec(), transport, persist)
    assert len(names) == len(cells) == 10
    assert all(cell["status"] == "unavailable" for cell in cells)
    assert all(base64.b64decode(row["body_base64"]) == b"framing partial" for row in raw["requests"])


def test_receipt_persistence_precedes_semantic_parsing(monkeypatch):
    published = []
    def fail_parse(*args):
        assert published == ["btc-funding-receipt.json"]
        raise RuntimeError("unexpected parser crash")

    monkeypatch.setattr(module, "admit_response", fail_parse)
    with pytest.raises(RuntimeError, match="parser crash"):
        module.capture(module.frozen_request_spec(), lambda url: response(b"{}"),
                       lambda name, receipt: published.append(name))


def test_real_http_response_premature_content_length_eof_is_incomplete(monkeypatch):
    class FakeSocket:
        def makefile(self, *args):
            return io.BytesIO(b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\n{}")

    response = module.http.client.HTTPResponse(FakeSocket())
    response.begin()
    class FakeOpener:
        def open(self, request, timeout):
            return response

    monkeypatch.setattr(module.urllib.request, "build_opener", lambda *args: FakeOpener())
    result = module.public_get("https://fapi.binance.com/fapi/v1/time")
    assert result["body"] == b"{}"
    assert result["body_complete"] is False
    assert "Content-Length EOF" in result["error"]
