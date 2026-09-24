import json
from pathlib import Path
from types import SimpleNamespace
import uuid

import pytest

from tests.research.test_lifecycle import registered, start
from tradingagents.research.onchain_replication.job import resource_policy, reconcile, _base, _command, PREFIX
from tradingagents.research.onchain_replication.provenance import file_hash


def policy(root):
    return {'memory_max_bytes': 512*1024**2, 'memory_high_bytes': 384*1024**2,
            'reserve_bytes': 3*1024**3, 'start_reserve_bytes': 3584*1024**2,
            'disk_floor_bytes': 20*1024**3, 'disk_paths': [str(root)], 'wall_seconds': 300}


def test_explicit_limits_refuse_missing_or_inadequate_contract(tmp_path):
    assert resource_policy(policy(tmp_path), tmp_path) == policy(tmp_path)
    for field, value in [('start_reserve_bytes', 3*1024**3), ('disk_floor_bytes', 1),
                         ('memory_max_bytes', 7*1024**3), ('disk_paths', []), ('wall_seconds', 28801)]:
        with pytest.raises(ValueError):
            resource_policy({**policy(tmp_path), field: value}, tmp_path)


@pytest.mark.parametrize('payload', [{'asset': 'ETH'}, {'asset': 'BTC'}, {}, {'asset': 'DOGE'}, {'asset': 'ETH', 'retries': 1}])
def test_price_job_accepts_only_one_explicit_asset(tmp_path, payload):
    from tradingagents.research.onchain_replication.job import job_schema
    job = {'schema_version': 1, 'kind': 'prices', 'resources': policy(tmp_path), 'environment_input': 'environment', 'payload': payload}
    if payload in ({'asset': 'ETH'}, {'asset': 'BTC'}):
        job_schema(job)
    else:
        with pytest.raises(ValueError, match='one explicit supported asset'):
            job_schema(job)


def test_generic_source_job_publishes_real_capture_denominator_with_synthetic_transport(registered, monkeypatch):
    from tests.research.test_lifecycle import commit
    from tradingagents.research.onchain_replication.job import execute_source_job
    from tradingagents.research.onchain_replication.source_inventory import required_dates
    from tradingagents.research.onchain_replication.price_source import price_policy
    import tradingagents.research.onchain_replication.price_source as source
    root, spec, _ = registered
    (root/'policy.json').write_text(json.dumps(price_policy('ETH')))
    spec['experiments']['example-a']['inputs']['price_policy'] = {'path': 'policy.json', 'sha256': file_hash(root/'policy.json'), 'dataset': 'sample'}
    spec['experiments']['example-a']['cells'] = ['capture', *('price-'+d for y in range(2016, 2025) for d in required_dates(y))]
    spec['experiments']['example-a']['outputs'] = ['cell-ledger.json', 'source-summary.json', 'artifact-index.json']
    actual = source.capture_admitted_prices
    requests = []
    def fetch(*args):
        requests.append(args)
        return 429, {}, b'synthetic refusal'
    monkeypatch.setattr(source, 'capture_admitted_prices', lambda run, asset: actual(run, asset, fetch=fetch))
    with start((root, spec, commit(root, spec))) as run:
        cells = execute_source_job(run, 'prices', {'asset': 'ETH'})
        terminal = run.finish(cells)
        assert terminal['cell_count'] == terminal['unavailable_count'] == 3289
        summary = json.loads((run.directory/'outputs/source-summary.json').read_bytes())
        assert summary['admitted_dates'] == 0 and summary['required_dates'] == 3288
        index = json.loads((run.directory/'outputs/artifact-index.json').read_bytes())
        assert len(requests) == 1 and len(index) > 3289
        assert all(file_hash(root/p) == info['sha256'] for p, info in index.items())


def failed_owner(registered, *, complete=False):
    root, _, source = registered
    with start(registered) as run:
        if complete:
            run.write_json('summary.json', {'fixture': True})
            run.finish([{'id': x, 'status': 'complete'} for x in ('sum', 'count')])
    args = SimpleNamespace(root=root, registration='registration.json', experiment='example-a', source=source)
    base = _base(args)
    (base/'guard').mkdir(parents=True)
    owner = {'experiment': args.experiment, 'source_commit': source, 'nonce': 'synthetic', 'monitor_pid': 2000000000, 'monitor_start_ticks': '0'}
    (base/'owner.json').write_text(json.dumps(owner))
    unit = 'onchain-replication-'+uuid.uuid4().hex+'.service'
    live = {'owner_identity': owner, 'monitor_pid': 2000000000, 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'cgroup': '/sys/fs/cgroup/'+unit, 'unit': unit, 'command': _command(args, 'worker')}
    (base/'guard/live.json').write_text(json.dumps(live))
    return args, base


