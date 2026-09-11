"""Two frozen Bitrue public metadata requests; no financial calculation."""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
import urllib.parse

from tradingagents.research import ResearchRun
from options_metadata import strict_json, lifecycle_bytes, transport_module

SPEC_CANONICAL_SHA256 = "5448142a2237f77c275eb89d8a5c746c8a9ec2f571a67af25527ce91f3244073"
REGISTRATION = "research/strategy-search-2026-09-11/gates-bitrue-metadata.json"
EXPERIMENT = "bitrue-metadata-20260911"
SCOPE = "Public literal contract metadata only; no prices, funding, profit, account eligibility or graduation."


def _positive(value, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("positive finite metadata number required")
    number = float(value)
    if not math.isfinite(number) or number < 0 or (number == 0 and not allow_zero):
        raise ValueError("positive finite metadata number required")


def parse_response(raw, request):
    if request["kind"] == "server-time":
        data = strict_json(raw)
        if "code" in data:
            raise ValueError("API error object is unavailable")
        return {"status": "complete", "raw_fields": data,
                "clock_semantics": {"status": "unavailable", "reason": "Official schema specifies an arbitrary object; no clock field or units are admitted."}, "scope": SCOPE}
    if request["kind"] != "contracts":
        raise ValueError("unregistered request kind")
    wrapped = strict_json(b'{"items":' + raw + b'}')
    if set(wrapped) != {"items"} or not isinstance(wrapped["items"], list):
        raise ValueError("documented standalone contract array required")
    rows = wrapped["items"]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("every contract row must be an object")
    names = Counter(row["symbol"] for row in rows if isinstance(row.get("symbol"), str))
    if sum(names.values()) != len(rows) or any(not name for name in names) or any(count != 1 for count in names.values()):
        raise ValueError("unique nonempty literal contract symbols required")
    statuses = []
    for index, row in enumerate(rows):
        problems = []
        for field in ("symbol", "type", "multiplierCoin"):
            if not isinstance(row.get(field), str) or not row[field]:
                problems.append(field + " missing or invalid")
        for field in ("side", "status"):
            if type(row.get(field)) is not int or row[field] not in (0, 1):
                problems.append(field + " undocumented or invalid")
        for field in ("multiplier", "minOrderVolume", "minOrderMoney"):
            try:
                _positive(row.get(field), allow_zero=field == "minOrderMoney")
            except (ValueError, TypeError, OverflowError):
                problems.append(field + " missing or invalid")
        name = row.get("symbol")
        if isinstance(name, str) and names[name] > 1:
            problems.append("duplicate contract name")
        asset = {"E-BTC-USDT": "BTC", "E-ETH-USDT": "ETH"}.get(name) if isinstance(name, str) else None
        match = not problems and asset is not None and row["multiplierCoin"] == asset and row["type"] == "E" and row["side"] == 1 and row["status"] == 1
        statuses.append({"row_index": index, "metadata_status": "complete" if not problems else "unavailable",
                         "problems": problems, "conditional_target_asset": asset if match else None,
                         "target_mapping": "conditional literal naming/unit match" if match else "ambiguous or outside fixed target mapping",
                         "account_eligibility": "unavailable"})
    return {"status": "complete", "contract_rows": rows, "row_metadata": statuses,
            "observed_rows": len(rows), "target_mapping_scope": "Exact E-BTC-USDT/E-ETH-USDT names, matching base face-value unit, perpetual type E, forward side1, status1 only; no lot arithmetic or trading permission.",
            "scope": SCOPE}


def capture(spec, transport=transport_module.public_get, persist_receipt=None):
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if hashlib.sha256(canonical).hexdigest() != SPEC_CANONICAL_SHA256:
        raise ValueError("Bitrue request specification differs from frozen definition")
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
        registered.write_json("metadata-capture.json", raw)
        registered.write_json("metadata-admission.json", admission)
        registered.finish(cells)


if __name__ == "__main__":
    main()
