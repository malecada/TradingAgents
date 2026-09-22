"""Synthetic hash namespaces only; never reads empirical stores."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

PATH = Path(__file__).resolve().parents[2] / 'research/onchain-graph-2026-09-16/fullpanel_resume/hash_union.py'
SPEC = importlib.util.spec_from_file_location('resume_hash_synthetic', PATH)
union = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(union)


def identity(bucket, number):
    return bytes([bucket]) + number.to_bytes(31, 'big')


def make(tmp_path, populations):
    roots, rows, streams = [], {}, {}
    for index, days in enumerate(populations):
        root = tmp_path / str(index)
        root.mkdir()
        roots.append(root)
        for day, values in days.items():
            raw = b''.join(values)
            union.frozen.append_day(root, [raw], day)
            rows[day] = len(values)
            streams[day] = hashlib.sha256(raw).hexdigest()
    return roots, rows, streams


def run(fixture, **kwargs):
    roots, rows, streams = fixture
    return union.audit(roots, rows, expected_day_stream_sha256=streams, **kwargs)


def saved(roots):
    return {(str(root), p.name): p.read_bytes() for root in roots for p in root.iterdir()}


def test_cross_root_and_within_day_duplicates_preserved(tmp_path):
    a, b = identity(0, 1), identity(255, 2)
    fixture = make(tmp_path, [{0: [a, b], 205: [a]}, {206: [b], 1095: [identity(7, 3)]}])
    before = saved(fixture[0])
    result = run(fixture)
    assert result['rows'] == 5 and result['unique'] == 3
    assert result['duplicate_excess'] == 2 and not result['admitted']
    assert result['days'] == 4 and result['input_bytes'] == 160
    assert result['duplicate_samples'] == [a.hex(), b.hex()]
    assert before == saved(fixture[0])
    assert run(fixture) == result


def test_all_buckets_against_independent_counter(tmp_path):
    values = [identity(i % 256, i % 1000) for i in range(4200)]
    values += values[::13]
    fixture = make(tmp_path, [{0: values[:2200]}, {206: values[2200:]}])
    result = run(fixture, sample_limit=2)
    oracle = Counter(values)
    assert result['unique'] == len(oracle)
    assert result['duplicate_excess'] == len(values) - len(oracle)
    assert len(result['duplicate_samples']) == 2
    for bucket in result['buckets']:
        items = [x for x in values if x[0] == int(bucket['bucket'], 16)]
        assert bucket['rows'] == len(items)
        assert bucket['unique'] == len(set(items))


def test_empty_days_and_comparison_boundary(tmp_path):
    fixture = make(tmp_path, [{0: [], 205: [identity(0, 0)] * 17000},
                              {206: [identity(0, 0)] * 17000, 1095: []}])
    result = run(fixture, sample_limit=0)
    assert result['unique'] == 1 and result['duplicate_excess'] == 33999
    assert result['duplicate_samples'] == [] and result['days'] == 4


def test_unique_and_empty_namespaces(tmp_path):
    fixture = make(tmp_path, [{0: []}, {206: [identity(4, 1)]}])
    assert run(fixture)['admitted']
    assert union.audit([tmp_path / '0'], {0: 0}, expected_day_stream_sha256={0: hashlib.sha256(b'').hexdigest()})['rows'] == 0


@pytest.mark.parametrize('bad', ['missing', 'rows', 'stream', 'missing_stream', 'overlap', 'same_root', 'partial', 'symlink', 'digest', 'route', 'length', 'offset'])
def test_fail_closed(tmp_path, bad):
    fixture = make(tmp_path, [{0: [identity(0, 1)]}, {206: [identity(0, 2)]}])
    roots, rows, streams = fixture
    if bad == 'missing':
        rows.pop(206)
    elif bad == 'rows':
        rows[206] = 2
    elif bad == 'stream':
        streams[206] = '0' * 64
    elif bad == 'missing_stream':
        streams.pop(206)
    elif bad == 'overlap':
        union.frozen.append_day(roots[1], [], 0)
    elif bad == 'same_root':
        roots[1] = roots[0]
    elif bad == 'partial':
        (roots[1] / 'append.lock').mkdir()
    elif bad == 'symlink':
        (roots[1] / 'ff.bin').symlink_to(roots[1] / '00.bin')
    elif bad in ('digest', 'route', 'length'):
        (roots[1] / '00.bin').write_bytes({'digest': identity(0, 3), 'route': identity(1, 2), 'length': b'x'}[bad])
    else:
        path = roots[1] / 'day-0206.json'
        receipt = json.loads(path.read_bytes())
        receipt['buckets'][255]['offset'] = 32
        receipt['total_bucket_bytes'] += 32
        path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        run(fixture)


@pytest.mark.parametrize('limit', ['MAX_BUCKET_BYTES', 'MAX_TOTAL_BYTES'])
def test_combined_caps_before_allocation_or_bucket_read(tmp_path, monkeypatch, limit):
    fixture = make(tmp_path, [{0: [identity(0, 1)]}, {206: [identity(0, 2)]}])
    monkeypatch.setattr(union, limit, 63)
    monkeypatch.setattr(union.np, 'empty', lambda *a, **k: pytest.fail('allocated before cap'))
    original = Path.open
    def protected(path, *args, **kwargs):
        if path.suffix == '.bin':
            pytest.fail('read bucket before cap')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', protected)
    with pytest.raises(ValueError, match='combined'):
        run(fixture)


def test_inventory_metadata_only_and_no_missing_root_creation(tmp_path, monkeypatch):
    fixture = make(tmp_path, [{0: [identity(0, 1)]}, {206: [identity(0, 2)]}])
    original = Path.open
    def protected(path, *args, **kwargs):
        if path.suffix == '.bin':
            pytest.fail('inventory read bucket')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', protected)
    result = union.inventory(fixture[0])
    assert result['input_bytes'] == 64 and result['bucket_bytes'][0] == 64
    missing = tmp_path / 'missing'
    with pytest.raises(ValueError):
        union.inventory([missing])
    assert not missing.exists()


def test_free_floor_before_allocation(tmp_path, monkeypatch):
    fixture = make(tmp_path, [{0: [identity(0, 1)]}, {206: []}])
    monkeypatch.setattr(union.frozen.shutil, 'disk_usage', lambda p: SimpleNamespace(free=union.frozen.FREE_FLOOR_BYTES))
    monkeypatch.setattr(union.np, 'empty', lambda *a, **k: pytest.fail('allocated before floor'))
    with pytest.raises(OSError, match='floor'):
        run(fixture)


def test_receipt_mutation_during_audit_detected(tmp_path, monkeypatch):
    fixture = make(tmp_path, [{0: [identity(0, 1)]}, {206: []}])
    original = union.np.empty
    def changed(*args, **kwargs):
        path = fixture[0][0] / 'day-0000.intent.json'
        value = json.loads(path.read_bytes())
        value['extra'] = 'changed during audit'
        path.write_text(json.dumps(value))
        return original(*args, **kwargs)
    monkeypatch.setattr(union.np, 'empty', changed)
    with pytest.raises(ValueError, match='changed during audit'):
        run(fixture)
