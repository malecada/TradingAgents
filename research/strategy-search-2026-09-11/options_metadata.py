"""Frozen current options/catalogue metadata only; no financial measurements."""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET

from tradingagents.research import ResearchRun

_spec = importlib.util.spec_from_file_location("options_metadata_transport", Path(__file__).with_name("carry_capture.py"))
transport_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(transport_module)
SPEC_CANONICAL_SHA256 = "6d71be815eeb57271a61f656d0712cc16719aab65861447f22dc31d213297143"
REGISTRATION = "research/strategy-search-2026-09-11/gates-options-metadata.json"
EXPERIMENT = "options-metadata-20260911"
FIELDS = ("symbol", "underlying", "underlyingType", "contractType", "expiryDate", "side", "unit", "minQty", "maxQty",
          "status", "initialMargin", "maintenanceMargin", "minInitialMargin", "minMaintenanceMargin", "nakedSell", "filters")
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
ADMISSION_SCOPE = "Metadata admission only; no fees, PnL, affordability, quotes, Greeks or adoption."


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def lifecycle_bytes(value):
    """Exactly the frozen ResearchRun JSON encoding, including final newline."""
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def enforce_one_cpu():
    os.sched_setaffinity(0, [min(os.sched_getaffinity(0))])


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key: " + key)
        result[key] = value
    return result


def _float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("nonfinite JSON number")
    return value


def _constant(text):
    raise ValueError("nonfinite JSON constant: " + text)


def strict_json(raw):
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_float=_float, parse_constant=_constant)
    if not isinstance(value, dict):
        raise ValueError("JSON object root required")
    return value


def _decimal(value, *, positive):
    try:
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise ValueError("invalid decimal type")
        number = Decimal(str(value))
        if not number.is_finite() or number < 0 or (positive and number == 0):
            raise ValueError("invalid decimal sign/value")
    except (ValueError, InvalidOperation):
        return {"status": "unavailable", "reason": "positive finite decimal required" if positive else "finite nonnegative decimal required"}
    return {"status": "complete", "value": str(number)}


def _field(row, name, positive=True):
    return _decimal(row[name], positive=positive) if name in row else {"status": "unavailable", "reason": "field absent"}


def parse_exchange_info(raw, *, deadline=None, output_budget=12 * 1024 * 1024):
    data = strict_json(raw)
    if "code" in data or "optionSymbols" not in data or not isinstance(data["optionSymbols"], list) or any(not isinstance(row, dict) for row in data["optionSymbols"]):
        raise ValueError("exchange information must contain optionSymbols object list, not an API error")
    symbols = data["optionSymbols"]
    identities = Counter(row["symbol"] for row in symbols if isinstance(row.get("symbol"), str))
    normalized, target_indices, allocated = [], [], 0
    for index, row in enumerate(symbols):
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("metadata normalization wall budget reached")
        quantity = {name: _field(row, name) for name in ("unit", "minQty", "maxQty")}
        margins = {name: _field(row, name, False) for name in ("initialMargin", "maintenanceMargin", "minInitialMargin", "minMaintenanceMargin")}
        ambiguity = []
        if isinstance(row.get("symbol"), str) and identities[row["symbol"]] > 1:
            ambiguity.append("duplicate symbol identity")
        filters = row.get("filters")
        lots = [item for item in filters if isinstance(item, dict) and item.get("filterType") == "LOT_SIZE"] if isinstance(filters, list) else []
        if not isinstance(filters, list) or any(not isinstance(item, dict) for item in filters):
            ambiguity.append("filters missing or invalid")
        if len(lots) != 1:
            ambiguity.append("missing or duplicate LOT_SIZE filters")
        lot_rules = [{name: _field(item, name) for name in ("minQty", "maxQty", "stepSize")} for item in lots]
        for values in (quantity, *lot_rules):
            if all(values[name]["status"] == "complete" for name in ("minQty", "maxQty")) and Decimal(values["minQty"]["value"]) > Decimal(values["maxQty"]["value"]):
                ambiguity.append("minQty exceeds maxQty")
        if len(lot_rules) == 1:
            for name in ("minQty", "maxQty"):
                if quantity[name]["status"] == lot_rules[0][name]["status"] == "complete" and Decimal(quantity[name]["value"]) != Decimal(lot_rules[0][name]["value"]):
                    ambiguity.append("top-level/LOT_SIZE conflict: " + name)
        if any(item["status"] != "complete" for item in quantity.values()) or any(item["status"] != "complete" for rules in lot_rules for item in rules.values()):
            ambiguity.append("missing or invalid quantity fields")
        expiry = row.get("expiryDate")
        target = row.get("underlying") in ("BTCUSDT", "ETHUSDT")
        result = {"row_index": index, "raw_fields": row, "explicit_btc_eth_target": target,
                  "field_availability": {name: "present" if name in row else "unavailable" for name in FIELDS},
                  "quantity_fields": quantity, "lot_size_filters": lot_rules,
                  "quantity_rule_status": "ambiguous" if ambiguity else "complete",
                  "ambiguities": ambiguity, "margin_fields": margins,
                  "expiry_status": "complete" if type(expiry) is int and expiry > 0 else "unavailable",
                  "crypto_classification": {"status": "ambiguous", "underlyingType": row.get("underlyingType"),
                      "contractType": row.get("contractType"), "reason": "Literal discriminators retained; no enum interpretation frozen."},
                  "account_seller_permission": "unavailable; nakedSell is symbol metadata only"}
        # Preserve raw bytes regardless of normalization resource admission.
        # Count actual nested indentation; repeating each envelope overcounts
        # rather than omitting indentation when rows are combined into one file.
        allocated += len(lifecycle_bytes({"cells": [{"normalized_symbol_rows": [result]}]}))
        if allocated > output_budget:
            raise ValueError("normalized metadata exceeds retained-output resource allowance")
        normalized.append(result)
        if target:
            target_indices.append(index)
    contracts = data.get("optionContracts")
    contract_status = "complete" if isinstance(contracts, list) and all(isinstance(row, dict) for row in contracts) else "unavailable"
    contract_rows = []
    for index, row in enumerate(contracts if isinstance(contracts, list) else []):
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("contract metadata normalization wall budget reached")
        metadata = {"row_index": index, "field_availability": {
            name: "present" if isinstance(row, dict) and name in row else "unavailable"
            for name in ("underlying", "underlyingType", "contractType")}}
        allocated += len(lifecycle_bytes({"cells": [{"optionContracts": {"row_metadata_availability": [metadata]}}]}))
        if allocated > output_budget:
            raise ValueError("normalized metadata exceeds retained-output resource allowance")
        contract_rows.append(metadata)
    return {"status": "complete", "symbol_count": len(symbols), "normalized_symbol_rows": normalized,
            "target_row_indices": target_indices, "explicit_btc_eth_target_count": len(target_indices),
            "optionContracts": {"status": contract_status, "literal_value": contracts, "row_metadata_availability": contract_rows},
            "scope": "Actual returned metadata only; target identity uses explicit underlying, no inferred enum, affordability or account permission."}


