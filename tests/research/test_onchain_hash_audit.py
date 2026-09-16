"""Exact synthetic hash fixtures; no network or actual source identities."""
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


PATH = Path(__file__).resolve().parents[2] / "research/onchain-graph-2026-09-16/comparison/hash_audit.py"
SPEC = importlib.util.spec_from_file_location("onchain_hash_audit", PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


@pytest.fixture(autouse=True)
def ample_disk(monkeypatch):
    monkeypatch.setattr(audit.shutil, "disk_usage", lambda path: SimpleNamespace(free=100*1024**3))


def run(chunks, parent, **kwargs):
    limits = dict(max_total_hashes=100000, max_total_bytes=3200000)
    limits.update(kwargs)
    return audit.audit_hashes(chunks, scratch_parent=parent, **limits)


def identity(prefix, suffix):
    return bytes([prefix]) + bytes(23) + suffix.to_bytes(8, "big")


def test_exact_cross_chunk_day_and_bucket_duplicates(tmp_path):
    a, b, c = identity(0, 1), identity(255, 1), identity(0, 2)
    chunks = [a+b, c+a, b+a]  # Three invented day chunks; 32-byte suffix matters.
    result = run(chunks, tmp_path)
    assert (result["total"], result["unique"], result["duplicate_excess"]) == (6, 3, 3)
    assert result["input_stream_sha256"] == hashlib.sha256(b"".join(chunks)).hexdigest()
    assert result["buckets"][0] == dict(bucket="00", bytes=128, total=4, unique=2, duplicate_excess=2)
    assert result["buckets"][255]["duplicate_excess"] == 1
    assert len(result["buckets"]) == 256
    assert list(tmp_path.iterdir()) == []


def test_permutation_invariant_counts_and_order_sensitive_digest(tmp_path):
    rows = [identity(1, 1), identity(2, 1), identity(1, 2), identity(1, 1)]
    first = run([b"".join(rows)], tmp_path)
    second = run([b"".join(reversed(rows))], tmp_path)
    assert first["buckets"] == second["buckets"]
    assert first["unique"] == second["unique"] == 3
    assert first["input_stream_sha256"] != second["input_stream_sha256"]


@pytest.mark.parametrize("chunks,limits,match", [
    ([bytes(31)], {}, "complete 32-byte"),
    ([bytes(33)], {}, "complete 32-byte"),
    ([bytes(64)], {"max_total_hashes": 1}, "hash cap"),
    ([bytes(64)], {"max_total_bytes": 63}, "byte cap"),
    ([bytes(32), bytes(32)], {"max_bucket_bytes": 32}, "bucket 00"),
    ([bytes(audit.MAX_CHUNK_BYTES+32)], {}, "32 MiB"),
])
def test_caps_and_malformed_chunks_cleanup_only_owned_child(tmp_path, chunks, limits, match):
    preserved = tmp_path / "previous.bin"
    preserved.write_bytes(b"retained original")
    original_dir = tmp_path / "old-audit"
    original_dir.mkdir()
    (original_dir / "00.bin").write_bytes(b"old")
    with pytest.raises(ValueError, match=match):
        run(chunks, tmp_path, **limits)
    assert preserved.read_bytes() == b"retained original"
    assert (original_dir / "00.bin").read_bytes() == b"old"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["old-audit", "previous.bin"]


def test_disk_stop_before_each_write_preserves_parent(tmp_path, monkeypatch):
    free = iter([audit.FREE_FLOOR_BYTES+1000, audit.FREE_FLOOR_BYTES+1000, audit.FREE_FLOOR_BYTES+31])
    monkeypatch.setattr(audit.shutil, "disk_usage", lambda path: SimpleNamespace(free=next(free)))
    with pytest.raises(OSError, match="20 GiB"):
        run([identity(0, 1), identity(1, 2)], tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_comparison_window_boundary_counts_duplicate_once(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "COMPARE_HASHES", 2)
    rows = [identity(3, n) for n in [1, 2, 2, 2, 3, 3, 4]]
    result = run([b"".join(rows)], tmp_path)
    assert result["unique"] == 4
    assert result["duplicate_excess"] == 3


def test_empty_stream_and_nonbyte_failure(tmp_path):
    result = run([b""], tmp_path)
    assert result["total"] == result["unique"] == result["duplicate_excess"] == 0
    assert result["input_stream_sha256"] == hashlib.sha256(b"").hexdigest()
    with pytest.raises(TypeError, match="immutable bytes"):
        run([bytearray(32)], tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_source_iterator_failure_cleans_only_new_scratch(tmp_path):
    def broken():
        yield bytes(32)
        raise RuntimeError("invented source failure")

    with pytest.raises(RuntimeError, match="invented source"):
        run(broken(), tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_memory_ceiling_cannot_be_relaxed(tmp_path):
    with pytest.raises(ValueError, match="fixed memory ceiling"):
        run([], tmp_path, max_bucket_bytes=audit.MAX_BUCKET_BYTES+32)
