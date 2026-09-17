"""Bounded transport continuation; immutable physical and logical evidence."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import time

_SPEC = importlib.util.spec_from_file_location('resume_private_recovery', Path(__file__).with_name('recovery_graph.py'))
recovery = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(recovery)
bulk, storage = recovery.bulk, recovery.storage
ATTEMPTS = 4
DELAYS = (5, 15, 45)
PHYSICAL_REQUESTS = ATTEMPTS * bulk.DAY_REQUESTS
PHYSICAL_BYTES = ATTEMPTS * bulk.DAY_BYTES


def retryable(record):
    """HTTP failures and deterministic validation errors never trigger retries."""
    if record.get('status') not in (None, 200, 206):
        return False
    error = record.get('error', '')
    message = error.lower()
    if any(token in message for token in ('certificate', 'hostname', 'wrong_version_number',
            'unsupported protocol', 'protocol_version', 'handshake_failure', 'no shared cipher')):
        return False
    kind = error.split(':', 1)[0]
    if error == 'ValueError: response body length mismatch':
        return True
    if kind in {'ConnectionResetError', 'ConnectionAbortedError', 'ConnectionRefusedError',
                'BrokenPipeError', 'TimeoutError', 'SSLEOFError', 'IncompleteRead',
                'RemoteDisconnected', 'gaierror'}:
        return True
    if kind == 'SSLError':
        return 'unexpected_eof' in message or 'eof occurred' in message
    if kind == 'URLError':
        return any(token in message for token in ('connection reset', 'connection aborted',
            'connection refused', 'broken pipe', 'timed out', 'timeout',
            'temporary failure in name resolution', 'name or service not known',
            'nodename nor servname provided', 'getaddrinfo failed', 'unexpected_eof', 'eof occurred'))
    return False


def resume_day(date, directory, inventory, plan, budget, *, reuse_prefix=None, reused_blocks=None):
    """New directory only. Four attempts per missing logical request, then stop.

    ``date-attempts`` is a sibling of the selected logical ``date`` directory.
    Actual receipt bytes are never edited; selected receipts carry logical numbers.
    Selected bodies are hardlinked; unique body inodes are charged exactly once.
    """
    bulk._limits(plan)
    source, files, cached = recovery._prefix(date, reuse_prefix, inventory, plan, reused_blocks)
    directory = Path(directory)
    attempt_dir = directory.with_name(directory.name+'-attempts')
    if directory.exists() or attempt_dir.exists() or date in budget.dates:
        raise FileExistsError('existing continuation evidence is immutable')
    original_factory = storage.BinaryCapture
    observed = {}
    original_charge = bulk._charge
    charged_inodes = set()

    def charge(own, shared, seen):
        # Only this new day's two flat directories participate. No old store is
        # scanned or discounted. Hardlinks arise solely from selected attempts.
        duplicate = 0
        fresh = set()
        for path in own.glob('*.zst'):
            info = path.stat()
            key = (info.st_dev, info.st_ino)
            if path.name not in seen:
                if key in charged_inodes:
                    duplicate += info.st_size
                else:
                    fresh.add(key)
        # Suppress only the duplicate addition, never a prior family's baseline.
        shared.new_raw_bytes -= duplicate
        try:
            original_charge(own, shared, seen)
        finally:
            charged_inodes.update(fresh)

    physical = None
    reused_count = reused_bytes = 0
    before_raw, before_meta = budget.new_raw_bytes, budget.new_metadata_bytes

    def factory(spec, own):
        nonlocal physical
        logical = original_factory(spec, own)
        attempt_dir.mkdir(exist_ok=False)
        physical = original_factory(dict(spec, max_requests=PHYSICAL_REQUESTS,
                                         max_total_bytes=PHYSICAL_BYTES), attempt_dir)
        copied = False

        def get(url, headers=None):
            nonlocal copied, reused_count, reused_bytes
            number = logical.count+1
            if cached and not copied:
                raw = sum(e['bytes'] for e in files.values() if e['path'].endswith('.zst'))
                fragment = max(4096, os.statvfs(own).f_frsize)
                meta = sum(((e['bytes']+fragment-1)//fragment)*fragment
                           for e in files.values() if not e['path'].endswith('.zst'))
                budget._reserve(own, raw+bulk.WORKING_RESERVE+bulk.MAX_STORED_RESPONSE,
                    meta+bulk.REQUEST_METADATA_RESERVE+3*bulk.DOCUMENT_RESERVE,
                    raw+meta+bulk.WORKING_RESERVE+bulk.REQUEST_METADATA_RESERVE)
                for entry in files.values():
                    storage._publish(Path(own)/entry['path'], recovery._read(source, entry))
                storage.atomic_json(Path(own)/'reuse-provenance.json', dict(
                    schema_version=1, source_directory=str(source), files=list(files.values()),
                    receipt_count=len(cached), clocks='Original clocks; no HTTP on replay.'))
                copied = True
            if number <= len(cached):
                record = cached[number-1]
                if record['url'] != url or record['request_headers'] != dict(headers or {}):
                    raise ValueError('cached replay request identity changed')
                body = recovery._body(Path(own), files, record)
                reused_count += 1
                reused_bytes += len(body)
            else:
                if logical.count >= bulk.DAY_REQUESTS or logical.total >= bulk.DAY_BYTES-1:
                    budget.stop('logical request/response bound reached')
                for attempt in range(1, ATTEMPTS+1):
                    budget.before_request(attempt_dir)
                    if physical.count >= PHYSICAL_REQUESTS or physical.total >= PHYSICAL_BYTES-1:
                        budget.stop('physical request/response bound reached')
                    # Preserve retry intent before sleeping or starting a transport.
                    mapping = dict(logical_request=number, attempt=attempt,
                                   delay_seconds=0 if attempt == 1 else DELAYS[attempt-2],
                                   physical_request=physical.count+1)
                    storage.atomic_json(attempt_dir/f'mapping-{physical.count+1:04d}.json', mapping)
                    bulk._charge(attempt_dir, budget, observed)
                    if attempt > 1:
                        time.sleep(DELAYS[attempt-2])
                        budget.before_request(attempt_dir)
                    # Keep the final selected response inside the original logical cap.
                    physical.spec['max_response_bytes'] = min(spec['max_response_bytes'],
                        bulk.DAY_BYTES-logical.total-1)
                    try:
                        body, actual = physical.get(url, headers)
                    finally:
                        bulk._charge(attempt_dir, budget, observed)
                    logical.denied = physical.denied
                    if not retryable(actual):
                        break
                    if attempt == ATTEMPTS:
                        if budget.stopped is None:
                            budget.stopped = 'transport retries exhausted; no subsequent acquisition: '+actual['error']
                        break
                stem = f'request-{number:04d}'
                original_stem = f"request-{actual['request_number']:04d}"
                record = copy.deepcopy(actual)
                record['request_number'] = number
                record['blob']['path'] = stem+'.body.zst'
                intent = json.loads((attempt_dir/(original_stem+'-intent.json')).read_bytes())
                intent['request_number'] = number
                # Selected body is one immutable inode, referenced by both views.
                budget._reserve(own, bulk.MAX_STORED_RESPONSE, bulk.REQUEST_METADATA_RESERVE,
                                bulk.MAX_STORED_RESPONSE+bulk.REQUEST_METADATA_RESERVE)
                os.link(attempt_dir/(original_stem+'.body.zst'), Path(own)/(stem+'.body.zst'), follow_symlinks=False)
                storage.atomic_json(Path(own)/(stem+'-intent.json'), intent)
                storage.atomic_json(Path(own)/(stem+'.json'), record)
            logical.records.append(record)
            logical.count += 1
            logical.total += record['bytes']
            return body, record
        logical.get = get
        return logical

    storage.BinaryCapture = factory
    bulk._charge = charge
    try:
        result = bulk.capture_day(date, directory, inventory, plan, budget, reused_blocks=reused_blocks)
    finally:
        storage.BinaryCapture = original_factory
        bulk._charge = original_charge
    # Even a failed terminal publication returns the observed physical counters.
    attempts_manifest_sha = None
    try:
        attempt_files = bulk._verify(attempt_dir, physical)
        bulk._json(attempt_dir, 'manifest.json', dict(schema_version=1, date=date,
            files=attempt_files, requests=physical.count, received_bytes=physical.total,
            denied=physical.denied, max_attempts=ATTEMPTS, delays_seconds=list(DELAYS)), budget, observed)
        attempts_manifest_sha = bulk._sha_file(attempt_dir/'manifest.json')
    except Exception as exc:
        result.update(status='unavailable', reason=(result.get('reason') or '')+
                      f'; attempt manifest: {type(exc).__name__}: {exc}')
    result.update(actual_network_requests=physical.count,
        actual_network_received_bytes=physical.total, reused_requests=reused_count,
        reused_received_bytes=reused_bytes, logical_requests=result['requests'],
        logical_received_bytes=result['received_bytes'],
        attempts_manifest_sha256=attempts_manifest_sha,
        retained_raw_bytes=budget.new_raw_bytes-before_raw,
        retained_metadata_allocated_bytes=budget.new_metadata_bytes-before_meta,
        budget=budget.snapshot(), stopped=budget.stopped)
    return result