def _one(element, name, required=True):
    values = element.findall(NS + name)
    if len(values) > 1 or (required and len(values) != 1):
        raise ValueError("missing/duplicate S3 field: " + name)
    return (values[0].text or "") if values else None


def parse_listing(raw, request):
    text = raw.decode("utf-8")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, re.IGNORECASE):
        raise ValueError("DTD/entity declarations prohibited")
    root = ET.fromstring(text)
    if root.tag != NS + "ListBucketResult":
        raise ValueError("S3 namespaced ListBucketResult required")
    prefix, maximum, delimiter = _one(root, "Prefix"), _one(root, "MaxKeys"), _one(root, "Delimiter", False)
    if prefix != request["prefix"] or not re.fullmatch(r"\d+", maximum) or int(maximum) != request["max_keys"]:
        raise ValueError("S3 prefix/max-keys differs from request")
    delimiter_mismatch = delimiter != request["delimiter"] if "delimiter" in request else delimiter not in (None, "")
    if delimiter_mismatch:
        raise ValueError("S3 delimiter differs from request")
    truncated = _one(root, "IsTruncated")
    if truncated not in ("true", "false"):
        raise ValueError("explicit boolean IsTruncated required")
    common, contents = [], []
    for item in root.findall(NS + "CommonPrefixes"):
        value = _one(item, "Prefix")
        if "delimiter" not in request or not value.startswith(prefix) or len(value) <= len(prefix) or not value.endswith(request["delimiter"]) or "/" in value[len(prefix):-1]:
            raise ValueError("CommonPrefix outside requested delimiter scope")
        common.append(value)
    for item in root.findall(NS + "Contents"):
        key, size = _one(item, "Key"), _one(item, "Size")
        if not key.startswith(prefix) or not re.fullmatch(r"\d+", size):
            raise ValueError("object key outside prefix or invalid size")
        if "delimiter" in request and request["delimiter"] in key[len(prefix):]:
            raise ValueError("Contents key violates requested delimiter semantics")
        contents.append({"Key": key, "Size": int(size), "LastModified": _one(item, "LastModified", False),
                         "ETag": _one(item, "ETag", False)})
    if len(common) + len(contents) > request["max_keys"] or len(set(common)) != len(common) or len({row["Key"] for row in contents}) != len(contents):
        raise ValueError("listing exceeds max-keys or duplicates identities")
    continuation = {name: _one(root, name, False) for name in ("Marker", "NextMarker", "ContinuationToken", "NextContinuationToken", "StartAfter", "KeyCount", "EncodingType")}
    return {"status": "complete", "prefix": prefix, "max_keys": int(maximum), "delimiter": delimiter,
            "is_truncated": truncated == "true", "partial_listing": truncated == "true",
            "common_prefixes": common, "contents": contents, "continuation_metadata": continuation,
            "scope": "Exact query response only; initial object listing is a lexical slice, not a representative sample. No global absence or chain completeness inference.",
            "provenance_limits": "LastModified is current object-version metadata; ETag is not SHA256; names do not establish body schema or executable quotes."}


