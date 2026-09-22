"""Read-only exact union of immutable fullpanel hash append namespaces.

Metadata inventory never reads bucket payloads. Final audit allocates a single
combined bucket, fills it directly, verifies its segments, then heapsorts it.
Ordered day-stream digests are bound to external day evidence: bucketization
does not retain the original stream order and cannot reconstruct that digest.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    'resume_frozen_hash', Path(__file__).resolve().parents[1] / 'fullpanel/hash_audit.py')
frozen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(frozen)
np = frozen.np
MAX_BUCKET_BYTES = frozen.MAX_BUCKET_BYTES
MAX_TOTAL_BYTES = frozen.MAX_TOTAL_BYTES


def _snapshot(bucket_roots):
    roots = tuple(Path(p) for p in bucket_roots)
    if not roots or len({p.resolve() for p in roots}) != len(roots):
        raise ValueError('hash roots must be nonempty and distinct')
    ledgers, fingerprints, days = [], [], set()
    combined = [0] * 256
    for root in roots:
        if not root.is_dir() or any(p.is_symlink() for p in (root, *root.parents)):
            raise ValueError('hash root missing or symlinked')
        members = list(root.iterdir())
        if any(p.is_symlink() or not p.is_file() for p in members):
            raise ValueError('symlink or append active or failed')
        if (root / 'append.lock').exists():
            raise ValueError('append active or failed; no partial recovery')
        receipts, segments, sizes = frozen._ledger(root)
        if days.intersection(receipts):
            raise ValueError('day occurs in multiple hash namespaces')
        days.update(receipts)
        # Bind even empty segments to the chronological append position.
        offsets = [0] * 256
        for day in sorted(receipts):
            for bucket, item in enumerate(receipts[day]['buckets']):
                if item['offset'] != offsets[bucket]:
                    raise ValueError('day segment chronological offset mismatch')
                offsets[bucket] += item['bytes']
        combined = [a+b for a, b in zip(combined, sizes)]
        ledgers.append((root, receipts, segments, sizes))
        fingerprints.append({p.name: (p.stat().st_dev, p.stat().st_ino,
            p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns,
            hashlib.sha256(p.read_bytes()).hexdigest() if p.suffix == '.json' else None)
            for p in members})
    if sum(combined) > MAX_TOTAL_BYTES:
        raise ValueError('combined hash byte cap exceeded')
    # This check precedes every payload read and NumPy allocation.
    if any(size > MAX_BUCKET_BYTES for size in combined):
        raise ValueError('combined bucket exceeds reviewed memory ceiling')
    return ledgers, combined, fingerprints


def inventory(bucket_roots):
    """Metadata-only complete-segment and combined-cap preflight; no writes."""
    ledgers, sizes, _ = _snapshot(bucket_roots)
    return dict(input_bytes=sum(sizes), bucket_bytes=sizes,
                roots=[dict(path=str(root), days=sorted(receipts),
                            input_bytes=sum(local_sizes))
                       for root, receipts, _, local_sizes in ledgers])


def audit(bucket_roots, expected_day_rows, *, expected_day_stream_sha256,
          sample_limit=20):
    """Audit every supplied day, retaining all duplicate occurrences in counts.

No scratch mutation, copy, cleanup or partial-append recovery is performed.
The caller owns execution admission and the aggregate process RSS guard.
"""
    frozen._integer(sample_limit, 'sample limit', 100)
    expected = dict(expected_day_rows)
    streams = dict(expected_day_stream_sha256)
    for day, rows in expected.items():
        frozen._integer(day, 'expected day', frozen.MAX_DAY_INDEX)
        frozen._integer(rows, 'expected rows')
    ledgers, sizes, before = _snapshot(bucket_roots)
    receipts = {day: receipt for _, local, _, _ in ledgers for day, receipt in local.items()}
    if set(receipts) != set(expected) or set(streams) != set(expected):
        raise ValueError('expected day population mismatch')
    if any(receipts[d]['rows'] != n for d, n in expected.items()):
        raise ValueError('expected day row mismatch')
    if any(receipts[d]['stream_sha256'] != streams[d] for d in expected):
        raise ValueError('expected day stream digest mismatch')
    for root, _, _, _ in ledgers:
        frozen._space(root, 0)
    summaries, samples = [], []
    excess = 0
    for bucket, size in enumerate(sizes):
        duplicates = 0
        digest = hashlib.sha256()
        if size:
            identities = np.empty(size // frozen.HASH_BYTES, dtype='V32')
            payload = memoryview(identities).cast('B')
            position = 0
            for root, _, segments, local_sizes in ledgers:
                if not local_sizes[bucket]:
                    continue
                with (root / f'{bucket:02x}.bin').open('rb', buffering=0) as stream:
                    for _, length, _, expected_digest in sorted(segments[bucket]):
                        segment_digest = hashlib.sha256()
                        end = position + length
                        while position < end:
                            block = payload[position:min(end, position + frozen.MAX_CHUNK_BYTES)]
                            read = stream.readinto(block)
                            if read != len(block):
                                raise ValueError('truncated bucket records')
                            if any(byte != bucket for byte in block[::frozen.HASH_BYTES]):
                                raise ValueError('hash routed to wrong bucket')
                            segment_digest.update(block)
                            digest.update(block)
                            position += read
                            del block
                        if segment_digest.hexdigest() != expected_digest:
                            raise ValueError('bucket segment digest mismatch')
                    if stream.read(1):
                        raise ValueError('bucket grew during audit')
            if position != size:
                raise ValueError('combined bucket denominator mismatch')
            del payload
            identities.sort(kind='heapsort')
            for start in range(1, len(identities), frozen.reviewed.COMPARE_HASHES):
                stop = min(len(identities), start + frozen.reviewed.COMPARE_HASHES)
                equal = identities[start:stop] == identities[start-1:stop-1]
                duplicates += int(np.count_nonzero(equal))
                if len(samples) < sample_limit:
                    for index in np.flatnonzero(equal):
                        value = bytes(identities[start + int(index)]).hex()
                        if not samples or samples[-1] != value:
                            samples.append(value)
                        if len(samples) >= sample_limit:
                            break
                del equal
            del identities
        rows = size // frozen.HASH_BYTES
        summaries.append(dict(bucket=f'{bucket:02x}', bytes=size, rows=rows,
            unique=rows-duplicates, duplicate_excess=duplicates, sha256=digest.hexdigest()))
        excess += duplicates
    if _snapshot([item[0] for item in ledgers])[2] != before:
        raise ValueError('hash namespace changed during audit')
    rows = sum(expected.values())
    return dict(schema_version=1, status='complete', admitted=excess == 0,
        algorithm='full32-leading-byte-buckets-inplace-heapsort', rows=rows,
        unique=rows-excess, duplicate_excess=excess, input_bytes=sum(sizes),
        days=len(expected), expected_day_rows={str(d): expected[d] for d in sorted(expected)},
        expected_day_stream_sha256={str(d): streams[d] for d in sorted(streams)},
        duplicate_samples=samples, buckets=summaries, scratch_preserved=True,
        duplicate_policy='any duplicate blocks entire panel; no date-local exclusion',
        roots=[str(item[0]) for item in ledgers],
        limits=dict(max_bucket_bytes=MAX_BUCKET_BYTES, max_total_bytes=MAX_TOTAL_BYTES,
                    max_chunk_bytes=frozen.MAX_CHUNK_BYTES,
                    free_floor_bytes=frozen.FREE_FLOOR_BYTES,
                    allocation_margin_bytes=frozen.ALLOCATION_MARGIN_BYTES))
