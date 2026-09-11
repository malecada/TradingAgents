"""Synthetic archive bodies and fake transport only; no price or network reads."""
import base64
import csv
import hashlib
import importlib.util
import io
import json
import struct
from pathlib import Path
import zipfile

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11/dated_archive.py"
spec = importlib.util.spec_from_file_location("dated_archive", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_archive(request, *, count=None, gap=None, header=True, filename=None, content=None, change=None):
    start, end = module._month_bounds(request["month"])
    count = count if count is not None else (end - start) // module.HOUR_MS
    stream = io.StringIO()
    writer = csv.writer(stream)
    if header:
        writer.writerow(module.HEADER)
    for index in range(count):
        if index == gap:
            continue
        stamp = start + index * module.HOUR_MS
        row = [stamp, 100, 110, 90, 105, 1, stamp + module.HOUR_MS - 1, 100, 1, 0.5, 50, 0]
        if change is not None:
            change(row, index)
        writer.writerow(row)
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(filename or request["filename"][:-4] + ".csv", content if content is not None else stream.getvalue())
    body = raw.getvalue()
    checksum = (hashlib.sha256(body).hexdigest() + "  " + request["filename"] + "\n").encode()
    return body, checksum


def response(body, status=200):
    return {"body": body, "http_status": status, "headers": {}, "body_complete": True,
            "error": None if status == 200 else f"HTTP {status}"}


@pytest.mark.parametrize("header", [True, False])
def test_may_calendar_admission_with_optional_exact_header(header):
    request = module.frozen_request_spec()["requests"][0]
    raw, checksum = make_archive(request, header=header)
    result = module.validate_archive(raw, checksum, request)
    assert result["status"] == "complete"
    assert result["coverage"]["observed_hours"] == 744
    assert result["coverage"]["missing_calendar_hour_ids_ms"] == []
    assert result["header_present"] is header


def test_contiguous_june_tail_is_conditional_not_lifetime_proof():
    request = module.frozen_request_spec()["requests"][2]
    result = module.validate_archive(*make_archive(request, count=608), request)
    assert result["status"] == "complete"
    assert result["coverage"]["observed_hours"] == 608
    assert result["coverage"]["calendar_hours"] == 720
    assert len(result["coverage"]["trailing_missing_hour_ids_ms"]) == 112
    assert result["coverage"]["internal_gap_hour_ids_ms"] == []
    assert result["terminal_lifetime"] == "unverified"


@pytest.mark.parametrize("month_index,count,gap", [(0, 743, None), (2, 608, 200)])
def test_partial_may_or_internal_june_gap_is_unavailable(month_index, count, gap):
    request = module.frozen_request_spec()["requests"][month_index]
    result = module.validate_archive(*make_archive(request, count=count, gap=gap), request)
    assert result["status"] == "unavailable"
    assert result["coverage"]["missing_calendar_hour_ids_ms"]


@pytest.mark.parametrize("failure", ["checksum", "traversal", "oversize", "ratio", "bad_zip"])
def test_corrupt_or_unsafe_archive_fails(failure):
    request = module.frozen_request_spec()["requests"][0]
    if failure == "traversal":
        raw, checksum = make_archive(request, filename="../" + request["filename"][:-4] + ".csv")
    elif failure == "oversize":
        raw, checksum = make_archive(request, content=b"x" * (module.MAX_UNCOMPRESSED + 1))
    elif failure == "ratio":
        raw, checksum = make_archive(request, content=b"x" * 100000)
    else:
        raw, checksum = make_archive(request)
    if failure == "checksum":
        raw += b"corrupt"
    elif failure == "bad_zip":
        raw = b"not zip"
        checksum = (hashlib.sha256(raw).hexdigest() + "  " + request["filename"] + "\n").encode()
    with pytest.raises((ValueError, zipfile.BadZipFile)):
        module.validate_archive(raw, checksum, request)


def test_eight_receipts_publish_and_denial_stops_remaining_requests():
    calls, published = [], []
    def denied(url):
        calls.append(url)
        return response(b"denied", 403)
    raw, admission, cells = module.capture(module.frozen_request_spec(), denied,
                                          lambda name, receipt: published.append(name))
    assert len(calls) == 1
    assert len(cells) == len(published) == 8
    assert all(row["status"] == "unavailable" for row in cells)
    assert sum(row["attempted"] for row in raw["requests"]) == 1


def test_pairing_and_raw_bytes_survive_successful_fake_capture():
    frozen = module.frozen_request_spec()
    pairs = {}
    for request in frozen["requests"][::2]:
        body, checksum = make_archive(request, count=608 if request["month"] == "2026-06" else None)
        pairs[request["url"]] = body
        pairs[request["url"] + ".CHECKSUM"] = checksum
    raw, admission, cells = module.capture(frozen, lambda url: response(pairs[url]))
    assert all(row["status"] == "complete" for row in cells)
    assert [row["id"] for row in cells] == module.cell_ids()
    for receipt in raw["requests"]:
        assert base64.b64decode(receipt["body_base64"]) == pairs[receipt["url"]]


def test_frozen_url_change_rejected_before_transport():
    frozen = module.frozen_request_spec()
    frozen["requests"][0]["url"] = "https://other.invalid/"
    with pytest.raises(ValueError, match="frozen"):
        module.capture(frozen, lambda url: pytest.fail("transport called"))


def test_later_exception_does_not_erase_published_receipt(tmp_path):
    count = 0
    def transport(url):
        nonlocal count
        count += 1
        if count == 2:
            raise RuntimeError("later failure")
        return response(b"first raw response")
    def persist(name, receipt):
        with (tmp_path / name).open("x") as stream:
            json.dump(receipt, stream)
    with pytest.raises(RuntimeError):
        module.capture(module.frozen_request_spec(), transport, persist)
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert base64.b64decode(json.loads(files[0].read_text())["body_base64"]) == b"first raw response"


@pytest.mark.parametrize("column,value", [(5, -1), (7, -1), (8, 1.5), (9, -1), (10, -1),
                                         (11, "nan"), (2, 99), (0, 1777593600001)])
def test_numeric_schema_and_clock_fail_closed(column, value):
    request = module.frozen_request_spec()["requests"][0]
    def change(row, index):
        if index == 0:
            row[column] = value
    with pytest.raises(ValueError):
        module.validate_archive(*make_archive(request, change=change), request)


def test_zero_volume_and_zero_trade_hours_are_retained_and_counted():
    request = module.frozen_request_spec()["requests"][0]
    def change(row, index):
        if index == 20:
            for column in (5, 7, 8, 9, 10):
                row[column] = 0
    result = module.validate_archive(*make_archive(request, change=change), request)
    assert result["status"] == "complete"
    assert result["coverage"]["observed_hours"] == 744
    assert result["coverage"]["zero_volume_hour_count"] == 1
    assert result["coverage"]["zero_trade_hour_count"] == 1


@pytest.mark.parametrize("failure", ["deflate", "csv"])
def test_parser_errors_retain_all_receipts_and_eight_cells(failure):
    frozen = module.frozen_request_spec()
    pairs = {}
    for request in frozen["requests"][::2]:
        if failure == "csv":
            # Under the 2 MiB file cap, but above csv.reader field-size limit.
            # Avoid an earlier compression-ratio rejection, so CSV is exercised.
            raw = io.BytesIO()
            with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_STORED) as archive:
                archive.writestr(request["filename"][:-4] + ".csv", "x" * 140000)
            body = raw.getvalue()
        else:
            body, _ = make_archive(request)
            damaged = bytearray(body)
            # ZIP local header is 30 bytes then filename and extra field.
            name_length, extra_length = struct.unpack_from("<HH", damaged, 26)
            compressed_start = 30 + name_length + extra_length
            damaged[compressed_start] = (damaged[compressed_start] & ~7) | 7
            body = bytes(damaged)  # Deflate BTYPE=3 is reserved/invalid.
        checksum = (hashlib.sha256(body).hexdigest() + "  " + request["filename"] + "\n").encode()
        pairs[request["url"]] = body
        pairs[request["url"] + ".CHECKSUM"] = checksum
    published = []
    _, admission, cells = module.capture(frozen, lambda url: response(pairs[url]),
        lambda name, receipt: published.append(name))
    assert len(cells) == len(published) == 8
    zip_results = [row for row in admission["cells"] if row["id"].endswith("-zip")]
    assert all(row["status"] == "unavailable" for row in zip_results)
    assert all(("invalid block type" if failure == "deflate" else "field larger") in row["reason"] for row in zip_results)
