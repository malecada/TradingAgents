"""Invented identities only; no historical source reads or network."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[2] / 'research/onchain-graph-2026-09-16/fullpanel/hash_audit.py'
SPEC = importlib.util.spec_from_file_location('fullpanel_hash_test', PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def identity(first, number):
    return bytes([first]) + number.to_bytes(31, 'big')


def test_exact_nonadjacent_and_withinday_duplicates_preserved(tmp_path):
    values = [identity(0, 1), identity(255, 2), identity(0, 1)]
    one = audit.append_day(tmp_path, [b''.join(values)], 1095)
    audit.append_day(tmp_path, [identity(7, 3)], 0)
    audit.append_day(tmp_path, [identity(255, 2), identity(8, 4)], 501)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    result = audit.audit(tmp_path, {0: 1, 501: 2, 1095: 3})
    assert result['rows'] == 6 and result['unique'] == 4 and result['duplicate_excess'] == 2
    assert not result['admitted'] and result['scratch_preserved']
    assert one['stream_sha256'] == hashlib.sha256(b''.join(values)).hexdigest()
    assert one['bytes'] == 96
    assert result['duplicate_samples'] == [identity(0, 1).hex(), identity(255, 2).hex()]
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    assert audit.audit(tmp_path, {1095: 3, 501: 2, 0: 1}) == result


def test_all_buckets_against_python_counter(tmp_path):
    values = [identity(i % 256, i % 1000) for i in range(4000)]
    values += values[::11]
    oracle = Counter(values)
    audit.append_day(tmp_path, [b''.join(values[:2000])], 9)
    audit.append_day(tmp_path, [b''.join(values[2000:])], 2)
    result = audit.audit(tmp_path, {9: 2000, 2: len(values)-2000}, sample_limit=2)
    assert result['unique'] == len(oracle)
    assert result['duplicate_excess'] == len(values)-len(oracle)
    assert len(result['duplicate_samples']) == 2
    for item in result['buckets']:
        bucket = int(item['bucket'], 16)
        expected = [v for v in values if v[0] == bucket]
        assert item['rows'] == len(expected)
        assert item['unique'] == len(set(expected))


def test_empty_day_and_empty_population(tmp_path):
    assert audit.audit(tmp_path, {})['admitted']
    receipt = audit.append_day(tmp_path, [b''], 3)
    assert receipt['rows'] == 0
    result = audit.audit(tmp_path, {3: 0})
    assert result['admitted'] and result['rows'] == 0
    assert len(result['buckets']) == 256


def test_duplicate_comparison_boundary_and_zero_sample_limit(tmp_path):
    value = identity(0, 0)
    audit.append_day(tmp_path, [value * 40000], 1)
    result = audit.audit(tmp_path, {1: 40000}, sample_limit=0)
    assert result['unique'] == 1 and result['duplicate_excess'] == 39999
    assert result['duplicate_samples'] == []


def test_duplicate_append_rejected_without_changes(tmp_path):
    audit.append_day(tmp_path, [identity(0, 1)], 1)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    with pytest.raises(ValueError, match='already appended'):
        audit.append_day(tmp_path, [identity(0, 2)], 1)
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}


def test_partial_failure_retains_and_blocks(tmp_path):
    def failed():
        yield identity(0, 1)
        raise RuntimeError('injected')
    with pytest.raises(RuntimeError, match='injected'):
        audit.append_day(tmp_path, failed(), 3)
    assert (tmp_path/'00.bin').read_bytes() == identity(0, 1)
    assert (tmp_path/'append.lock').is_dir()
    with pytest.raises(ValueError, match='partial recovery'):
        audit.audit(tmp_path, {3: 1})
    with pytest.raises(FileExistsError):
        audit.append_day(tmp_path, [], 4)


@pytest.mark.parametrize('bad', ['truncated', 'digest', 'counter', 'unknown_day', 'missing_day', 'span', 'symlink'])
def test_corruption_rejected(tmp_path, bad):
    audit.append_day(tmp_path, [identity(0, 1)], 1)
    expected = {1: 1}
    if bad == 'truncated':
        (tmp_path/'00.bin').write_bytes(b'broken')
    elif bad == 'digest':
        (tmp_path/'00.bin').write_bytes(identity(0, 2))
    elif bad == 'unknown_day':
        expected = {2: 1}
    elif bad == 'missing_day':
        expected = {}
    elif bad == 'symlink':
        (tmp_path/'ff.bin').symlink_to(tmp_path/'00.bin')
    else:
        path = tmp_path/'day-0001.json'
        receipt = json.loads(path.read_bytes())
        if bad == 'counter':
            receipt['rows'] = 2
        else:
            receipt['buckets'][0]['offset'] = 32
        path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        audit.audit(tmp_path, expected)


@pytest.mark.parametrize('day', [-1, 1096, True, 1.5])
def test_invalid_day(tmp_path, day):
    with pytest.raises(ValueError):
        audit.append_day(tmp_path, [], day)


def test_bounds_and_short_chunks_stop_before_payload(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match='width'):
        audit.append_day(tmp_path/'short', [b'x'], 0)
    with pytest.raises(ValueError, match='aggregate'):
        audit.append_day(tmp_path/'total', [identity(0, 1)], 0, max_total_bytes=31)
    monkeypatch.setattr(audit, 'MAX_BUCKET_BYTES', 31)
    with pytest.raises(ValueError, match='memory'):
        audit.append_day(tmp_path/'bucket', [identity(0, 1)], 0)
    assert not list(tmp_path.rglob('*.bin'))


def test_free_floor_prevents_intent(tmp_path, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(audit.shutil, 'disk_usage', lambda path: SimpleNamespace(free=audit.FREE_FLOOR_BYTES))
    with pytest.raises(OSError, match='floor'):
        audit.append_day(tmp_path, [], 0)
    assert list(tmp_path.iterdir()) == []
