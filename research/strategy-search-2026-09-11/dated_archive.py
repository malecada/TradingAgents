"""Frozen delivery-futures archive admission; no spread/return computation."""
from __future__ import annotations

import argparse
import base64
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import re
import time
import zipfile
import zlib

from tradingagents.research import ResearchRun

_source = Path(__file__).with_name("carry_capture.py")
_spec = importlib.util.spec_from_file_location("dated_archive_capture_transport", _source)
capture_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(capture_module)

HOUR_MS = 3_600_000
MAX_BYTES, MAX_UNCOMPRESSED = 5 * 1024 * 1024, 2 * 1024 * 1024
HEADER = ["open_time", "open", "high", "low", "close", "volume", "close_time",
          "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]
REGISTRATION = "research/strategy-search-2026-09-11/gates-dated-archive.json"
EXPERIMENT = "dated-archive-20260911"


def frozen_request_spec():
    requests = []
    for asset in ("btc", "eth"):
        symbol = asset.upper() + "USDT_260626"
        for month in ("2026-05", "2026-06"):
            filename = f"{symbol}-1h-{month}.zip"
            url = f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/1h/{filename}"
            for kind in ("zip", "checksum"):
                requests.append({"id": f"{asset}-{month}-{kind}", "asset": asset,
                                 "symbol": symbol, "month": month, "kind": kind,
                                 "filename": filename,
                                 "url": url + (".CHECKSUM" if kind == "checksum" else "")})
    return {"schema_version": 1, "max_requests": 8, "timeout_seconds_per_request": 20,
            "max_response_bytes": MAX_BYTES, "max_uncompressed_bytes": MAX_UNCOMPRESSED,
            "max_compression_ratio": 100, "requests": requests}


def cell_ids():
    return [request["id"] for request in frozen_request_spec()["requests"]]


def _utc(stamp=None):
    return (datetime.now(timezone.utc) if stamp is None else
            datetime.fromtimestamp(stamp / 1000, timezone.utc)).isoformat()


def _month_bounds(month):
    if month not in ("2026-05", "2026-06"):
        raise ValueError("unregistered month")
    start = datetime(2026, int(month[-2:]), 1, tzinfo=timezone.utc)
    end = datetime(2026, int(month[-2:]) + 1, 1, tzinfo=timezone.utc)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def checksum_digest(raw, filename):
    match = re.fullmatch(r"([0-9a-fA-F]{64})  " + re.escape(filename) + r"\r?\n?", raw.decode("ascii"))
    if match is None:
        raise ValueError("checksum must be SHA256, two spaces and exact archive filename")
    return match.group(1).lower()


def _numeric(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("nonfinite CSV value")
    return result


def _clock(value):
    if not re.fullmatch(r"\d{13}", value):
        raise ValueError("timestamps must be integer milliseconds")
    return int(value)


def validate_archive(raw, checksum, request):
    expected_sha = checksum_digest(checksum, request["filename"])
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("paired archive checksum mismatch")
    expected_member = request["filename"][:-4] + ".csv"
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        if len(members) != 1 or members[0].filename != expected_member or members[0].is_dir():
            raise ValueError("ZIP must contain exactly the expected CSV filename without paths")
        info = members[0]
        if info.flag_bits & 1:
            raise ValueError("encrypted ZIP is not admitted")
        if info.file_size > MAX_UNCOMPRESSED or info.file_size / max(info.compress_size, 1) > 100:
            raise ValueError("ZIP exceeds uncompressed-size/compression-ratio bound")
        with archive.open(info) as stream:
            csv_bytes = stream.read(MAX_UNCOMPRESSED + 1)
        if len(csv_bytes) != info.file_size or len(csv_bytes) > MAX_UNCOMPRESSED:
            raise ValueError("ZIP member size mismatch or oversize")
    rows = list(csv.reader(io.StringIO(csv_bytes.decode("utf-8"))))
    header_present = bool(rows and rows[0] == HEADER)
    if header_present:
        rows = rows[1:]
    if not rows:
        raise ValueError("empty archive CSV")
    start, end = _month_bounds(request["month"])
    stamps, previous, zero_volume, zero_trades = [], None, [], []
    for row in rows:
        if len(row) != 12:
            raise ValueError("CSV must have exactly twelve fields")
        stamp, close_stamp = _clock(row[0]), _clock(row[6])
        if stamp % HOUR_MS or not start <= stamp < end or (previous is not None and stamp <= previous):
            raise ValueError("hourly open times must be unique ascending within registered month")
        if close_stamp != stamp + HOUR_MS - 1:
            raise ValueError("hourly close-time mismatch")
        opn, high, low, close = [_numeric(value) for value in row[1:5]]
        if min(opn, high, low, close) <= 0 or not low <= min(opn, close) <= max(opn, close) <= high:
            raise ValueError("invalid positive OHLC")
        for index in (5, 7, 8, 9, 10):
            if _numeric(row[index]) < 0:
                raise ValueError("negative volume/trade count")
        if not _numeric(row[8]).is_integer():
            raise ValueError("trade count must be integer")
        if _numeric(row[5]) == 0:
            zero_volume.append(stamp)
        if _numeric(row[8]) == 0:
            zero_trades.append(stamp)
        _numeric(row[11])
        stamps.append(stamp)
        previous = stamp
    observed = set(stamps)
    missing = [stamp for stamp in range(start, end, HOUR_MS) if stamp not in observed]
    internal = [stamp for stamp in missing if stamps[0] < stamp < stamps[-1]]
    leading = [stamp for stamp in missing if stamp < stamps[0]]
    trailing = [stamp for stamp in missing if stamp > stamps[-1]]
    coverage = {"observed_hours": len(stamps), "calendar_hours": (end - start) // HOUR_MS,
                "first_open_ms": stamps[0], "last_open_ms": stamps[-1],
                "first_open_utc": _utc(stamps[0]), "last_open_utc": _utc(stamps[-1]),
                "missing_calendar_hour_ids_ms": missing, "internal_gap_hour_ids_ms": internal,
                "leading_missing_hour_ids_ms": leading, "trailing_missing_hour_ids_ms": trailing,
                "zero_volume_hour_count": len(zero_volume), "zero_volume_hour_ids_ms": zero_volume,
                "zero_trade_hour_count": len(zero_trades), "zero_trade_hour_ids_ms": zero_trades}
    reason = None
    if internal or leading:
        reason = "internal/leading hourly gaps are not admitted"
    elif request["month"] == "2026-05" and missing:
        reason = "May requires all 744 calendar hours"
    return {"status": "unavailable" if reason else "complete", **({"reason": reason} if reason else {}),
            "coverage": coverage, "member": expected_member, "member_sha256": hashlib.sha256(csv_bytes).hexdigest(),
            "member_bytes": len(csv_bytes), "header_present": header_present,
            "archive_checksum_agrees": True, "terminal_lifetime": "unverified",
            "interpretation": ("Conditional continuous June observations; trailing calendar hours, if absent, remain unknown. Exact expiry end-hour is unverified."
                               if request["month"] == "2026-06" else "Complete May calendar coverage; contract lifetime and execution remain unverified."),
            "units": "Hourly public linear delivery-futures OHLC and volume; no spread, return or fill estimate."}


def capture(spec, transport=capture_module.public_get, persist_receipt=None):
    if json.dumps(spec, sort_keys=True) != json.dumps(frozen_request_spec(), sort_keys=True):
        raise ValueError("request_spec differs from frozen archive objects")
    receipts, bodies, denied = [], {}, False
    for request in spec["requests"]:
        before, started = time.monotonic(), _utc()
        attempted = not denied
        if attempted:
            response = transport(request["url"])
        else:
            response = {"body": b"", "http_status": None, "headers": {}, "body_complete": False,
                        "error": "not attempted after same-host HTTP denial"}
        body = response["body"]
        if not isinstance(body, bytes):
            raise ValueError("transport body must be bytes")
        if len(body) > MAX_BYTES:
            body = body[:MAX_BYTES]
            response = {**response, "body_complete": False, "error": "response exceeds 5 MiB; retained prefix"}
        if response["http_status"] in capture_module.DENIALS:
            denied = True
        receipt = {**request, "request_utc": started, "retrieval_utc": _utc(),
                   "elapsed_seconds": time.monotonic() - before, "attempted": attempted,
                   "http_status": response["http_status"], "error": response["error"],
                   "headers": {name: value for name, value in response["headers"].items()
                               if name.lower() in {"date", "content-type"}},
                   "body_complete": response["body_complete"], "body_bytes": len(body),
                   "body_sha256": hashlib.sha256(body).hexdigest(),
                   "body_base64": base64.b64encode(body).decode("ascii")}
        receipts.append(receipt)
        if persist_receipt is not None:
            persist_receipt(request["id"] + "-receipt.json", receipt)
        bodies[request["id"]] = body
    results = {}
    for receipt in receipts:
        key = receipt["id"]
        if receipt["error"] or receipt["http_status"] != 200 or not receipt["body_complete"]:
            results[key] = {"id": key, "status": "unavailable", "reason": receipt["error"] or "HTTP/body unavailable"}
        elif receipt["kind"] == "checksum":
            try:
                digest = checksum_digest(bodies[key], receipt["filename"])
                results[key] = {"id": key, "status": "complete", "declared_archive_sha256": digest,
                                "scope": "Provider checksum format only; paired ZIP integrity/admission reported in ZIP cell."}
            except (ValueError, UnicodeError) as exc:
                results[key] = {"id": key, "status": "unavailable", "reason": str(exc)}
    for receipt in receipts:
        key = receipt["id"]
        if receipt["kind"] != "zip" or key in results:
            continue
        checksum_key = key[:-3] + "checksum"
        if results[checksum_key]["status"] != "complete":
            results[key] = {"id": key, "status": "unavailable", "reason": "paired checksum unavailable"}
            continue
        try:
            results[key] = {"id": key, **validate_archive(bodies[key], bodies[checksum_key], receipt)}
        except (ValueError, UnicodeError, OSError, zipfile.BadZipFile, RuntimeError, zlib.error, csv.Error) as exc:
            results[key] = {"id": key, "status": "unavailable", "reason": type(exc).__name__ + ": " + str(exc)}
    admissions = [results[key] for key in cell_ids()]
    cells = [{"id": result["id"], "status": result["status"],
              **({"reason": result["reason"]} if result["status"] == "unavailable" else {})} for result in admissions]
    return ({"schema_version": 1, "request_spec": spec, "requests": receipts,
             "total_body_bytes": sum(row["body_bytes"] for row in receipts)},
            {"schema_version": 1, "cells": admissions, "terminal_lifetime": "unverified",
             "interpretation": "Archive admission only; no PnL or evidence of fresh confirmation/executable expiry settlement."}, cells)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2], registration=REGISTRATION,
                           experiment=EXPERIMENT, source=args.source) as run:
        raw, admission, cells = capture(json.loads(run.read_input("request_spec")), persist_receipt=run.write_json)
        run.write_json("archive-capture.json", raw)
        run.write_json("archive-admission.json", admission)
        run.finish(cells)


if __name__ == "__main__":
    main()
