"""Registered forced static triangle proxies; no quotes fetched and no orders."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

from tradingagents.research import ResearchRun
from options_metadata import strict_json, lifecycle_bytes
import triangle_capture
import triangle_bound

REGISTRATION = "research/strategy-search-2026-09-11/gates-triangle-proxy.json"
EXPERIMENT = "triangle-proxy-20260911"
MAX_OUTPUT_BYTES = 2 * 1024**2
REQUIRED = ("triangle-exchange-info", "triangle-book-ticker")
SOURCE_IDS = ("triangle-exchange-info", "triangle-server-time", "triangle-book-ticker",
              "triangle-btcusdt-depth", "triangle-ethusdt-depth", "triangle-ethbtc-depth")


def _index(rows):
    if not isinstance(rows, list) or len(rows) != 6 or any(not isinstance(row, dict) for row in rows) or {row["id"] for row in rows} != set(SOURCE_IDS):
        raise ValueError("exact six-cell parent source denominator required")
    return {row["id"]: row for row in rows}


def decode_sources(capture, admission):
    spec = capture["request_spec"]
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if hashlib.sha256(canonical).hexdigest() != triangle_capture.SPEC_CANONICAL_SHA256:
        raise ValueError("parent request specification differs from frozen source definition")
    expected = {request["id"]: request for request in spec["requests"]}
    records, admitted = _index(capture["requests"]), _index(admission["cells"])
    parsed, availability = {}, {}
    for identifier in SOURCE_IDS:
        record, parent = records[identifier], admitted[identifier]
        state = {"id": identifier, "required_for_static_proxy": identifier in REQUIRED,
                 "parent_status": parent.get("status"),
                 "request_utc": record.get("request_utc"), "retrieval_utc": record.get("retrieval_utc"),
                 "raw_integrity_status": "unavailable", "schema_status": "unavailable"}
        try:
            if any(record.get(key) != value for key, value in expected[identifier].items()):
                raise ValueError("receipt request identity differs from frozen specification")
            raw = base64.b64decode(record["body_base64"], validate=True)
            if type(record["body_bytes"]) is not int or len(raw) != record["body_bytes"] or len(raw) > spec["max_response_bytes"] or hashlib.sha256(raw).hexdigest() != record["body_sha256"]:
                raise ValueError("raw parent body hash/size mismatch")
            state["raw_integrity_status"] = "complete"
            if type(record["http_status"]) is not int or record["http_status"] != 200 or record.get("attempted") is not True or record["body_complete"] is not True or record["error"] is not None:
                raise ValueError("parent HTTP response unavailable/incomplete")
            result = triangle_capture.parse_response(raw, expected[identifier])
            if result["status"] != "complete":
                raise ValueError("parent raw schema is unavailable")
            state["schema_status"] = "complete"
            if parent.get("status") != "complete":
                raise ValueError("parent source admission unavailable: " + str(parent.get("reason", "no complete admission")))
            expected_parent = {"id": identifier, **result}
            if json.dumps(parent, sort_keys=True, separators=(",", ":"), allow_nan=False) != json.dumps(expected_parent, sort_keys=True, separators=(",", ":"), allow_nan=False):
                raise ValueError("parent normalized admission differs from raw reparsed result")
            parsed[identifier] = result
            state["status"] = "complete"
        except MemoryError:
            raise
        except Exception as exc:
            state.update(status="unavailable", reason=type(exc).__name__ + ": " + str(exc))
        availability[identifier] = state
    return parsed, availability


def _inference_limits():
    return {
        "expected_return_confidence": {"status": "unavailable", "reason": "One asynchronously observed static snapshot is not a repeated-cycle profit sample."},
        "power": {"status": "unavailable", "reason": "No repeated execution sample or expected-profit test is registered."},
        "market_beta": {"status": "unavailable", "reason": "No return time series or measured partial-fill inventory exposure."},
        "execution_frequency": {"status": "unavailable", "reason": "A static snapshot cannot establish opportunity persistence or executable cycle frequency."},
        "annual_economic_relevance": {"status": "unavailable", "reason": "The 3% annual relevance threshold cannot be evaluated from one static snapshot."},
    }


def evaluate(capture, admission):
    """Two parsed parent envelopes -> fixed eight-case proxy output and cells."""
    try:
        parsed, availability = decode_sources(capture, admission)
    except MemoryError:
        raise
    except Exception as exc:
        reason = type(exc).__name__ + ": " + str(exc)
        parsed = {}
        availability = {identifier: {"id": identifier, "required_for_static_proxy": identifier in REQUIRED,
                        "status": "unavailable", "reason": reason} for identifier in SOURCE_IDS}
    missing = [identifier for identifier in REQUIRED if availability[identifier]["status"] != "complete"]
    quotes = parsed["triangle-book-ticker"]["quotes"] if not missing else {}
    output = triangle_bound.evaluate(quotes)
    if missing:
        reason = "Required source inputs unavailable: " + "; ".join(identifier + ": " + availability[identifier]["reason"] for identifier in missing)
        for result in output["cases"].values():
            result.update(status="unavailable", reason=reason, graduation=False)
        for cell in output["cells"]:
            cell.update(status="unavailable", reason=reason)
    for result in output["cases"].values():
        result["inference_limits"] = _inference_limits()
        result["graduation"] = False
        result["execution"] = {"status": "unavailable", "reason": "Forced continuous static model only; optional depth admission cannot establish fills, atomicity or simultaneous quotes."}
    ticker = availability["triangle-book-ticker"]
    output.update(source_availability=availability, required_source_ids=list(REQUIRED),
                  all_six_source_cells_available=all(row["status"] == "complete" for row in availability.values()),
                  ticker_capture_clocks={"request_utc": ticker.get("request_utc"), "retrieval_utc": ticker.get("retrieval_utc"),
                    "scope": "Literal source clocks retained; no cross-symbol simultaneity or depth/ticker alignment inferred."},
                  quote_source="Only the frozen batch book-ticker response drives the proxy; depth and time never substitute prices.",
                  inference_limits=_inference_limits(), graduation=False,
                  execution_scope="A forced full-notional model, not filled-order PnL or an upper bound on wallet wealth with abstention, partial sizing or residual cash.")
    return output, output["cells"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2], registration=REGISTRATION,
                           experiment=EXPERIMENT, source=args.source) as registered:
        raw_capture, raw_admission = registered.read_input("capture"), registered.read_input("admission")
        try:
            capture, admission = strict_json(raw_capture), strict_json(raw_admission)
        except (ValueError, UnicodeError) as exc:
            capture, admission = {"parent_decode_error": str(exc)}, {}
        proxy, cells = evaluate(capture, admission)
        if len(lifecycle_bytes(proxy)) > MAX_OUTPUT_BYTES:
            raise ValueError("proxy output exceeds registered 2 MiB serialized limit")
        registered.write_json("proxy.json", proxy)
        registered.finish(cells)


if __name__ == "__main__":
    main()
