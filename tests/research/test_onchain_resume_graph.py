"""Synthetic Parquet and fake transports; no network or real observations."""
import importlib.util
import io
import json
from pathlib import Path
import urllib.error

import pytest

ROOT = Path(__file__).resolve().parents[2]
BASE = Path('research/onchain-graph-2026-09-16/comparison')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


engine = load('resume_engine_test', ROOT/BASE/'resume_graph.py')
fixtures = load('resume_bulk_fixtures', Path(__file__).with_name('test_onchain_bulk_graph.py'))


def setup(monkeypatch, *, faults=(), status=200, groups=2):
    monkeypatch.setattr(fixtures, 'bulk', engine.bulk)
    inventory, plan, requests, blocks = fixtures.setup(monkeypatch, status=status, groups=groups)
    original = engine.storage.BinaryCapture
    calls, sleeps = [], []
    failures = iter(faults)
    def factory(spec, directory):
        capture = original(spec, directory)
        good = capture.opener
        class Opener:
            def open(self, request, timeout):
                calls.append(request)
                fault = next(failures, None)
                if isinstance(fault, Exception):
                    raise fault
                if fault == 'short':
                    class Short:
                        status = 200
                        headers = {'content-length': '99', 'etag': '"fixture"'}
                        def __init__(self): self.stream = io.BytesIO(b'partial')
                        def read(self, size): return self.stream.read(size)
                        read1 = read
                        def close(self): self.stream.close()
                    return Short()
                return good.open(request, timeout)
        capture.opener = Opener()
        return capture
    monkeypatch.setattr(engine.storage, 'BinaryCapture', factory)
    monkeypatch.setattr(engine.time, 'sleep', sleeps.append)
    return inventory, plan, calls, sleeps


def reference(directory, count):
    return dict(directory=str(directory), receipt_count=count, files=[
        dict(path=p.name, bytes=p.stat().st_size, sha256=engine.storage.sha(p.read_bytes()))
        for i in range(1, count+1) for suffix in ('-intent.json', '.json', '.body.zst')
        for p in [directory/f'request-{i:04d}{suffix}']])


def test_retry_retains_all_attempts_and_unique_body_accounting(tmp_path, monkeypatch):
    inv, plan, calls, sleeps = setup(monkeypatch, faults=[ConnectionResetError('invented'), 'short'])
    budget = fixtures.budget()
    result = engine.resume_day('2001-01-01', tmp_path/'day', inv, plan, budget)
    assert result['status'] == 'complete', result
    assert sleeps == [5, 15]
    assert len(calls) == result['actual_network_requests'] == result['requests']+2
    assert result['actual_network_received_bytes'] == result['received_bytes']+7
    failed = json.loads((tmp_path/'day-attempts/request-0002.json').read_bytes())
    assert failed['bytes'] == 7 and 'error' in failed
    assert (tmp_path/'day/request-0001.body.zst').samefile(tmp_path/'day-attempts/request-0003.body.zst')
    unique = {(p.stat().st_dev, p.stat().st_ino): p.stat().st_size for p in tmp_path.rglob('*.zst')}
    assert result['retained_raw_bytes'] == budget.new_raw_bytes == sum(unique.values())
    assert result['retained_metadata_allocated_bytes'] == budget.new_metadata_bytes
    assert not result['numerical_integrity_admitted']


def test_exhaustion_stops_later_days(tmp_path, monkeypatch):
    inv, plan, calls, sleeps = setup(monkeypatch, faults=[urllib.error.URLError('[Errno -3] Temporary failure in name resolution')]*4)
    budget = fixtures.budget()
    first = engine.resume_day('2001-01-01', tmp_path/'first', inv, plan, budget)
    second = engine.resume_day('2001-01-02', tmp_path/'second', inv, plan, budget)
    assert first['status'] == second['status'] == 'unavailable'
    assert first['actual_network_requests'] == len(calls) == 4
    assert second['actual_network_requests'] == 0 and sleeps == [5, 15, 45]
    assert 'transport retries exhausted' in budget.stopped


@pytest.mark.parametrize('status', [401, 403, 429, 404, 500])
def test_http_errors_never_retry(tmp_path, monkeypatch, status):
    inv, plan, calls, sleeps = setup(monkeypatch, status=status)
    budget = fixtures.budget()
    cell = engine.resume_day('2001-01-01', tmp_path/'day', inv, plan, budget)
    assert cell['status'] == 'unavailable'
    assert len(calls) == 1 and sleeps == []
    assert bool(budget.stopped) == (status in (401, 403, 429))


