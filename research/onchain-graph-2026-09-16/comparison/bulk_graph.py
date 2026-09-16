"""Serial bounded raw-graph day capture; no numerical rows or implicit resume.

The caller supplies registered inputs, new unique dates, baseline accounting,
and a shared Budget. This module supplies no launcher or research admission.
"""
from datetime import date as Date
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import urllib.parse


HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("bulk_graph_capture_helpers", HERE / "graph_capture.py")
graph_capture = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(graph_capture)
day, storage = graph_capture.day, graph_capture.storage
MIB, GIB = 1024**2, 1024**3
DAY_BYTES, DAY_REQUESTS = 272*MIB, 291
WORKING_RESERVE = 2*DAY_BYTES
MAX_STORED_RESPONSE = 33*MIB
REQUEST_METADATA_RESERVE = 8*MIB
DOCUMENT_RESERVE = MIB
FREE_FLOOR = 20*GIB
RAW_CEILING, METADATA_CEILING = 120*GIB, 2*GIB
TRANSACTION_TYPES = dict(hash="string", block_hash="string", block_number="int64",
                         block_timestamp="timestamp[ns]", transaction_index="int64",
                         from_address="string", to_address="string", value="double", receipt_status="int64")
BLOCK_TYPES = dict(number="int64", hash="string", parent_hash="string",
                   timestamp="timestamp[ns]", transaction_count="int64")


class BudgetStop(ValueError):
    pass


class Budget:
    """Shared append-only accounting. Baselines are caller-audited retained bytes.

    Raw usage is actual .zst file length; metadata usage is max(physical blocks,
    length rounded to filesystem fragment size). No scan of older days occurs.
    Use serially: this object is not a concurrent reservation service.
    """
    def __init__(self, *, existing_raw_bytes, existing_metadata_bytes,
                 raw_ceiling=RAW_CEILING, metadata_ceiling=METADATA_CEILING,
                 disk_usage=shutil.disk_usage):
        for name, value, maximum in (("raw baseline", existing_raw_bytes, RAW_CEILING),
                                      ("metadata baseline", existing_metadata_bytes, METADATA_CEILING),
                                      ("raw ceiling", raw_ceiling, RAW_CEILING),
                                      ("metadata ceiling", metadata_ceiling, METADATA_CEILING)):
            if type(value) is not int or not 0 <= value <= maximum:
                raise ValueError("invalid " + name)
        self.existing_raw_bytes, self.existing_metadata_bytes = existing_raw_bytes, existing_metadata_bytes
        self.new_raw_bytes = self.new_metadata_bytes = 0
        self.raw_ceiling, self.metadata_ceiling = raw_ceiling, metadata_ceiling
        self.disk_usage, self.stopped, self.dates = disk_usage, None, set()

    def snapshot(self):
        return dict(existing_raw_bytes=self.existing_raw_bytes, existing_metadata_bytes=self.existing_metadata_bytes,
                    new_raw_bytes=self.new_raw_bytes, new_metadata_bytes=self.new_metadata_bytes,
                    total_raw_bytes=self.existing_raw_bytes+self.new_raw_bytes,
                    total_metadata_bytes=self.existing_metadata_bytes+self.new_metadata_bytes,
                    raw_ceiling=self.raw_ceiling, metadata_ceiling=self.metadata_ceiling, stopped=self.stopped)

    def stop(self, reason):
        if self.stopped is None:
            self.stopped = reason
        raise BudgetStop(self.stopped)

    def _reserve(self, directory, raw, metadata, disk_reserve):
        if self.existing_raw_bytes+self.new_raw_bytes+raw > self.raw_ceiling:
            self.stop("aggregate retained raw cap; no automatic retry")
        if self.existing_metadata_bytes+self.new_metadata_bytes+metadata > self.metadata_ceiling:
            self.stop("aggregate metadata cap; no automatic retry")
        if self.disk_usage(directory).free < FREE_FLOOR+disk_reserve:
            self.stop("disk reserve reached; no automatic retry")

    def before_day(self, directory):
        if self.stopped:
            raise BudgetStop(self.stopped)
        self._reserve(directory, WORKING_RESERVE, REQUEST_METADATA_RESERVE+2*DOCUMENT_RESERVE,
                      WORKING_RESERVE+REQUEST_METADATA_RESERVE)

    def before_request(self, directory):
        if self.stopped:
            raise BudgetStop(self.stopped)
        self._reserve(directory, WORKING_RESERVE+MAX_STORED_RESPONSE,
                      REQUEST_METADATA_RESERVE+2*DOCUMENT_RESERVE,
                      WORKING_RESERVE+REQUEST_METADATA_RESERVE)

    def before_document(self, directory):
        # Terminal metadata may be written after a global stop, provided its
        # own physical floor and cap still fit. No request can bypass the latch.
        self._reserve(directory, 0, DOCUMENT_RESERVE, DOCUMENT_RESERVE)