def parse_response(raw, request, *, deadline=None, output_budget=12 * 1024 * 1024):
    if request["kind"] == "exchange-info":
        return parse_exchange_info(raw, deadline=deadline, output_budget=output_budget)
    if request["kind"] == "server-time":
        data = strict_json(raw)
        if "code" in data or type(data.get("serverTime")) is not int:
            raise ValueError("integer serverTime required; API errors are unavailable")
        return {"status": "complete", "serverTime": data["serverTime"], "scope": "Returned clock only; no synchronization/publication inference."}
    return parse_listing(raw, request)


def capture(spec, transport=transport_module.public_get, persist_receipt=None):
    if hashlib.sha256(_canonical(spec)).hexdigest() != SPEC_CANONICAL_SHA256:
        raise ValueError("request_spec differs from exact frozen options metadata specification")
    started = time.monotonic()
    deadline = started + spec["max_wall_seconds"]
    receipts, results, denied, received, normalized_bytes = [], [], set(), 0, 0
    for request in spec["requests"]:
        host = urllib.parse.urlsplit(request["url"]).hostname
        before, request_utc = time.monotonic(), _utc()
        reason = ("not attempted after same-host HTTP denial" if host in denied else
                  "not attempted: remaining resource budget cannot admit full request" if before + 20 > deadline or received + spec["max_response_bytes"] > spec["max_total_response_bytes"] else None)
        response = transport(request["url"]) if reason is None else {"body": b"", "http_status": None, "headers": {}, "body_complete": False, "error": reason}
        body = response["body"]
        if not isinstance(body, bytes):
            raise ValueError("transport body must be bytes")
        if len(body) > spec["max_response_bytes"]:
            body = body[:spec["max_response_bytes"]]
            response = {**response, "error": "response exceeds 5 MiB; retained prefix", "body_complete": False}
        received += len(body)
        if response["http_status"] in transport_module.DENIALS:
            denied.add(host)
        receipt = {**request, "request_utc": request_utc, "retrieval_utc": _utc(), "elapsed_seconds": time.monotonic() - before,
                   "attempted": reason is None, "http_status": response["http_status"], "error": response["error"],
                   "body_complete": response["body_complete"], "body_bytes": len(body),
                   "body_sha256": hashlib.sha256(body).hexdigest(), "body_base64": base64.b64encode(body).decode(),
                   "headers": {name: value for name, value in response["headers"].items() if name.lower() in ("date", "content-type")}}
        receipts.append(receipt)
        if persist_receipt is not None:
            persist_receipt(request["id"] + "-receipt.json", receipt)
        if response["error"] or response["http_status"] != 200 or not response["body_complete"]:
            result = {"status": "unavailable", "reason": response["error"] or "incomplete HTTP response"}
        else:
            try:
                remaining = 12 * 1024 * 1024 - normalized_bytes
                result = parse_response(body, request, deadline=deadline, output_budget=remaining)
                if len(lifecycle_bytes({"cells": [{"id": request["id"], **result}]})) > remaining:
                    raise ValueError("metadata exceeds retained-output resource allowance")
            except MemoryError:
                raise  # Process/resource failure is not recoverable admission.
            except Exception as exc:
                result = {"status": "unavailable", "reason": type(exc).__name__ + ": " + str(exc)}
        results.append({"id": request["id"], **result})
        normalized_bytes += len(lifecycle_bytes({"cells": [results[-1]]}))
    cells = [{"id": row["id"], "status": row["status"], **({"reason": row["reason"]} if row["status"] == "unavailable" else {})} for row in results]
    raw = {"schema_version": 1, "request_spec": spec, "requests": receipts, "total_body_bytes": received}
    admission = {"schema_version": 1, "cells": results, "scope": ADMISSION_SCOPE}
    total_output_bytes = sum(len(lifecycle_bytes(row)) for row in receipts) + len(lifecycle_bytes(raw)) + len(lifecycle_bytes(admission))
    if total_output_bytes > spec["max_output_bytes"]:
        # Raw receipts already exist; discard only oversized normalization from
        # this new result, preserving the complete raw source denominator.
        results = [{"id": row["id"], "status": "unavailable", "reason": "actual lifecycle-encoded output budget exceeded"} for row in results]
        admission = {"schema_version": 1, "cells": results, "scope": ADMISSION_SCOPE}
        cells = list(results)
        total_output_bytes = sum(len(lifecycle_bytes(row)) for row in receipts) + len(lifecycle_bytes(raw)) + len(lifecycle_bytes(admission))
        if total_output_bytes > spec["max_output_bytes"]:
            raise RuntimeError("raw receipt/envelope bytes exceed output budget; prior receipts retained")
    return raw, admission, cells


def main():
    enforce_one_cpu()
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
