"""Independent checks on invented recovered source bytes, with no real HTTP."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BASE = Path('research/onchain-graph-2026-09-16/comparison')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixtures = load('recovery_check_fixtures', Path(__file__).with_name('test_onchain_recovery_graph.py'))


@pytest.mark.parametrize('cached', [True, False])
def test_recovered_and_stopped_days_are_independently_checked(tmp_path, monkeypatch, cached):
    monkeypatch.syspath_prepend(str(ROOT/BASE))
    checker = load('recovery_independent_check', ROOT/BASE/'recovery_check.py')
    inventory, plan, requests, _ = fixtures.setup(monkeypatch)
    own = tmp_path/BASE
    (own/'bulk-artifacts').mkdir(parents=True)
    prefix = None
    if cached:
        old = tmp_path/'original'
        first = fixtures.recovery.bulk.capture_day('2001-01-01', old, inventory, plan, fixtures.fixtures.budget())
        prefix = fixtures.reference(old, first['requests']-1)
    requests.clear()
    (own/'capture-plan.json').write_text(json.dumps(plan))
    (own/'bulk-cohort.json').write_text(json.dumps(dict(dates=['2001-01-01','2001-01-02'])))
    (own/'recovery-cohort.json').write_text(json.dumps(dict(dates=['2001-01-01','2001-01-02'],
        prefixes={'2001-01-01':prefix} if cached else {})))
    inv = tmp_path/'research_runs/eth-panel-readiness-20260916/outputs/inventory.json'
    inv.parent.mkdir(parents=True); inv.write_text(json.dumps(inventory))
    budget = fixtures.fixtures.budget()
    cell = fixtures.recovery.recovery_day('2001-01-01', own/'bulk-artifacts/2001-01-01', inventory, plan, budget, reuse_prefix=prefix)
    checked = checker.check_day(tmp_path, '2001-01-01', cell)
    assert checked['status'] == 'verified' and checked['source_status'] == 'complete'
    assert checked['actual_network_requests'] == (1 if cached else 21)
    budget.stopped = 'invented transport stop'
    stopped = fixtures.recovery.recovery_day('2001-01-02', own/'bulk-artifacts/2001-01-02', inventory, plan, budget)
    checked = checker.check_day(tmp_path, '2001-01-02', stopped)
    assert checked['status'] == 'verified' and checked['source_status'] == 'unavailable'
    assert checked['actual_network_requests'] == 0
