"""Independent adverse guard cases; reuse synthetic admission/kernel fixtures only."""
import copy, dataclasses, importlib.util, json
from pathlib import Path
import pytest

H = Path(__file__).resolve().parent
worker = H.parent / 'real-data-pilot-lock-correction01-2026-10-08'
spec = importlib.util.spec_from_file_location('review_guard_fixtures', worker / 'test_lock01.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
registered, context, live = fixture.registered, fixture.context, fixture.live

@pytest.mark.parametrize('mutation', [
    'owner_source', 'owner_experiment', 'owner_pid', 'owner_ticks',
    'admission_source', 'not_ready', 'guard_command', 'guard_phase',
    'guard_lease', 'guard_release', 'guard_policy', 'changed_job',
    'changed_plan', 'wrong_execution', 'missing_execution_pin',
])
def test_changed_guard_rejects(context, live, mutation):
    run, execution, owner = fixture.setup_run(context, live)
    receipt, value = live
    if mutation == 'owner_source': value['owner_identity']['source_commit'] = '0' * 40
    elif mutation == 'owner_experiment': value['owner_identity']['experiment'] = 'wrong'
    elif mutation == 'owner_pid': value['monitor_pid'] += 1
    elif mutation == 'owner_ticks':
        owner = copy.deepcopy(owner); owner['monitor_start_ticks'] = '0'
        value['owner_identity'] = owner
    elif mutation == 'admission_source': run.admission = dataclasses.replace(run.admission, source='0' * 40)
    elif mutation == 'not_ready': run.admission = dataclasses.replace(run.admission, ready=False)
    elif mutation == 'guard_command': value['command'] = ['wrong']
    elif mutation == 'guard_phase': value['phase'] = 'failed'
    elif mutation == 'guard_lease': value['monotonic_seconds'] -= 100
    elif mutation == 'guard_release': (receipt / 'release.json').write_text('{}')
    elif mutation == 'guard_policy': value['reserve_bytes'] += 1
    elif mutation == 'changed_job': (run.admission.root / 'execution_job.json').write_text('{}')
    elif mutation == 'changed_plan': (run.admission.root / 'pilot.json').write_text('{}')
    elif mutation == 'wrong_execution': execution = copy.deepcopy(execution); execution['environment_input'] = 'wrong'
    elif mutation == 'missing_execution_pin':
        inputs = dict(run.admission.inputs); del inputs['execution_job']
        run.admission = dataclasses.replace(run.admission, inputs=inputs)
    (receipt / 'live.json').write_text(json.dumps(value))
    with fixture._lock(run.admission.root), pytest.raises((ValueError, RuntimeError, KeyError)):
        fixture.extracted()['_guard'](run, execution['resources'], owner, run.admission.root, execution=execution)

def test_fresh_context_checks_twice_without_rereading_via_lifecycle(context, live, monkeypatch):
    run, execution, owner = fixture.setup_run(context, live)
    def unexpected(*args): raise AssertionError('nested lifecycle read attempted')
    monkeypatch.setattr(run, 'read_input', unexpected)
    fixture.extracted()['locked_checks'](run, execution['resources'], owner, run.admission.root, execution)

def test_second_guard_revalidates_changed_bytes(context, live):
    run, execution, owner = fixture.setup_run(context, live)
    guard = fixture.extracted()['_guard']
    with fixture._lock(run.admission.root):
        guard(run, execution['resources'], owner, run.admission.root, execution=execution)
        (run.admission.root / 'execution_job.json').write_text('{}')
        with pytest.raises(ValueError, match='registered pilot input differs'):
            guard(run, execution['resources'], owner, run.admission.root, execution=execution)
