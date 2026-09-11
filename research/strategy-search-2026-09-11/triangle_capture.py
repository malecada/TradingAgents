"""Six frozen public triangle input requests; source admission, never PnL."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
import urllib.parse

from tradingagents.research import ResearchRun
from options_metadata import strict_json, lifecycle_bytes, transport_module

SPEC_CANONICAL_SHA256 = "15736490d3e219f0a8ac28c382acc65b4ec309febd5ca9e4bf068580d0c7abf8"
REGISTRATION = "research/strategy-search-2026-09-11/gates-triangle-inputs.json"
EXPERIMENT = "triangle-inputs-20260911"
PAIRS = {"BTCUSDT": ("BTC", "USDT"), "ETHUSDT": ("ETH", "USDT"), "ETHBTC": ("ETH", "BTC")}
SCOPE = "Asynchronously observed public inputs only; no cross-source alignment, fills, fees, cash profit or graduation."


def _positive(value):
    if isinstance(value, bool):
        raise ValueError("boolean price/quantity is invalid")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError("finite positive price/quantity required")
    return result


def _symbol_rows(rows):
    if not isinstance(rows, list) or len(rows) != 3 or any(not isinstance(row, dict) for row in rows):
        raise ValueError("exact three-symbol object list required")
    if {row["symbol"] for row in rows} != set(PAIRS):
        raise ValueError("requested symbol identities absent or duplicated")
    return {row["symbol"]: row for row in rows}


def parse_response(raw, request):
    kind = request["kind"]
    # The wrapper preserves strict duplicate/nonfinite checks for array roots.
    if kind == "book-ticker":
        wrapped = strict_json(b'{"items":' + raw + b'}')
        if set(wrapped) != {"items"}:
            raise ValueError("ticker body must be one standalone JSON array")
        data = wrapped["items"]
    else:
        data = strict_json(raw)
    if isinstance(data, dict) and "code" in data:
        raise ValueError("API error object is unavailable")
    if kind == "exchange-info":
        rows = _symbol_rows(data.get("symbols"))
        rules = {}
        for symbol, row in rows.items():
            if (row.get("baseAsset"), row.get("quoteAsset")) != PAIRS[symbol]:
                raise ValueError("symbol base/quote identity mismatch")
            if row.get("status") != "TRADING" or row.get("isSpotTradingAllowed") is not True:
                raise ValueError("symbol does not meet conditional current spot-availability prerequisite")
            filters = row.get("filters")
            if filters is not None and (not isinstance(filters, list) or any(not isinstance(item, dict) or not isinstance(item.get("filterType"), str) or not item["filterType"] for item in filters)):
                raise ValueError("filters must be objects with named filterType")
            names = [item["filterType"] for item in filters or []]
            missing = [name for name in ("LOT_SIZE", "MARKET_LOT_SIZE") if name not in names]
            if not {"MIN_NOTIONAL", "NOTIONAL"}.intersection(names):
                missing.append("MIN_NOTIONAL-or-NOTIONAL")
            rules[symbol] = {"status": "unavailable", "observed_filter_types": names,
                             "missing_relevant_filters": missing,
                             "reason": "Actual lot/notional/market-order filter interpretation and personal access are not admitted."}
        return {"status": "complete", "symbols": rows, "additional_metadata": {key: value for key, value in data.items() if key != "symbols"},
                "pair_availability": "conditional current metadata only", "filter_interpretation": rules, "scope": SCOPE}
    if kind == "server-time":
        if type(data.get("serverTime")) is not int or data["serverTime"] <= 0:
            raise ValueError("positive integer serverTime required")
        return {"status": "complete", "raw_fields": data, "scope": "Returned server clock only; no synchronization or historical-publication inference."}
    if kind == "book-ticker":
        rows = _symbol_rows(data)
        for row in rows.values():
            values = {name: _positive(row[name]) for name in ("bidPrice", "askPrice", "bidQty", "askQty")}
            if values["bidPrice"] > values["askPrice"]:
                raise ValueError("crossed best bid/ask")
        return {"status": "complete", "quotes": rows, "scope": SCOPE}
    if kind == "depth":
        if type(data.get("lastUpdateId")) is not int or data["lastUpdateId"] < 0:
            raise ValueError("nonnegative integer depth lastUpdateId required")
        prices = {}
        for side in ("bids", "asks"):
            levels = data.get(side)
            if not isinstance(levels, list) or not 1 <= len(levels) <= 20:
                raise ValueError("one to twenty levels required on each side")
            if any(not isinstance(level, list) or len(level) != 2 for level in levels):
                raise ValueError("each level must contain exactly price and quantity")
            prices[side] = [_positive(level[0]) for level in levels]
            for level in levels:
                _positive(level[1])
            if side == "bids" and any(a <= b for a, b in zip(prices[side], prices[side][1:])):
                raise ValueError("bid prices must be strictly descending")
            if side == "asks" and any(a >= b for a, b in zip(prices[side], prices[side][1:])):
                raise ValueError("ask prices must be strictly ascending")
        if prices["bids"][0] > prices["asks"][0]:
            raise ValueError("crossed depth best bid/ask")
        return {"status": "complete", "symbol": request["symbol"], "raw_fields": data,
                "observed_bid_levels": len(data["bids"]), "observed_ask_levels": len(data["asks"]),
                "scope": "Depth20 bounded asynchronous observation, not a complete book or fill; lastUpdateId is not a timestamp."}
    raise ValueError("unregistered request kind")


def capture(spec, transport=transport_module.public_get, persist_receipt=None):
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if hashlib.sha256(canonical).hexdigest() != SPEC_CANONICAL_SHA256:
        raise ValueError("triangle request specification differs from frozen definition")
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
        if response["error"] or response["http_status"] != 200 or not response["body_complete"]:
            result = {"status": "unavailable", "reason": response["error"] or "incomplete HTTP response"}
        else:
            try:
                result = parse_response(body, request)
                size = len(lifecycle_bytes({"cells": [{"id": request["id"], **result}]}))
                if normalization + size > spec["max_admission_bytes"]:
                    raise ValueError("pretty-encoded normalized admission exceeds 12 MiB")
            except MemoryError:
                raise
            except Exception as exc:
                result = {"status": "unavailable", "reason": type(exc).__name__ + ": " + str(exc)}
        results.append({"id": request["id"], **result})
        normalization += len(lifecycle_bytes({"cells": [results[-1]]}))
    raw = {"schema_version": 1, "request_spec": spec, "requests": receipts,
           "total_body_bytes": sum(row["body_bytes"] for row in receipts)}
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
        registered.write_json("triangle-capture.json", raw)
        registered.write_json("triangle-admission.json", admission)
        registered.finish(cells)


if __name__ == "__main__":
    main()
