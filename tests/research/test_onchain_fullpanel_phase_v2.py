"""Synthetic exact phase-byte regression; no empirical rows or recounts."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'research/onchain-graph-2026-09-16/fullpanel'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


v2 = load('fullpanel_phase_v2_test', BASE/'check_final_phase_v2.py')
original = load('fullpanel_phase_v2_original', BASE/'check_final.py')


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def phase_fixture(reused=False):
    histogram = {2: 3, 10: 7, 100: 1, 0: 2}
    if reused:
        histogram = {str(k): n for k, n in histogram.items()}
    phase = dict(source_reused=reused, source=dict(activity=dict(
        in_degree_histogram=histogram, out_degree_histogram=dict(histogram),
        unchanged_string_keys={'2': 4, '10': 5}, events=17)),
        count=dict(features={'local40_sums': list(range(40))}),
        total_seconds=1.23456789, previous_output_sha256='a'*64)
    raw = encoded(phase)
    return json.loads(raw), raw


@pytest.mark.parametrize('reused', [False, True])
def test_exact_original_phase_bytes_and_hash_without_mutation(reused):
    phase, expected = phase_fixture(reused)
    unchanged = copy.deepcopy(phase)
    corrected = v2.json_bytes(phase)
    assert corrected == expected and len(corrected) == len(expected)
    assert hashlib.sha256(corrected).digest() == hashlib.sha256(expected).digest()
    assert phase == unchanged
    assert all(type(k) is str for k in phase['source']['activity']['in_degree_histogram'])
    assert (original.json_bytes(phase) == expected) is reused
    restored = json.loads(corrected)
    assert restored == phase
    assert list(restored['source']['activity']['unchanged_string_keys']) == ['10', '2']


@pytest.mark.parametrize('change', ['degree_count', 'feature', 'timing', 'source_reused'])
def test_numerical_and_timing_corruption_still_fails_exact_binding(change):
    phase, expected = phase_fixture()
    if change == 'degree_count':
        phase['source']['activity']['in_degree_histogram']['10'] += 1
    elif change == 'feature':
        phase['count']['features']['local40_sums'][9] += 1
    elif change == 'timing':
        phase['total_seconds'] += 0.00000001
    else:
        phase['source_reused'] = True
    with pytest.raises(AssertionError):
        assert hashlib.sha256(v2.json_bytes(phase)).digest() == hashlib.sha256(expected).digest()


@pytest.mark.parametrize('key', ['01', '-1', '+2', '1.0', ' 1', '', '2e1', 2, True])
@pytest.mark.parametrize('reused', [False, True])
def test_invalid_or_ambiguous_histogram_keys_rejected(key, reused):
    phase, _ = phase_fixture(reused)
    phase['source']['activity']['in_degree_histogram'][key] = 1
    with pytest.raises(ValueError, match='canonical'):
        v2.json_bytes(phase)


@pytest.mark.parametrize('value', [None, 0, 1, 'false'])
def test_source_origin_flag_cannot_be_coerced(value):
    phase, _ = phase_fixture()
    phase['source_reused'] = value
    with pytest.raises(ValueError, match='boolean'):
        v2.json_bytes(phase)


def test_original_module_bytes_bound_and_identity_preserved(tmp_path):
    original_path = tmp_path/v2.BASE/'check_final.py'
    original_path.parent.mkdir(parents=True)
    original_path.write_bytes((BASE/'check_final.py').read_bytes())
    checker = v2.load_original(tmp_path)
    assert Path(checker.__file__) == original_path
    assert checker.main.__code__.co_filename == str(original_path)
    assert checker.verify_daily.__code__.co_filename == str(original_path)
    assert checker.json_bytes is v2.json_bytes
    assert checker.file_sha(original_path) == v2.ORIGINAL_SHA256
    original_path.write_bytes(original_path.read_bytes()+b'\nraise RuntimeError("must never execute")\n')
    with pytest.raises(ValueError, match='source hash'):
        v2.load_original(tmp_path)


def test_report_provenance_keeps_original_exclusive_publisher(tmp_path):
    calls = []
    def publish(path, value):
        calls.append(path)
        with path.open('xb') as output:
            output.write(encoded(value))
    checker = SimpleNamespace(day_module=lambda: SimpleNamespace(publish_report=publish))
    metadata = dict(wrapper_sha256='a'*64, original_checker_sha256=v2.ORIGINAL_SHA256)
    v2.wrap_publication(checker, metadata)
    result = dict(passed=True, reviewer_script_sha256=v2.ORIGINAL_SHA256)
    before = copy.deepcopy(result)
    path = tmp_path/'report.json'
    checker.day_module().publish_report(path, result)
    output = json.loads(path.read_bytes())
    assert output['phase_serialization_correction'] == metadata and result == before
    assert output['reviewer_script_sha256'] == v2.ORIGINAL_SHA256
    with pytest.raises(FileExistsError):
        checker.day_module().publish_report(path, result)
    assert calls == [path, path]


def test_cli_delegates_unchanged_to_original_main(monkeypatch):
    arguments = ['check_final_phase_v2.py', '--root', '/synthetic', '--source', 'b'*40, '--report', '/synthetic/report.json']
    seen = []
    monkeypatch.setattr(v2, 'load_original', lambda root: SimpleNamespace(main=lambda: seen.append((root, list(__import__('sys').argv)))))
    monkeypatch.setattr('sys.argv', arguments)
    v2.main()
    assert seen == [('/synthetic', arguments)]


@pytest.mark.parametrize('reused', [False, True])
def test_frozen_verify_daily_strict_phase_and_manifest_roundtrip(tmp_path, reused):
    """Synthetic compact evidence exercises both original exact-byte checks."""
    fixture = load('phase_v2_compact_fixture', ROOT/'tests/research/test_onchain_fullpanel_final.py')
    run, plan, date, value, previous = fixture.daily_fixture(tmp_path)
    value['source_reused'] = reused
    for name in v2.HISTOGRAMS:
        value['source']['activity'][name] = {'2': 3, '10': 7, '100': 1}
    phase = {k: copy.deepcopy(v) for k, v in value.items() if k not in original.EXTRA_DAILY_KEYS}
    # Invented producer receipt: fresh dict keys were integers; reused were text.
    producer = copy.deepcopy(phase)
    if not reused:
        for name in v2.HISTOGRAMS:
            producer['source']['activity'][name] = {int(k): n for k, n in producer['source']['activity'][name].items()}
    raw = encoded(producer)
    digest = hashlib.sha256(raw).hexdigest()
    value['independent']['phase_sha256'] = digest
    audit_path = tmp_path/value['audit']['path']
    fixture.publish(audit_path, value['independent'])
    value['audit']['sha256'] = original.file_sha(audit_path)
    phase_name = str(Path(original.BASE)/'artifacts/scratch'/date/'phase.json')
    for item in value['scratch_manifest']:
        if item['path'] == phase_name:
            item.update(sha256=digest, bytes=len(raw))
    output = run/'outputs'/('day-'+date+'.json')
    fixture.publish(output, value)
    cleanup_path = tmp_path/original.BASE/'artifacts/cleanup'/(date+'.json')
    cleanup = original.load(cleanup_path)
    cleanup.update(daily_output_sha256=original.file_sha(output), bytes=sum(m['bytes'] for m in value['scratch_manifest']))
    fixture.publish(cleanup_path, cleanup)
    if not reused:
        with pytest.raises(AssertionError):
            original.verify_daily(tmp_path, run, plan, date, value, previous, set())
    corrected = v2.load_original(ROOT)
    assert corrected.verify_daily(tmp_path, run, plan, date, value, previous, set())['passed']
    value['total_seconds'] += 0.01
    with pytest.raises(AssertionError):
        corrected.verify_daily(tmp_path, run, plan, date, value, previous, set())
