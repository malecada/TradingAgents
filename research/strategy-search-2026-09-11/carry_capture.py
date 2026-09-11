"""One-shot public input capture and conditional coverage checks; no trading PnL."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import http.client
import json
import math
from pathlib import Path
import signal
import time
import urllib.error
import urllib.parse
import urllib.request

from tradingagents.research import ResearchRun

START_MS, END_MS = 1775001600000, 1782864000000
DAY_MS = 86_400_000
MAX_BYTES, TIMEOUT_SECONDS = 5 * 1024 * 1024, 20
DENIALS = {403, 418, 429, 451}
REGISTRATION = "research/strategy-search-2026-09-11/gates-capture.json"
EXPERIMENT = "carry-inputs-20260911"


def frozen_request_spec():
    requests = []
    for kind, host, endpoint in (
        ("funding", "fapi.binance.com", "/fapi/v1/fundingRate"),
        ("spot", "api.binance.com", "/api/v3/klines"),
        ("perp", "fapi.binance.com", "/fapi/v1/klines"),
        ("mark", "fapi.binance.com", "/fapi/v1/markPriceKlines"),
    ):
        for asset in ("btc", "eth"):
            params = {"symbol": asset.upper() + "USDT", "startTime": START_MS,
                      "endTime": END_MS - 1, "limit": 1000}
            if kind != "funding":
                params["interval"] = "1d"
            requests.append({"id": f"{asset}-{kind}", "kind": kind,
                             "url": "https://" + host + endpoint, "parameters": params})
    requests.extend({"id": name, "kind": name,
                     "url": "https://fapi.binance.com/fapi/v1/" + endpoint,
                     "parameters": {}}
                    for name, endpoint in (("exchange-info", "exchangeInfo"), ("server-time", "time")))
    return {"schema_version": 1, "window": ["2026-04-01T00:00:00Z", "2026-07-01T00:00:00Z"],
            "max_requests": 10, "timeout_seconds_per_request": TIMEOUT_SECONDS,
            "max_response_bytes": MAX_BYTES, "requests": requests}


def _utc():
    return datetime.now(timezone.utc).isoformat()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _deadline(signum, frame):
    raise TimeoutError("20-second request wall deadline")


def public_get(url):
    """Main-thread Linux transport: no proxies, auth, retry or redirects.

    The alarm bounds connection and streamed-body reads together. Exact received
    prefix bytes are retained on timeout/oversize and never labeled a full body.
    """
    body, headers, status, error, complete = bytearray(), {}, None, None, False
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    if previous_timer != (0.0, 0.0):
        raise RuntimeError("capture requires no pre-existing real-time alarm")
    signal.signal(signal.SIGALRM, _deadline)
    try:
        signal.setitimer(signal.ITIMER_REAL, TIMEOUT_SECONDS)
        request = urllib.request.Request(url, headers={"Accept": "application/json",
                                         "User-Agent": "RegisteredCarryInputResearch/1.0"})
        try:
            response = opener.open(request, timeout=TIMEOUT_SECONDS)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            status = response.code
            headers = {name: response.headers[name] for name in ("Date", "Content-Type")
                       if name in response.headers}
            while True:
                chunk = response.read1(min(65536, MAX_BYTES - len(body) + 1))
                if not chunk:
                    remaining_length = getattr(response, "length", None)
                    if remaining_length is not None and remaining_length > 0:
                        error = "incomplete HTTP body: premature Content-Length EOF; retained received prefix"
                    else:
                        complete = True
                    break
                remaining = MAX_BYTES - len(body)
                body.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    error = "response exceeds 5 MiB; retained exact prefix only"
                    break
            if status != 200 and error is None:
                error = f"HTTP {status}"
    except http.client.IncompleteRead as exc:
        remaining = MAX_BYTES - len(body)
        body.extend(exc.partial[:remaining])
        error = "IncompleteRead: incomplete HTTP body; retained received prefix"
    except (OSError, ValueError, http.client.HTTPException) as exc:
        error = type(exc).__name__ + ": " + str(exc)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)
    return {"body": bytes(body), "http_status": status, "headers": headers,
            "error": error, "body_complete": complete}


def _number(value, name, positive=False):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(f"invalid {name}")
    return value


def _integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be integer milliseconds")
    return value


def funding_coverage(data):
    """Retain every observed/missing identity under the conditional schedule."""
    expected = [START_MS + index * DAY_MS // 3 for index in range(273)]
    if not isinstance(data, list):
        return {"expected_events": 273, "observed_events": None,
                "status": "unavailable", "reason": "funding response is not an event list"}
    seen, slots, unexpected, invalid_indices, duplicates, duplicate_slots = set(), set(), [], [], [], []
    offsets = []
    for index, row in enumerate(data):
        stamp = row.get("fundingTime") if isinstance(row, dict) else None
        if isinstance(stamp, bool) or not isinstance(stamp, int):
            invalid_indices.append(index)
            continue
        if stamp in seen:
            duplicates.append(stamp)
        seen.add(stamp)
        slot = min(expected, key=lambda value: abs(stamp - value))
        offset = abs(stamp - slot)
        offsets.append(offset)
        if START_MS <= stamp < END_MS and offset <= 5000:
            if slot in slots:
                duplicate_slots.append(slot)
            slots.add(slot)
        else:
            unexpected.append(stamp)
    missing = [stamp for stamp in expected if stamp not in slots]
    return {"status": "complete", "expected_events": 273, "observed_events": len(data),
            "matched_unique_slots": len(slots), "missing_slot_count": len(missing),
            "missing_canonical_slots_ms": missing, "unexpected_count": len(unexpected),
            "unexpected_timestamps_ms": unexpected, "duplicate_timestamps_ms": duplicates,
            "duplicate_canonical_slots_ms": duplicate_slots, "invalid_timestamp_row_indices": invalid_indices,
            "maximum_schedule_offset_ms": max(offsets) if offsets else None,
            "limitation": "Conditional 00/08/16 UTC +/-5s schedule; not historical calendar proof."}


def admit_response(request, body):
    """Semantic admission only; conditional schedule is not calendar proof."""
    data = json.loads(body)
    kind = request["kind"]
    if kind == "funding":
        if not isinstance(data, list) or len(data) != 91 * 3:
            raise ValueError("funding must contain all 273 conditional expected events")
        previous = None
        maximum_offset = 0
        for index, row in enumerate(data):
            if row["symbol"] != request["parameters"]["symbol"]:
                raise ValueError("funding symbol mismatch")
            stamp = _integer(row["fundingTime"], "fundingTime")
            if not START_MS <= stamp < END_MS or (previous is not None and stamp <= previous):
                raise ValueError("funding times must be unique increasing inside window")
            offset = abs(stamp - (START_MS + index * DAY_MS // 3))
            if offset > 5000:
                raise ValueError("funding does not match conditional 00/08/16 UTC schedule +/-5 seconds")
            maximum_offset = max(maximum_offset, offset)
            _number(row["fundingRate"], "fundingRate")
            _number(row["markPrice"], "event markPrice", positive=True)
            previous = stamp
        return {"status": "complete", "observations": len(data), "expected_events": 273,
                "schedule": "conditional 3/day 00/08/16 UTC +/-5 seconds; not historical calendar proof",
                "maximum_schedule_offset_ms": maximum_offset,
                "units": "signed funding rate and USDT mark price; event identity retained in raw body"}
    if kind in {"spot", "perp", "mark"}:
        if not isinstance(data, list) or len(data) != 91:
            raise ValueError("bars must contain exactly 91 daily observations")
        for index, row in enumerate(data):
            if not isinstance(row, list) or len(row) != 12:
                raise ValueError("bar schema must have 12 fields")
            expected = START_MS + index * DAY_MS
            if _integer(row[0], "openTime") != expected:
                raise ValueError("bar openTimes must be unique ordered complete UTC days")
            if _integer(row[6], "closeTime") != expected + DAY_MS - 1:
                raise ValueError("bar closeTime must end its UTC day")
            opn, high, low, close = [_number(value, "OHLC", positive=True) for value in row[1:5]]
            if not low <= min(opn, close) <= max(opn, close) <= high:
                raise ValueError("invalid OHLC ordering")
        return {"status": "complete", "observations": 91, "expected_days": 91,
                "clock": "UTC daily open inclusive, close next midnight minus 1ms",
                "units": "USDT price; public historical bars are not execution fills"}
    if kind == "exchange-info":
        if not isinstance(data, dict) or not isinstance(data.get("symbols"), list):
            raise ValueError("exchange metadata lacks symbols")
        admitted = []
        for symbol in ("BTCUSDT", "ETHUSDT"):
            rows = [row for row in data["symbols"] if row.get("symbol") == symbol]
            if len(rows) != 1:
                raise ValueError("required symbol metadata absent or duplicated")
            row = rows[0]
            if row.get("contractType") != "PERPETUAL" or row.get("quoteAsset") != "USDT" or row.get("marginAsset") != "USDT" or row.get("status") != "TRADING":
                raise ValueError("symbol is not currently active USDT perpetual")
            admitted.append(symbol)
        return {"status": "complete", "symbols": admitted,
                "limitation": "Current public metadata; not historical product state or account eligibility."}
    if kind == "server-time":
        stamp = _integer(data["serverTime"], "serverTime")
        if stamp <= 0:
            raise ValueError("invalid serverTime")
        return {"status": "complete", "server_time_ms": stamp,
                "limitation": "Current server clock; not proof of historical publication/availability."}
    raise ValueError("unregistered response kind")


def capture(spec, transport=public_get, persist_receipt=None):
    # Canonical bytes distinguish bool/int/float coercions that dict equality accepts.
    if json.dumps(spec, sort_keys=True) != json.dumps(frozen_request_spec(), sort_keys=True):
        raise ValueError("request_spec differs from exact frozen specification")
    receipts, admissions, cells, denied = [], [], [], set()
    for request in spec["requests"]:
        host = urllib.parse.urlsplit(request["url"]).hostname
        url = request["url"] + ("?" + urllib.parse.urlencode(request["parameters"])
                                 if request["parameters"] else "")
        start, before = _utc(), time.monotonic()
        attempted = host not in denied
        if attempted:
            try:
                response = transport(url)
            except http.client.IncompleteRead as exc:
                response = {"body": exc.partial[:MAX_BYTES], "http_status": None, "headers": {},
                            "error": "IncompleteRead: incomplete HTTP body; retained received prefix",
                            "body_complete": False}
            except (OSError, ValueError, http.client.HTTPException) as exc:
                response = {"body": b"", "http_status": None, "headers": {},
                            "error": type(exc).__name__ + ": " + str(exc), "body_complete": False}
        else:
            response = {"body": b"", "http_status": None, "headers": {},
                        "error": "not attempted after same-host HTTP denial", "body_complete": False}
        body = response["body"]
        if not isinstance(body, bytes):
            raise ValueError("transport body must be exact bytes")
        if len(body) > MAX_BYTES:
            body = body[:MAX_BYTES]
            response = {**response, "error": "response exceeds 5 MiB; retained exact prefix only",
                        "body_complete": False}
        if response["http_status"] in DENIALS:
            denied.add(host)
        receipt = {**request, "request_url": url, "request_utc": start,
                   "retrieval_utc": _utc(), "elapsed_seconds": time.monotonic() - before,
                   "attempted": attempted, "http_status": response["http_status"],
                   "headers": {name: value for name, value in response["headers"].items()
                               if name.lower() in {"date", "content-type"}},
                   "error": response["error"], "body_complete": response["body_complete"],
                   "body_bytes": len(body), "body_sha256": hashlib.sha256(body).hexdigest(),
                   "body_base64": base64.b64encode(body).decode("ascii")}
        receipts.append(receipt)
        # Immutable per-cell persistence precedes parsing and every later request.
        # A later process failure cannot erase already published receipt bytes.
        if persist_receipt is not None:
            persist_receipt(request["id"] + "-receipt.json", receipt)
        if response["error"] or response["http_status"] != 200 or not response["body_complete"]:
            result = {"status": "unavailable", "reason": response["error"] or "HTTP/body incomplete"}
        else:
            try:
                result = admit_response(request, body)
            except (ValueError, KeyError, TypeError, OverflowError, AttributeError) as exc:
                result = {"status": "unavailable", "reason": type(exc).__name__ + ": " + str(exc)}
        if request["kind"] == "funding":
            try:
                result["coverage"] = funding_coverage(json.loads(body))
            except (ValueError, TypeError):
                result["coverage"] = {"status": "unavailable", "expected_events": 273,
                                      "observed_events": None, "reason": "no parseable event list"}
        if request["kind"] == "server-time" and result["status"] == "complete":
            lower = int(datetime.fromisoformat(receipt["request_utc"]).timestamp() * 1000) - 5000
            upper = int(datetime.fromisoformat(receipt["retrieval_utc"]).timestamp() * 1000) + 5000
            stamp = result["server_time_ms"]
            result["clock_check"] = {"earliest_allowed_ms": lower, "latest_allowed_ms": upper,
                                     "server_minus_request_ms": stamp - (lower + 5000),
                                     "server_minus_retrieval_ms": stamp - (upper - 5000),
                                     "agrees": lower <= stamp <= upper}
            if not lower <= stamp <= upper:
                result.update(status="unavailable", reason="server clock outside request/retrieval interval +/-5 seconds")
        admissions.append({"id": request["id"], **result})
        cells.append({"id": request["id"], "status": result["status"],
                      **({"reason": result["reason"]} if result["status"] == "unavailable" else {})})
    return ({"schema_version": 1, "request_spec": spec, "requests": receipts,
             "total_body_bytes": sum(row["body_bytes"] for row in receipts)},
            {"schema_version": 1, "cells": admissions,
             "interpretation": "Data availability only; no PnL, fresh confirmation, historical calendar or account eligibility claim."},
            cells)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2], registration=REGISTRATION,
                           experiment=EXPERIMENT, source=args.source) as run:
        raw, admission, cells = capture(json.loads(run.read_input("request_spec")),
                                        persist_receipt=run.write_json)
        run.write_json("capture.json", raw)
        run.write_json("admission.json", admission)
        run.finish(cells)


if __name__ == "__main__":
    main()
