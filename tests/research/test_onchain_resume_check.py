"""Independent audit of synthetic retry evidence; tampering must be rejected."""
import json
from pathlib import Path

import pytest
from tests.research.test_onchain_resume_graph import BASE, ROOT, engine, fixtures, load, setup, reference


def capture(tmp_path, monkeypatch, *, faults=(), prefix=False):
    monkeypatch.syspath_prepend(str(ROOT/BASE))
    checker = load('resume_independent_test', ROOT/BASE/'resume_check.py')
    inv, plan, calls, sleeps = setup(monkeypatch, faults=faults)
    own = tmp_path/BASE
    (own/'bulk-artifacts').mkdir(parents=True)
    cached = None
    if prefix:
        old = tmp_path/'original'
        first = engine.bulk.capture_day('2001-01-01', old, inv, plan, fixtures.budget())
        cached = reference(old, first['requests']-1)
    (own/'capture-plan.json').write_text(json.dumps(plan))
    (own/'bulk-cohort.json').write_text(json.dumps(dict(dates=['2001-01-01', '2001-01-02'])))
    (own/'resume-cohort.json').write_text(json.dumps(dict(dates=['2001-01-01', '2001-01-02'],
        prefixes={'2001-01-01': cached} if cached else {})))
    path = tmp_path/'research_runs/eth-panel-readiness-20260916/outputs/inventory.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(inv))
    budget = fixtures.budget()
    cell = engine.resume_day('2001-01-01', own/'bulk-artifacts/2001-01-01', inv, plan, budget, reuse_prefix=cached)
    return checker, cell, own, budget, inv, plan


@pytest.mark.parametrize('mode', ['clean', 'retry', 'exhaust', 'prefix'])
def test_independent_checks_all_outcomes(tmp_path, monkeypatch, mode):
    faults = [ConnectionResetError('invented')]*(4 if mode == 'exhaust' else 1) if mode in ('retry', 'exhaust') else []
    checker, cell, own, budget, inv, plan = capture(tmp_path, monkeypatch, faults=faults, prefix=mode == 'prefix')
    report = checker.check_day(tmp_path, '2001-01-01', cell)
    assert report['status'] == 'verified' and report['attempts_verified']
    if mode == 'exhaust':
        stopped = engine.resume_day('2001-01-02', own/'bulk-artifacts/2001-01-02', inv, plan, budget)
        assert checker.check_day(tmp_path, '2001-01-02', stopped)['actual_network_requests'] == 0


@pytest.mark.parametrize('kind', ['counter', 'failed_body', 'mapping', 'hardlink', 'raw_accounting'])
def test_checker_rejects_tampering(tmp_path, monkeypatch, kind):
    checker, cell, own, _, _, _ = capture(tmp_path, monkeypatch, faults=[ConnectionResetError('invented')])
    attempts = own/'bulk-artifacts/2001-01-01-attempts'
    if kind == 'counter':
        cell['actual_network_requests'] -= 1
    elif kind == 'failed_body':
        (attempts/'request-0001.body.zst').write_bytes(b'wrong')
    elif kind == 'mapping':
        path = attempts/'mapping-0002.json'
        value = json.loads(path.read_bytes()); value['delay_seconds'] = 0
        path.write_text(json.dumps(value))
    elif kind == 'hardlink':
        path = own/'bulk-artifacts/2001-01-01/request-0001.body.zst'
        raw = path.read_bytes(); path.unlink(); path.write_bytes(raw)
    else:
        cell['retained_raw_bytes'] += 1
    with pytest.raises(ValueError):
        checker.check_day(tmp_path, '2001-01-01', cell)