def _allocated(path):
    stat = path.stat()
    fragment = max(4096, os.statvfs(path).f_frsize)
    return max(stat.st_blocks*512, ((stat.st_size+fragment-1)//fragment)*fragment)


def _charge(directory, budget, observed):
    """Stat at most one day's files; count every new byte even after failure."""
    added_raw = added_metadata = 0
    for path in directory.iterdir():
        if not path.is_file() or path.is_symlink():
            raise ValueError("unexpected non-regular day artifact")
        size = path.stat().st_size if path.suffix == ".zst" else _allocated(path)
        prior = observed.get(path.name, 0)
        if size < prior:
            raise ValueError("retained artifact shrank")
        if path.suffix == ".zst":
            added_raw += size-prior
        else:
            added_metadata += size-prior
        observed[path.name] = size
    budget.new_raw_bytes += added_raw
    budget.new_metadata_bytes += added_metadata
    if budget.existing_raw_bytes+budget.new_raw_bytes > budget.raw_ceiling:
        budget.stop("actual retained raw cap exceeded")
    if budget.existing_metadata_bytes+budget.new_metadata_bytes > budget.metadata_ceiling:
        budget.stop("actual metadata cap exceeded")


def _json(directory, name, value, budget, observed):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n").encode()
    if len(raw) > DOCUMENT_RESERVE-65536:
        raise ValueError("day metadata document exceeds fixed reserve")
    budget.before_document(directory)
    storage.atomic_json(directory/name, value)
    _charge(directory, budget, observed)


def _sha_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(MIB), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify(directory, capture):
    """Bind every immutable intent/receipt/body; read one bounded blob at a time."""
    intents = sorted(directory.glob("request-*-intent.json"))
    receipts = sorted(p for p in directory.glob("request-*.json") if not p.name.endswith("-intent.json"))
    if len(intents) != len(receipts) or len(receipts) != len(capture.records):
        raise ValueError("request intent/receipt denominator mismatch")
    bound = set()
    for number, receipt_path in enumerate(receipts, 1):
        stem = f"request-{number:04d}"
        if receipt_path.name != stem+".json":
            raise ValueError("request sequence changed")
        receipt = json.loads(receipt_path.read_bytes())
        intent = json.loads((directory/(stem+"-intent.json")).read_bytes())
        if intent.get("method") != "GET" or intent.get("status") != "intent":
            raise ValueError("request intent method/status changed")
        for key in ("url", "request_headers", "requested_at", "request_number"):
            if receipt[key] != intent[key]:
                raise ValueError("intent/receipt binding changed")
        if receipt != capture.records[number-1] or receipt["request_number"] != number:
            raise ValueError("in-memory/retained receipt changed")
        blob = receipt["blob"]
        if blob["path"] != stem+".body.zst" or blob["path"] in bound:
            raise ValueError("body path/identity changed")
        if blob["raw_bytes"] > 32*MIB+1 or blob["stored_bytes"] > MAX_STORED_RESPONSE:
            raise ValueError("response storage bound exceeded")
        raw = storage.read_blob(directory/blob["path"], blob)
        if len(raw) != receipt["bytes"] or storage.sha(raw) != receipt["sha256"]:
            raise ValueError("receipt/raw body hash mismatch")
        bound.add(blob["path"])
    if bound != {p.name for p in directory.glob("*.zst")}:
        raise ValueError("orphan raw body")
    if sum(r["bytes"] for r in capture.records) != capture.total:
        raise ValueError("received-byte denominator changed")
    return [dict(path=p.name, bytes=p.stat().st_size, sha256=_sha_file(p))
            for p in sorted(directory.iterdir()) if p.is_file()]


def _limits(plan):
    if plan["required_types"] != TRANSACTION_TYPES or plan["block_required_types"] != BLOCK_TYPES:
        raise ValueError("fixed nine-column or block schema changed")
    limits = dict(plan["limits"], max_requests=DAY_REQUESTS, max_total_bytes=DAY_BYTES)
    for name, maximum in (("max_logical_bytes", 8*GIB), ("max_footer_bytes", 4*MIB),
                           ("max_projection_bytes", 256*MIB), ("max_response_bytes", 32*MIB),
                           ("max_block_bytes", 16*MIB), ("timeout_seconds", 30)):
        if type(limits[name]) is not int or not 0 < limits[name] <= maximum:
            raise ValueError("invalid fixed bound: " + name)
    return limits


def capture_day(date, directory, inventory, plan, budget, *, reused_blocks=None):
    """Capture one new date into exactly directory; never retry an existing path.

    A complete result admits raw ranges/metadata only, not transaction rows,
    graph integrity, motifs, historical availability, or financial evaluation.
    reused_blocks references caller-hash-validated retained inputs; no copy or
    network request is made for that object and baseline usage must include it.
    """
    if not isinstance(date, str) or Date.fromisoformat(date).isoformat() != date:
        raise ValueError("canonical ISO source date required")
    directory = Path(directory)
    if directory.exists() or date in budget.dates:
        raise FileExistsError("existing day/date is immutable; no retry or resume")
    limits = _limits(plan)
    directory.mkdir(parents=False, exist_ok=False)
    budget.dates.add(date)
    observed = {}
    before_raw, before_metadata = budget.new_raw_bytes, budget.new_metadata_bytes
    capture = storage.BinaryCapture(dict(limits, base_url=plan["base_url"]), directory)
    result = dict(date=date, status="unavailable", reason=None, projected_rows=None,
                  selected_bytes=None, numerical_integrity_admitted=False, reused_blocks=None)
    projection = None
    try:
        budget.before_day(directory)
        _json(directory, "day-intent.json", dict(date=date, plan=plan, limits=limits,
                                               baseline=budget.snapshot(), reused_blocks=bool(reused_blocks)), budget, observed)

        def fetch(obj, first=None, last=None):
            budget.before_request(directory)
            if not isinstance(obj["key"], str) or len(obj["key"]) > 4096 or len(obj["etag"]) > 1024:
                raise ValueError("object identity exceeds metadata bound")
            url = plan["base_url"]+urllib.parse.quote(obj["key"], safe="/=")
            headers = {"If-Match": obj["etag"]}
            if first is not None:
                headers["Range"] = f"bytes={first}-{last}"
            try:
                body, receipt = capture.get(url, headers)
            finally:
                _charge(directory, budget, observed)
                if capture.denied:
                    budget.stop("source denied; no subsequent acquisition")
            return day.checked_response(body, receipt, obj, first, last)

        blocks = day.object_for(inventory, "blocks", date)
        if not 12 <= blocks["size"] <= limits["max_block_bytes"]:
            raise ValueError("block size exceeds fixed bound")
        if reused_blocks is None:
            block_body = fetch(blocks)
        else:
            block_body = day.checked_response(reused_blocks["body"], reused_blocks["receipt"], blocks)
            expected_url = plan["base_url"]+urllib.parse.quote(blocks["key"], safe="/=")
            if (reused_blocks["receipt"].get("url") != expected_url or
                    reused_blocks["receipt"].get("request_headers") != {"If-Match": blocks["etag"]}):
                raise ValueError("reused block request identity mismatch")
            if storage.sha(block_body) != reused_blocks["receipt"]["sha256"]:
                raise ValueError("reused block raw hash mismatch")
            provenance = reused_blocks["provenance"]
            if set(provenance) != {"receipt_path", "receipt_sha256", "blob_path", "stored_sha256"}:
                raise ValueError("reused block provenance fields differ")
            result["reused_blocks"] = provenance
            _json(directory, "reused-blocks.json", dict(provenance=provenance, receipt=reused_blocks["receipt"]), budget, observed)
        day.validate_blocks(block_body, plan["block_required_types"])
        del block_body
        obj = day.object_for(inventory, "transactions", date)
        if not 12 <= obj["size"] <= limits["max_logical_bytes"]:
            raise ValueError("transaction object exceeds fixed bound")
        tail = fetch(obj, obj["size"]-8, obj["size"]-1)
        size = struct.unpack("<I", tail[:4])[0]
        if tail[4:] != b"PAR1" or not 0 < size <= limits["max_footer_bytes"] or size+12 > obj["size"]:
            raise ValueError("invalid footer trailer")
        footer = fetch(obj, obj["size"]-size-8, obj["size"]-1)
        if footer[-8:] != tail:
            raise ValueError("footer changed")
        projection = day.numeric.projection(obj, footer, limits, plan["required_types"])
        result.update(projected_rows=projection["rows"], row_groups=projection["groups"],
                      selected_bytes=sum(r["bytes"] for r in projection["ranges"]))
        _json(directory, "projection.json", projection, budget, observed)
        for span in projection["ranges"]:
            fetch(obj, span["start"], span["end"])
        expected = len(projection["ranges"])+(2 if reused_blocks is not None else 3)
        if capture.count != expected or len(capture.records) != expected:
            raise ValueError("complete-day request denominator mismatch")
        result.update(status="complete", projected_rows=projection["rows"],
                      row_groups=projection["groups"], selected_bytes=sum(r["bytes"] for r in projection["ranges"]))
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
    try:
        _charge(directory, budget, observed)
        files = _verify(directory, capture)
        bindings_valid = True
    except Exception as exc:
        result.update(status="unavailable", reason=f"{result['reason'] or ''}; verification: {type(exc).__name__}: {exc}")
        files = [dict(path=p.name, bytes=p.stat().st_size, sha256=_sha_file(p))
                 for p in sorted(directory.iterdir()) if p.is_file()]
        bindings_valid = False
    result.update(requests=capture.count, received_bytes=capture.total, denied=capture.denied,
                  stored_raw_bytes=budget.new_raw_bytes-before_raw,
                  metadata_allocated_before_manifest=budget.new_metadata_bytes-before_metadata,
                  bindings_valid=bindings_valid, stopped=budget.stopped)
    manifest = dict(schema_version=1, result=result.copy(), files=files,
                    budget_before_manifest=budget.snapshot(), qualification="raw metadata only; no numerical rows decoded")
    manifest_sha = None
    try:
        _json(directory, "manifest.json", manifest, budget, observed)
        manifest_sha = _sha_file(directory/"manifest.json")
    except Exception as exc:
        result.update(status="unavailable", reason=f"{result['reason'] or ''}; manifest: {type(exc).__name__}: {exc}")
    result.update(manifest_sha256=manifest_sha, metadata_allocated_bytes=budget.new_metadata_bytes-before_metadata,
                  budget=budget.snapshot(), stopped=budget.stopped)
    return result
