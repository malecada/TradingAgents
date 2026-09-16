"""Exact external-storage audit of complete 32-byte transaction identities.

Only newly created scratch is deleted. No source reads, acquisition or retained
store writes occur here. The caller must preserve success/failure receipts.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import tempfile

import numpy as np


HASH_BYTES = 32
MAX_CHUNK_BYTES = 32 * 1024**2
MAX_BUCKET_BYTES = 256 * 1024**2
FREE_FLOOR_BYTES = 20 * 1024**3
COMPARE_HASHES = 1024**2 // HASH_BYTES


def _cap(name, value, *, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} exceeds fixed memory ceiling {maximum}")


def _space(path, write_bytes):
    if shutil.disk_usage(path).free < FREE_FLOOR_BYTES + write_bytes:
        raise OSError("hash audit would breach 20 GiB free-space floor")


def audit_hashes(chunks, *, scratch_parent, max_total_hashes, max_total_bytes,
                 max_bucket_bytes=MAX_BUCKET_BYTES):
    """Audit byte chunks containing integral numbers of complete identities.

    Every occurrence participates, including overlaps/day boundaries supplied by
    the caller. Excess occurrences are total minus exact unique identities, not
    the number of identities having duplicates. Partitioning and comparison use
    all 32 bytes; the leading byte only chooses a bucket.

    Partition array payload is bounded by 2*32 MiB + 8*(32 MiB/32), plus <=8 MiB
    transient bincount casting. Sort stage holds <=256 MiB bucket payload and
    <=32 KiB boolean comparison payload. NumPy heapsort is in-place with O(1)
    workspace. Python/runtime/allocator overhead and the caller's iterator are
    outside these payload bounds; the enclosing aggregate-RSS guard still applies.
    Disk payload never exceeds max_total_bytes and no second sorted copy exists.
    """
    _cap("max_total_hashes", max_total_hashes)
    _cap("max_total_bytes", max_total_bytes)
    _cap("max_bucket_bytes", max_bucket_bytes, maximum=MAX_BUCKET_BYTES)
    parent = Path(scratch_parent)
    if not parent.is_dir():
        raise ValueError("scratch_parent must be an existing directory")
    _space(parent, 0)
    owned = Path(tempfile.mkdtemp(prefix="exact-hash-audit-", dir=parent))
    byte_counts = [0] * 256
    digest = hashlib.sha256()
    total_bytes = 0
    try:
        for chunk in chunks:
            if not isinstance(chunk, bytes):
                raise TypeError("each hash chunk must be immutable bytes")
            size = len(chunk)
            if size > MAX_CHUNK_BYTES:
                raise ValueError("input chunk exceeds 32 MiB ceiling")
            if size % HASH_BYTES:
                raise ValueError("chunk must contain complete 32-byte hashes")
            if total_bytes + size > max_total_bytes:
                raise ValueError("aggregate byte cap exceeded")
            if (total_bytes + size)//HASH_BYTES > max_total_hashes:
                raise ValueError("aggregate hash cap exceeded")
            if not size:
                continue
            hashes = np.frombuffer(chunk, dtype="V32")
            leading = np.frombuffer(chunk, dtype=np.uint8)[::HASH_BYTES]
            counts = np.bincount(leading, minlength=256)
            # Preflight every bucket before the first write for this chunk.
            for bucket, count in enumerate(counts):
                if byte_counts[bucket] + int(count)*HASH_BYTES > max_bucket_bytes:
                    raise ValueError(f"bucket {bucket:02x} byte cap exceeded")
            ordered = hashes[np.argsort(leading, kind="heapsort")]
            offset = 0
            for bucket, count in enumerate(counts):
                count = int(count)
                if not count:
                    continue
                write_bytes = count*HASH_BYTES
                _space(owned, write_bytes)
                path = owned / f"{bucket:02x}.bin"
                # Only this exclusively owned child is ever opened for writing.
                with path.open("ab") as handle:
                    written = handle.write(memoryview(ordered[offset:offset+count]).cast("B"))
                    if written != write_bytes:
                        raise OSError("short hash bucket write")
                byte_counts[bucket] += write_bytes
                offset += count
            digest.update(chunk)
            total_bytes += size
            del chunk, hashes, leading, ordered, counts
        summaries = []
        duplicate_excess = 0
        for bucket, size in enumerate(byte_counts):
            total = size//HASH_BYTES
            duplicates = 0
            if size:
                path = owned / f"{bucket:02x}.bin"
                if path.stat().st_size != size:
                    raise OSError("hash bucket length changed")
                identities = np.fromfile(path, dtype="V32", count=total)
                if len(identities) != total:
                    raise OSError("short hash bucket read")
                identities.sort(kind="heapsort")
                for start in range(1, total, COMPARE_HASHES):
                    stop = min(total, start+COMPARE_HASHES)
                    duplicates += int(np.count_nonzero(identities[start:stop] == identities[start-1:stop-1]))
                del identities
            duplicate_excess += duplicates
            summaries.append(dict(bucket=f"{bucket:02x}", bytes=size, total=total,
                                  unique=total-duplicates, duplicate_excess=duplicates))
        total = total_bytes//HASH_BYTES
        return dict(schema_version=1, algorithm="full32-leading-byte-buckets-inplace-heapsort",
                    total=total, unique=total-duplicate_excess, duplicate_excess=duplicate_excess,
                    input_bytes=total_bytes, input_stream_sha256=digest.hexdigest(), buckets=summaries,
                    limits=dict(max_total_hashes=max_total_hashes, max_total_bytes=max_total_bytes,
                                max_bucket_bytes=max_bucket_bytes, max_chunk_bytes=MAX_CHUNK_BYTES,
                                free_floor_bytes=FREE_FLOOR_BYTES))
    finally:
        shutil.rmtree(owned)