def test_prefix_is_exact_copy_only_missing_http(tmp_path, monkeypatch):
    inv, plan, calls, sleeps = setup(monkeypatch)
    old = tmp_path/'original'
    first = engine.bulk.capture_day('2001-01-01', old, inv, plan, fixtures.budget())
    prefix = reference(old, first['requests']-1)
    calls.clear()
    cell = engine.resume_day('2001-01-01', tmp_path/'new', inv, plan, fixtures.budget(), reuse_prefix=prefix)
    assert cell['status'] == 'complete', cell
    assert len(calls) == cell['actual_network_requests'] == 1
    assert cell['reused_requests'] == first['requests']-1
    for entry in prefix['files']:
        assert (old/entry['path']).read_bytes() == (tmp_path/'new'/entry['path']).read_bytes()
    with pytest.raises(FileExistsError):
        engine.resume_day('2001-01-01', tmp_path/'new', inv, plan, fixtures.budget())


def test_tampered_prefix_and_low_disk_do_not_issue_http(tmp_path, monkeypatch):
    from types import SimpleNamespace
    inv, plan, calls, sleeps = setup(monkeypatch)
    old = tmp_path/'original'
    engine.bulk.capture_day('2001-01-01', old, inv, plan, fixtures.budget())
    prefix = reference(old, 1)
    (old/'request-0001.json').write_text('{}')
    calls.clear()
    with pytest.raises(ValueError):
        engine.resume_day('2001-01-01', tmp_path/'bad', inv, plan, fixtures.budget(), reuse_prefix=prefix)
    budget = fixtures.budget()
    budget.disk_usage = lambda _: SimpleNamespace(free=engine.bulk.FREE_FLOOR)
    cell = engine.resume_day('2001-01-01', tmp_path/'low', inv, plan, budget)
    assert cell['status'] == 'unavailable' and cell['actual_network_requests'] == 0
    assert cell['attempts_manifest_sha256'] is None
    assert not calls


def test_maximum_physical_request_denominator(tmp_path, monkeypatch):
    faults = [fault for _ in range(291) for fault in
              (ConnectionResetError('invented'), ConnectionResetError('invented'),
               ConnectionResetError('invented'), None)]
    inv, plan, calls, sleeps = setup(monkeypatch, faults=faults, groups=32)
    budget = fixtures.budget()
    cell = engine.resume_day('2001-01-01', tmp_path/'maximum', inv, plan, budget)
    assert cell['status'] == 'complete', cell
    assert cell['actual_network_requests'] == len(calls) == 1164
    assert cell['logical_requests'] == 291
    assert sleeps == [5, 15, 45]*291
    assert cell['actual_network_received_bytes'] == cell['logical_received_bytes']
    assert cell['actual_network_received_bytes'] <= engine.PHYSICAL_BYTES


def test_disk_stop_between_retries_preserves_actual_attempt_counters(tmp_path, monkeypatch):
    from types import SimpleNamespace
    inv, plan, calls, sleeps = setup(monkeypatch, faults=[ConnectionResetError('invented')])
    budget = fixtures.budget()
    def sleep(_):
        budget.disk_usage = lambda _: SimpleNamespace(free=engine.bulk.FREE_FLOOR)
    monkeypatch.setattr(engine.time, 'sleep', sleep)
    cell = engine.resume_day('2001-01-01', tmp_path/'stopped', inv, plan, budget)
    assert cell['status'] == 'unavailable'
    assert len(calls) == cell['actual_network_requests'] == 1
    assert cell['attempts_manifest_sha256'] is None
    assert (tmp_path/'stopped-attempts/request-0001.json').exists()


@pytest.mark.parametrize('error', [
    urllib.error.URLError('[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed'),
    urllib.error.URLError('[SSL: WRONG_VERSION_NUMBER] wrong version number'),
    urllib.error.URLError('unknown deterministic failure'),
])
def test_security_and_unclassified_url_errors_never_retry(tmp_path, monkeypatch, error):
    inv, plan, calls, sleeps = setup(monkeypatch, faults=[error])
    cell = engine.resume_day('2001-01-01', tmp_path/'day', inv, plan, fixtures.budget())
    assert cell['status'] == 'unavailable' and len(calls) == 1 and sleeps == []
