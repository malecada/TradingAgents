"""Persistent exact full32 audit using the reviewed leading-byte/heapsort design.

Only caller-declared recomputable scratch is written. Every record is exactly
32 bytes; day attribution is sealed by append-segment receipts, not extra bytes
in each record. No input or scratch is deleted, and partial appends never resume.
The old utility's V32 in-place heapsort and comparison-block bounds are retained;
calling its whole audit would create a second disk copy and delete that copy.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil

SPEC = importlib.util.spec_from_file_location('fullpanel_frozen_hash_audit', Path(__file__).resolve().parents[1] / 'comparison/hash_audit.py')
reviewed = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewed)
np = reviewed.np
HASH_BYTES = reviewed.HASH_BYTES
MAX_CHUNK_BYTES = reviewed.MAX_CHUNK_BYTES
MAX_BUCKET_BYTES = reviewed.MAX_BUCKET_BYTES
MAX_TOTAL_BYTES = 40 * 1024**3
FREE_FLOOR_BYTES = reviewed.FREE_FLOOR_BYTES
ALLOCATION_MARGIN_BYTES = 1024**2
MAX_DAY_INDEX = 1095


def _integer(value, name, maximum=None):
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
        raise ValueError('invalid ' + name)
    return value


def _root(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('scratch root is a symlink')
    path.mkdir(parents=True, exist_ok=True)
    if any(p.is_symlink() for p in path.iterdir()):
        raise ValueError('scratch member is a symlink')
    return path


def _publish(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    with path.open('xb') as stream:
        if stream.write(raw) != len(raw):
            raise OSError('short receipt write')
        stream.flush()
        os.fsync(stream.fileno())


def _space(root, amount):
    if shutil.disk_usage(root).free < FREE_FLOOR_BYTES + amount + ALLOCATION_MARGIN_BYTES:
        raise OSError('hash audit would breach free-space floor plus allocation margin')


def _ledger(root):
    """Validate complete metadata and exact file lengths before further mutation."""
    receipts, intents = {}, set()
    for path in root.iterdir():
        match = re.fullmatch(r'day-(\d{4})(\.intent)?\.json', path.name)
        if match:
            day = _integer(int(match[1]), 'day index', MAX_DAY_INDEX)
            value = json.loads(path.read_bytes())
            if value.get('day_index') != day or value.get('schema_version') != 1:
                raise ValueError('day receipt identity mismatch')
            if match[2]:
                intents.add(day)
            else:
                if value.get('status') != 'complete':
                    raise ValueError('incomplete append receipt')
                receipts[day] = value
        elif not re.fullmatch(r'[0-9a-f]{2}\.bin', path.name) and path.name != 'append.lock':
            raise ValueError('unrecognized scratch member: ' + path.name)
    if set(receipts) != intents:
        raise ValueError('incomplete append intent; no partial recovery')
    segments = [[] for _ in range(256)]
    for day, receipt in receipts.items():
        rows = _integer(receipt['rows'], 'day rows')
        if receipt['bytes'] != rows * HASH_BYTES or len(receipt['buckets']) != 256:
            raise ValueError('day byte/row denominator mismatch')
        if (not isinstance(receipt['stream_sha256'], str)
                or not re.fullmatch('[0-9a-f]{64}', receipt['stream_sha256'])):
            raise ValueError('invalid input stream digest')
        total = 0
        end_total = 0
        for bucket, item in enumerate(receipt['buckets']):
            if item['bucket'] != f'{bucket:02x}':
                raise ValueError('bucket ordering mismatch')
            count = _integer(item['rows'], 'segment rows')
            offset = _integer(item['offset'], 'segment offset')
            if offset % HASH_BYTES or item['bytes'] != count * HASH_BYTES:
                raise ValueError('segment byte/row denominator mismatch')
            if not isinstance(item['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', item['sha256']):
                raise ValueError('invalid segment digest')
            if count:
                segments[bucket].append((offset, item['bytes'], day, item['sha256']))
            elif item['sha256'] != hashlib.sha256(b'').hexdigest():
                raise ValueError('empty segment digest mismatch')
            total += count
            end_total += offset + item['bytes']
        if total != rows:
            raise ValueError('day segment count mismatch')
        if receipt['total_bucket_bytes'] != end_total:
            raise ValueError('day aggregate byte counter mismatch')
    sizes = []
    for bucket, spans in enumerate(segments):
        position = 0
        for offset, size, _, _ in sorted(spans):
            if offset != position:
                raise ValueError('bucket segments overlap or have a gap')
            position += size
        path = root / f'{bucket:02x}.bin'
        if (path.stat().st_size if path.exists() else 0) != position:
            raise ValueError('bucket length differs from complete append receipts')
        if position > MAX_BUCKET_BYTES:
            raise ValueError('bucket exceeds reviewed memory ceiling')
        sizes.append(position)
    return receipts, segments, sizes


def append_day(bucket_root, hashes, day_index, *, max_total_bytes=MAX_TOTAL_BYTES):
    """Append iterable immutable byte chunks (32 B..32 MiB, integral records).

    Receipt rows count occurrences, stream_sha256 binds their original order.
    A retained append.lock or intent without receipt is a hard stop. Source
    iterator/I/O failures preserve partial buckets and the intent for inspection.
    """
    _integer(day_index, 'day index', MAX_DAY_INDEX)
    _integer(max_total_bytes, 'total byte cap')
    root = _root(bucket_root)
    lock = root / 'append.lock'
    lock.mkdir()  # exclusive across all days, retained if any append has begun
    started = False
    try:
        receipts, _, sizes = _ledger(root)
        if day_index in receipts:
            raise ValueError('day already appended')
        total = sum(sizes)
        if total > max_total_bytes:
            raise ValueError('existing buckets exceed byte cap')
        _space(root, 0)
        intent = root / f'day-{day_index:04d}.intent.json'
        started = True
        _publish(intent, dict(schema_version=1, day_index=day_index, status='intent', max_total_bytes=max_total_bytes))
        offsets = list(sizes)
        counts = [0] * 256
        digests = [hashlib.sha256() for _ in range(256)]
        stream_digest = hashlib.sha256()
        rows = 0
        for chunk in hashes:
            if not isinstance(chunk, bytes):
                raise TypeError('hash chunks must be immutable bytes')
            if len(chunk) % HASH_BYTES or len(chunk) > MAX_CHUNK_BYTES:
                raise ValueError('hash chunk width or memory bound invalid')
            if not chunk:
                continue
            if total + len(chunk) > max_total_bytes:
                raise ValueError('aggregate byte cap exceeded')
            array = np.frombuffer(chunk, dtype='V32')
            leading = np.frombuffer(chunk, dtype=np.uint8)[::HASH_BYTES]
            histogram = np.bincount(leading, minlength=256)
            for bucket, count in enumerate(histogram):
                if sizes[bucket] + int(count) * HASH_BYTES > MAX_BUCKET_BYTES:
                    raise ValueError('bucket exceeds reviewed memory ceiling')
            ordered = array[np.argsort(leading, kind='heapsort')]
            offset = 0
            for bucket, count in enumerate(histogram):
                count = int(count)
                if not count:
                    continue
                payload = memoryview(ordered[offset:offset+count]).cast('B')
                _space(root, len(payload))
                with (root / f'{bucket:02x}.bin').open('ab') as output:
                    if output.write(payload) != len(payload):
                        raise OSError('short bucket write')
                    output.flush()
                    os.fsync(output.fileno())
                digests[bucket].update(payload)
                counts[bucket] += count
                sizes[bucket] += len(payload)
                offset += count
            stream_digest.update(chunk)
            rows += len(chunk) // HASH_BYTES
            total += len(chunk)
            del chunk, array, leading, histogram, ordered, payload
        receipt = dict(schema_version=1, status='complete', day_index=day_index, rows=rows,
            bytes=rows * HASH_BYTES, stream_sha256=stream_digest.hexdigest(), total_bucket_bytes=total,
            record_format='full32; leading-byte bucket; day attribution in segment receipts',
            buckets=[dict(bucket=f'{b:02x}', offset=offsets[b], rows=counts[b], bytes=counts[b]*HASH_BYTES,
                          sha256=digests[b].hexdigest()) for b in range(256)])
        _space(root, 0)
        _publish(root / f'day-{day_index:04d}.json', receipt)
        lock.rmdir()
        return receipt
    except BaseException:
        if not started:
            lock.rmdir()
        raise


def audit(bucket_root, expected_day_rows, *, sample_limit=20):
    """Exact full-population audit; any duplicate blocks the entire panel.

    One <=256 MiB V32 array is sorted in place using reviewed NumPy heapsort.
    Segment verification uses <=32 MiB, adjacent comparisons <=32 KiB booleans.
    No second disk copy or automatic cleanup occurs. Aggregate RSS guard remains
    the caller's responsibility, including its own hash iterator and runtime.
    """
    _integer(sample_limit, 'sample limit', 100)
    expected = dict(expected_day_rows)
    for day, rows in expected.items():
        _integer(day, 'expected day', MAX_DAY_INDEX)
        _integer(rows, 'expected rows')
    root = _root(bucket_root)
    if (root / 'append.lock').exists():
        raise ValueError('append active or failed; no partial recovery')
    receipts, segments, sizes = _ledger(root)
    if set(receipts) != set(expected) or any(receipts[d]['rows'] != n for d, n in expected.items()):
        raise ValueError('expected day population mismatch')
    summaries, samples = [], []
    duplicate_excess = 0
    for bucket, size in enumerate(sizes):
        digest = hashlib.sha256()
        if size:
            path = root / f'{bucket:02x}.bin'
            with path.open('rb') as stream:
                for _, length, _, expected_digest in sorted(segments[bucket]):
                    segment_digest = hashlib.sha256()
                    remaining = length
                    while remaining:
                        raw = stream.read(min(remaining, MAX_CHUNK_BYTES))
                        if not raw or len(raw) % HASH_BYTES:
                            raise ValueError('truncated bucket records')
                        if any(byte != bucket for byte in memoryview(raw)[::HASH_BYTES]):
                            raise ValueError('hash routed to wrong bucket')
                        segment_digest.update(raw)
                        digest.update(raw)
                        remaining -= len(raw)
                    if segment_digest.hexdigest() != expected_digest:
                        raise ValueError('bucket segment digest mismatch')
                if stream.read(1):
                    raise ValueError('bucket grew during audit')
            del raw
            identities = np.fromfile(path, dtype='V32', count=size//HASH_BYTES)
            if identities.nbytes != size or hashlib.sha256(memoryview(identities).cast('B')).hexdigest() != digest.hexdigest():
                raise ValueError('bucket changed before sorting')
            identities.sort(kind='heapsort')
            duplicates = 0
            for start in range(1, len(identities), reviewed.COMPARE_HASHES):
                stop = min(len(identities), start + reviewed.COMPARE_HASHES)
                equal = identities[start:stop] == identities[start-1:stop-1]
                duplicates += int(np.count_nonzero(equal))
                if len(samples) < sample_limit:
                    for index in np.flatnonzero(equal):
                        value = bytes(identities[start + int(index)]).hex()
                        if not samples or samples[-1] != value:
                            samples.append(value)
                        if len(samples) >= sample_limit:
                            break
            del identities
        else:
            duplicates = 0
        duplicate_excess += duplicates
        rows = size // HASH_BYTES
        summaries.append(dict(bucket=f'{bucket:02x}', bytes=size, rows=rows, unique=rows-duplicates,
                              duplicate_excess=duplicates, sha256=digest.hexdigest()))
    rows = sum(expected.values())
    return dict(schema_version=1, status='complete', admitted=duplicate_excess == 0,
                algorithm='full32-leading-byte-buckets-inplace-heapsort', rows=rows,
                unique=rows-duplicate_excess, duplicate_excess=duplicate_excess,
                input_bytes=sum(sizes), days=len(expected), expected_day_rows={str(d): expected[d] for d in sorted(expected)},
                duplicate_samples=samples, duplicate_policy='any duplicate blocks entire panel; no date-local exclusion',
                buckets=summaries, scratch_preserved=True,
                limits=dict(max_bucket_bytes=MAX_BUCKET_BYTES, max_chunk_bytes=MAX_CHUNK_BYTES,
                            free_floor_bytes=FREE_FLOOR_BYTES, allocation_margin_bytes=ALLOCATION_MARGIN_BYTES))
