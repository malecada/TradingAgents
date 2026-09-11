"""Two frozen WBETH source requests; no financial calculation."""
from __future__ import annotations

import argparse
import base64
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
import urllib.parse

from tradingagents.research import ResearchRun
from options_metadata import strict_json, lifecycle_bytes, transport_module

SPEC_CANONICAL_SHA256 = "58104f4558710b80fd1228406dae9fe2777aad4f41ef2927bbfc904c051e4ead"
REGISTRATION = "research/strategy-search-2026-09-11/gates-wbeth-inputs.json"
EXPERIMENT = "wbeth-inputs-20260911"
SCOPE = "Fixed raw WBETH spot bars and current metadata only; no return, staking attribution, profit, fills or graduation."


START_MS = 1775001600000
DAY_MS = 86400000


def _number(value, positive=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("numeric field type invalid")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid decimal field") from exc
    if not number.is_finite() or number < 0 or (positive and number == 0):
        raise ValueError("nonfinite or nonpositive source number")
    return number


def parse_response(raw, request):
    if request["kind"] == "exchange-info":
        data = strict_json(raw)
        if "code" in data or not isinstance(data.get("symbols"), list) or len(data["symbols"]) != 1:
            raise ValueError("exact one-symbol exchange metadata required")
        row = data["symbols"][0]
        if not isinstance(row, dict) or any(row.get(key) != value for key, value in
                {"symbol":"WBETHUSDT", "baseAsset":"WBETH", "quoteAsset":"USDT", "status":"TRADING"}.items()):
            raise ValueError("WBETHUSDT active source identity unavailable")
        if row.get("isSpotTradingAllowed") is not True:
            raise ValueError("explicit spot-enabled source field required")
        filters = row.get("filters")
        if not isinstance(filters, list) or not filters or any(not isinstance(f, dict) or not isinstance(f.get("filterType"), str) for f in filters):
            raise ValueError("literal filter objects required")
        if len({f["filterType"] for f in filters}) != len(filters):
            raise ValueError("duplicate filter identity")
        return {"status":"complete", "symbol_metadata":row,
                "qualification":"Current literal filters only; no historical rule, fee, lot interpretation or account entitlement.","scope":SCOPE}
    if request["kind"] != "spot":
        raise ValueError("unregistered source kind")
    wrapped = strict_json(b'{"items":' + raw + b'}')
    if set(wrapped) != {"items"} or not isinstance(wrapped["items"], list) or len(wrapped["items"]) != 91:
        raise ValueError("standalone complete 91-day array required")
    zero_activity = []
    for index, row in enumerate(wrapped["items"]):
        if not isinstance(row, list) or len(row) != 12:
            raise ValueError("exact 12-field bar required")
        stamp = START_MS + index * DAY_MS
        if type(row[0]) is not int or type(row[6]) is not int or row[0] != stamp or row[6] != stamp + DAY_MS - 1:
            raise ValueError("nonconsecutive or invalid daily clocks")
        op, high, low, close = [_number(v, positive=True) for v in row[1:5]]
        if not low <= min(op, close) <= max(op, close) <= high:
            raise ValueError("invalid OHLC ordering")
        volume, quote, taker, taker_quote = [_number(row[i]) for i in (5,7,9,10)]
        if type(row[8]) is not int or row[8] < 0:
            raise ValueError("nonnegative integer trade count required")
        if volume == 0 or row[8] == 0:
            zero_activity.append(index)
    return {"status":"complete", "observations":91, "expected_days":91,
            "start_ms":START_MS, "end_exclusive_ms":START_MS+91*DAY_MS,
            "zero_activity_row_indices":zero_activity,"row_index_base":0,
            "qualification":"Complete daily source clocks; zero activity retained, not realized fills or first-publication proof.","scope":SCOPE}


def capture(spec, transport=transport_module.public_get, persist_receipt=None):
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if hashlib.sha256(canonical).hexdigest() != SPEC_CANONICAL_SHA256:
        raise ValueError("WBETH request specification differs from frozen definition")
    deadline = time.monotonic() + spec["cooperative_seconds"]
    receipts, results, denied = [], [], set()
    normalization = 0
    for request in spec["requests"]:
        before = time.monotonic()
        clock = datetime.now(timezone.utc).isoformat()
        host = urllib.parse.urlsplit(request["url"]).hostname
        reason = ("not attempted after same-host HTTP denial" if host in denied else
                  "not attempted: insufficient cooperative request time budget" if before + spec["timeout_seconds"] > deadline else None)
        response = transport(request["url"]) if reason is None else {"body": b"", "http_status": None, "headers": {}, "body_complete": False, "error": reason}
        body = response["body"]
        if not isinstance(body, bytes):
            raise ValueError("transport must preserve bytes")
        if len(body) > spec["max_response_bytes"]:
            body = body[:spec["max_response_bytes"]]
            response = {**response, "error": "response exceeds 5 MiB; retained prefix", "body_complete": False}
        if response["http_status"] in transport_module.DENIALS:
            denied.add(host)
        receipt = {**request, "attempted": reason is None, "request_utc": clock,
                   "retrieval_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": time.monotonic() - before,
                   "http_status": response["http_status"], "headers": {name: value for name, value in response["headers"].items() if name.lower() in ("date", "content-type")},
                   "error": response["error"], "body_complete": response["body_complete"], "body_bytes": len(body),
                   "body_sha256": hashlib.sha256(body).hexdigest(), "body_base64": base64.b64encode(body).decode()}
        receipts.append(receipt)
        if persist_receipt is not None:
            persist_receipt(request["id"] + "-receipt.json", receipt)
        if response["error"] is not None or type(response["http_status"]) is not int or response["http_status"] != 200 or response["body_complete"] is not True:
            result = {"status": "unavailable", "reason": response["error"] or "incomplete HTTP response"}
        else:
            try:
                result = parse_response(body, request)
                size = len(lifecycle_bytes({"cells": [{"id": request["id"], **result}]}))
                if normalization + size > spec["max_admission_bytes"]:
                    raise ValueError("pretty-encoded normalized admission exceeds 10 MiB")
            except MemoryError:
                raise
            except Exception as exc:
                result = {"status": "unavailable", "reason": type(exc).__name__ + ": " + str(exc)}
        results.append({"id": request["id"], **result})
        normalization += len(lifecycle_bytes({"cells": [results[-1]]}))
    raw = {"schema_version": 1, "request_spec": spec, "requests": receipts,
           "total_body_bytes": sum(row["body_bytes"] for row in receipts)}
    admission = {"schema_version": 1, "cells": results, "scope": SCOPE}
    if len(lifecycle_bytes(admission)) > spec["max_admission_bytes"]:
        results = [{"id": row["id"], "status": "unavailable", "reason": "actual normalized admission byte cap exceeded"} for row in results]
        admission = {"schema_version": 1, "cells": results, "scope": SCOPE}
    output_bytes = sum(len(lifecycle_bytes(row)) for row in receipts) + len(lifecycle_bytes(raw)) + len(lifecycle_bytes(admission))
    if output_bytes > spec["max_output_bytes"]:
        results = [{"id": row["id"], "status": "unavailable", "reason": "actual lifecycle-encoded output budget exceeded"} for row in results]
        admission = {"schema_version": 1, "cells": results, "scope": SCOPE}
        output_bytes = sum(len(lifecycle_bytes(row)) for row in receipts) + len(lifecycle_bytes(raw)) + len(lifecycle_bytes(admission))
        if output_bytes > spec["max_output_bytes"]:
            raise RuntimeError("raw receipt/envelope bytes exceed output bound; prior receipts retained")
    cells = [{"id": row["id"], "status": row["status"], **({"reason": row["reason"]} if row["status"] == "unavailable" else {})} for row in results]
    return raw, admission, cells


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2], registration=REGISTRATION,
                           experiment=EXPERIMENT, source=args.source) as registered:
        raw, admission, cells = capture(strict_json(registered.read_input("request_spec")), persist_receipt=registered.write_json)
        registered.write_json("wbeth-capture.json", raw)
        registered.write_json("wbeth-admission.json", admission)
        registered.finish(cells)


if __name__ == "__main__":
    main()
