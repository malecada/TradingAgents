"""Bounded recovery of a frozen successful prefix; historical evidence is immutable."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import struct
import urllib.parse

_SPEC = importlib.util.spec_from_file_location("recovery_private_bulk", Path(__file__).with_name("bulk_graph.py"))
bulk = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(bulk)
storage = bulk.storage


def _read(directory, entry):
    path = entry["path"]
    if not isinstance(path, str) or Path(path).name != path or path in {".", ".."}:
        raise ValueError("unsafe cached member path")
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        member = os.open(path, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        with os.fdopen(member, "rb") as source:
            info = os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size != entry["bytes"]:
                raise ValueError("cached member type/size changed")
            raw = source.read(bulk.MAX_STORED_RESPONSE + 1)
    finally:
        os.close(fd)
    if len(raw) != entry["bytes"] or storage.sha(raw) != entry["sha256"]:
        raise ValueError("cached member hash changed")
    return raw


def _body(directory, files, receipt):
    blob = receipt["blob"]
    stored = _read(directory, files[blob["path"]])
    n = blob["raw_bytes"]
    if (type(n) is not int or not 0 <= n <= 32*bulk.MIB+1
            or blob.get("codec") != "zstd" or blob.get("level") != 3
            or blob["stored_bytes"] != len(stored) or storage.sha(stored) != blob["stored_sha256"]
            or storage.zstd.frame_content_size(stored) != n):
        raise ValueError("invalid cached blob metadata")
    raw = storage.zstd.ZstdDecompressor().decompress(stored, max_output_size=max(1, n), allow_extra_data=False)
    if len(raw) != n or storage.sha(raw) != blob["raw_sha256"]:
        raise ValueError("cached decompressed body changed")
    return raw


def _prefix(date, reference, inventory, plan, reused_blocks):
    if reference is None:
        return None, {}, []
    directory = Path(reference["directory"])
    if not directory.is_absolute() or any(p.is_symlink() for p in (directory, *directory.parents)):
        raise ValueError("cached source must be absolute and symlink-free")
    n = reference["receipt_count"]
    if type(n) is not int or not 0 < n <= bulk.DAY_REQUESTS:
        raise ValueError("invalid cached receipt count")
    entries = reference["files"]
    files = {entry["path"]: entry for entry in entries}
    expected = {f"request-{i:04d}{suffix}" for i in range(1, n+1)
                for suffix in ("-intent.json", ".json", ".body.zst")}
    if len(files) != len(entries) or set(files) != expected:
        raise ValueError("cached prefix member denominator changed")
    # Validate all frozen bytes before decoding metadata or allowing HTTP.
    for entry in entries:
        _read(directory, entry)
    records = []
    for i in range(1, n+1):
        stem = f"request-{i:04d}"
        receipt = json.loads(_read(directory, files[stem+".json"]))
        intent = json.loads(_read(directory, files[stem+"-intent.json"]))
        if "error" in receipt or receipt.get("status") not in {200, 206}:
            raise ValueError("failed historical receipt cannot be reused")
        if intent.get("method") != "GET" or intent.get("status") != "intent":
            raise ValueError("cached intent method/status changed")
        if receipt.get("request_number") != i or any(receipt.get(k) != intent.get(k) for k in
                ("url", "request_headers", "requested_at", "request_number")):
            raise ValueError("cached intent/receipt sequence changed")
        blob = receipt["blob"]
        if blob["path"] != stem+".body.zst" or blob["raw_bytes"] > 32*bulk.MIB+1:
            raise ValueError("cached body identity/bound changed")
        body = _body(directory, files, receipt)
        if len(body) != receipt["bytes"] or storage.sha(body) != receipt["sha256"]:
            raise ValueError("cached raw binding changed")
        records.append(receipt)
    if sum(r["bytes"] for r in records) >= bulk.DAY_BYTES:
        raise ValueError("cached prefix exceeds logical byte budget")
    blocks = bulk.day.object_for(inventory, "blocks", date)
    obj = bulk.day.object_for(inventory, "transactions", date)
    requests = [] if reused_blocks is not None else [(blocks, None, None)]
    requests.append((obj, obj["size"]-8, obj["size"]-1))
    tail = None
    for i, receipt in enumerate(records):
        if i >= len(requests):
            raise ValueError("cached prefix extends beyond deterministic requests")
        target, first, last = requests[i]
        headers = {"If-Match": target["etag"]}
        if first is not None:
            headers["Range"] = f"bytes={first}-{last}"
        url = plan["base_url"]+urllib.parse.quote(target["key"], safe="/=")
        if receipt["url"] != url or receipt["request_headers"] != headers:
            raise ValueError("cached request identity/order changed")
        body = _body(directory, files, receipt)
        bulk.day.checked_response(body, receipt, target, first, last)
        if target is blocks:
            bulk.day.validate_blocks(body, plan["block_required_types"])
        elif tail is None:
            size = struct.unpack("<I", body[:4])[0]
            if body[4:] != b"PAR1" or not 0 < size <= plan["limits"]["max_footer_bytes"] or size+12 > obj["size"]:
                raise ValueError("invalid cached trailer")
            tail = body
            requests.append((obj, obj["size"]-size-8, obj["size"]-1))
        elif i == (1 if reused_blocks is not None else 2):
            if body[-8:] != tail:
                raise ValueError("cached footer changed")
            projection = bulk.day.numeric.projection(obj, body, bulk._limits(plan), plan["required_types"])
            requests.extend((obj, span["start"], span["end"]) for span in projection["ranges"])
    return directory, files, records


def recovery_day(date, directory, inventory, plan, budget, *, reuse_prefix=None, reused_blocks=None):
    """Capture a unique recovery day; invalid frozen prefixes raise before HTTP.

    Legacy requests/received_bytes count logical responses, including replay.
    Actual network and reused denominators are separately returned to the caller.
    """
    bulk._limits(plan)
    source, files, records = _prefix(date, reuse_prefix, inventory, plan, reused_blocks)
    original_factory = storage.BinaryCapture
    counters = dict(actual_network_requests=0, actual_network_received_bytes=0,
                    reused_requests=0, reused_received_bytes=0)

    def factory(spec, own):
        capture = original_factory(spec, own)
        original_get = capture.get
        copied = False

        def get(url, headers=None):
            nonlocal copied
            if records and not copied:
                # Reserve duplicated physical evidence as well as the remaining
                # inherited working allowance before publishing any cached byte.
                copied_raw = sum(e["bytes"] for e in files.values() if e["path"].endswith(".zst"))
                fragment = max(4096, os.statvfs(own).f_frsize)
                copied_meta = sum(((e["bytes"]+fragment-1)//fragment)*fragment
                                  for e in files.values() if not e["path"].endswith(".zst"))
                budget._reserve(own, copied_raw+bulk.WORKING_RESERVE+bulk.MAX_STORED_RESPONSE,
                    copied_meta+bulk.REQUEST_METADATA_RESERVE+3*bulk.DOCUMENT_RESERVE,
                    copied_raw+copied_meta+bulk.WORKING_RESERVE+bulk.REQUEST_METADATA_RESERVE)
                for entry in files.values():
                    storage._publish(Path(own)/entry["path"], _read(source, entry))
                storage.atomic_json(Path(own)/"reuse-provenance.json", dict(
                    schema_version=1, source_directory=str(source), files=list(files.values()),
                    receipt_count=len(records), clocks="Copied receipt clocks refer to original acquisition; replay makes no HTTP request."))
                copied = True
            index = len(capture.records)
            if index < len(records):
                receipt = records[index]
                if receipt["url"] != url or receipt["request_headers"] != dict(headers or {}):
                    raise ValueError("cached replay request identity changed")
                body = _body(Path(own), files, receipt)
                capture.records.append(receipt)
                capture.count += 1
                capture.total += len(body)
                counters["reused_requests"] += 1
                counters["reused_received_bytes"] += len(body)
                return body, receipt
            before_count, before_total = capture.count, capture.total
            body, receipt = original_get(url, headers)
            counters["actual_network_requests"] += capture.count-before_count
            counters["actual_network_received_bytes"] += capture.total-before_total
            # BinaryCapture retains transport failures before returning. Latch without
            # raising so bulk's finally charges all retained files first.
            error = receipt.get("error", "")
            transport_error = error and (not error.startswith("ValueError:") or
                error == "ValueError: response body length mismatch")
            if transport_error and budget.stopped is None:
                budget.stopped = "transport failure; no subsequent acquisition: " + error
            return body, receipt
        capture.get = get
        return capture

    # This private module instance is used serially; no other bulk caller is patched.
    storage.BinaryCapture = factory
    try:
        result = bulk.capture_day(date, directory, inventory, plan, budget, reused_blocks=reused_blocks)
    finally:
        storage.BinaryCapture = original_factory
    result.update(counters, logical_requests=result["requests"], logical_received_bytes=result["received_bytes"])
    return result