def test_observer_retains_denominator_and_closes_only_owned_partial_fit(registered):
    args, base = failed_owner(registered)
    batches = args.root/PREFIX/'batches/example-a'
    batches.mkdir(parents=True)
    row = {'id': 'sum', 'status': 'complete', 'metrics': {'accuracy': .5}, 'attempts': ['example-a']}
    (batches/'cell-0000.json').write_text(json.dumps(row))
    fit = args.root/'research_artifacts/onchain_fit_cells'/'synthetic'/args.experiment
    fit.mkdir(parents=True)
    (fit/'claim.json').write_text(json.dumps({'experiment_id': args.experiment, 'provenance': {'source_commit': args.source}}))
    (fit/'checkpoint.bin').write_bytes(b'preserved partial checkpoint')
    result = reconcile(args)
    assert result['status'] == 'failed' and result['cgroup_empty']
    rows = json.loads((base/'postmortem-cells.json').read_bytes())
    assert [(r['id'], r['status']) for r in rows] == [('sum', 'complete'), ('count', 'unavailable')]
    assert (fit/'failed.json').exists() and (fit/'checkpoint.bin').read_bytes() == b'preserved partial checkpoint'
    assert reconcile(args) == result


@pytest.mark.parametrize('fault', ['owner', 'boot', 'command', 'cgroup'])
def test_observer_rejects_foreign_ownership_before_any_action(registered, monkeypatch, fault):
    import tradingagents.research.onchain_replication.job as module
    args, base = failed_owner(registered)
    path = base/'guard/live.json'
    live = json.loads(path.read_bytes())
    if fault == 'owner': live['owner_identity']['experiment'] = 'other'
    if fault == 'boot': live['boot_id'] = 'other'
    if fault == 'command': live['command'] = ['other']
    if fault == 'cgroup': live['cgroup'] = '/tmp/'+live['unit']
    path.write_text(json.dumps(live))
    monkeypatch.setattr(module.subprocess, 'run', lambda *a, **kw: pytest.fail('foreign process action'))
    with pytest.raises(ValueError):
        reconcile(args)
    assert not (base/'observer.json').exists()


def test_active_monitor_refuses_external_reconciliation(registered, monkeypatch):
    import tradingagents.research.onchain_replication.job as module
    args, base = failed_owner(registered)
    monkeypatch.setattr(module, 'same_process_alive', lambda *a: True)
    monkeypatch.setattr(module.subprocess, 'run', lambda *a, **kw: pytest.fail('active owner stopped'))
    with pytest.raises(RuntimeError, match='monitor remains active'):
        reconcile(args)
    assert not (base/'observer.json').exists()


def test_dependency_closure_includes_every_executed_component():
    from tradingagents.research.onchain_replication.job import required_sources
    expected = {'evaluation.py', 'training.py', 'model.py', 'resources.py', 'parquet_ranges.py',
                'range_source.py', 'registered_features.py', 'graph_baselines.py', 'verify.py'}
    assert expected <= {Path(p).name for p in required_sources()}
    from tradingagents.research.admission import runtime_hashes
    assert {'tradingagents/research/'+p for p in runtime_hashes()} <= required_sources()


def test_workspace_binding_records_shared_physical_ledger_and_artifacts(registered, tmp_path):
    from tradingagents.research.onchain_replication.job import workspace_binding
    root, _, _ = registered
    ledger = root/'shared-ledger'
    artifacts = root/'shared-artifacts'
    ledger.mkdir()
    artifacts.mkdir()
    (root/'research_runs').symlink_to(ledger, target_is_directory=True)
    (root/'research_artifacts').symlink_to(artifacts, target_is_directory=True)
    binding = workspace_binding(root)
    assert binding == {'root': str(root), 'ledger': str(ledger), 'artifacts': str(artifacts), 'git_common': str(root/'.git')}


@pytest.mark.parametrize('field', ['root', 'ledger', 'artifacts', 'git_common'])
def test_registered_workspace_mapping_refuses_before_job_access(registered, monkeypatch, field):
    import tradingagents.research.onchain_replication.job as module
    root, _, source = registered
    binding = module.workspace_binding(root)
    binding[field] += '-foreign'
    path = root/'workspace.json'
    path.write_text(json.dumps(binding))
    admitted = SimpleNamespace(ready=True, root=root,
        inputs={'execution_workspace': {'path': path.name, 'sha256': file_hash(path)}})
    monkeypatch.setattr(module, 'admit', lambda **kwargs: admitted)
    args = SimpleNamespace(root=root, registration='registration.json', experiment='example-a', source=source)
    with pytest.raises(ValueError, match='workspace/ledger/artifact mapping'):
        module._admitted(args)


@pytest.mark.parametrize('mutation', ['terminal', 'output', 'claim'])
def test_repeated_observer_revalidates_retained_terminal(registered, mutation):
    args, base = failed_owner(registered)
    reconcile(args)
    directory = args.root/'research_runs'/args.experiment
    if mutation == 'terminal':
        path = directory/'failed.json'
        value = json.loads(path.read_bytes())
        value['reason'] = 'changed after closure'
        path.write_text(json.dumps(value))
    elif mutation == 'output':
        (directory/'outputs/forged.json').write_text('{}')
    else:
        path = directory/'claim.json'
        value = json.loads(path.read_bytes())
        value['source'] = 'f'*40
        path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        reconcile(args)


@pytest.mark.parametrize('foreign', [False, True])
def test_successful_guard_must_be_the_same_owner_and_command(registered, foreign):
    args, base = failed_owner(registered, complete=True)
    live = json.loads((base/'guard/live.json').read_bytes())
    final = {**live, 'phase': 'complete', 'cleanup_verified': True, 'child_exit_code': 0,
             'limit_reason': None, 'memory_events': {'oom': 0, 'oom_kill': 0}}
    if foreign:
        final['command'] = ['other-command']
    (base/'guard/final.json').write_text(json.dumps(final))
    if foreign:
        with pytest.raises(ValueError, match='terminal guard ownership'):
            reconcile(args)
    else:
        assert reconcile(args)['status'] == 'complete'


@pytest.mark.parametrize('complete,name', [(True, 'guard/final.json'), (False, 'postmortem-cells.json'),
    (False, 'guard/observer-death.json'), (False, 'unsealed-journals.json')])
def test_repeated_observer_revalidates_resource_and_denominator_evidence(registered, complete, name):
    args, base = failed_owner(registered, complete=complete)
    if complete:
        live = json.loads((base/'guard/live.json').read_bytes())
        (base/'guard/final.json').write_text(json.dumps({**live, 'phase': 'complete',
            'cleanup_verified': True, 'child_exit_code': 0, 'limit_reason': None,
            'memory_events': {'oom': 0, 'oom_kill': 0}}))
    reconcile(args)
    path = base/name
    value = json.loads(path.read_bytes())
    if name == 'guard/final.json': value['child_exit_code'] = 1
    elif name == 'postmortem-cells.json': value = []
    elif name == 'guard/observer-death.json': value['cleanup_verified'] = False
    else: value = [{'forged': True}]
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='resource or denominator evidence changed'):
        reconcile(args)


@pytest.mark.parametrize('complete,field,value', [(False, 'status', 'complete'), (False, 'claim_sha256', 'f'*64),
    (True, 'experiment_id', 'unrelated'), (True, 'source', 'a'*40), (True, 'cells', []),
    (True, 'registration_sha256', 'b'*64), (True, 'output_sha256', {})])
def test_observer_refuses_unlinked_or_incomplete_lifecycle_terminal(registered, complete, field, value):
    args, base = failed_owner(registered, complete=complete)
    path = args.root/'research_runs'/args.experiment/('complete.json' if complete else 'failed.json')
    terminal = json.loads(path.read_bytes())
    terminal[field] = value
    path.write_text(json.dumps(terminal))
    with pytest.raises(ValueError):
        reconcile(args)
    assert not (base/'observer.json').exists() and not (base/'guard/observer-death.json').exists()
