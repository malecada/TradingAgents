"""Owned local supervisor/guard/worker for separately registered finite jobs.

No invocation is an admission by itself. The exact execution_job input, source,
environment, scientific inputs and cumulative claim budget must pass admission.
No terminal or previously reserved launch identity is restarted.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid

from ..admission import admit
from ..lifecycle import ResearchRun, _immutable, _encode
from .provenance import digest, file_hash, durable_mkdir, sync_directory
from . import resources

MODULE = 'tradingagents.research.onchain_replication.job'
PREFIX = 'research_artifacts/onchain-paper-replication-2026-09-24'


def required_sources():
    """Conservative complete package closure, including dynamically chosen arms."""
    package = Path(__file__).resolve().parent
    return ({'tradingagents/research/onchain_replication/'+p.name for p in package.glob('*.py')}
            | {'tradingagents/research/'+p.name for p in package.parent.glob('*.py')}
            | {'tradingagents/__init__.py'})


def same_process_alive(pid, ticks):
    if type(pid) is not int or pid <= 0 or not isinstance(ticks, str) or not ticks.isdecimal():
        raise ValueError('monitor process identity fields invalid')
    try:
        return (Path('/proc')/str(pid)/'stat').read_text().rsplit(')', 1)[1].split()[19] == ticks
    except FileNotFoundError:
        return False


def resource_policy(value, root):
    required = {'memory_max_bytes', 'memory_high_bytes', 'reserve_bytes', 'start_reserve_bytes',
                'disk_floor_bytes', 'disk_paths', 'wall_seconds'}
    if set(value) != required:
        raise ValueError('execution resource policy fields differ')
    for name in required-{'disk_paths'}:
        if type(value[name]) is not int or value[name] <= 0:
            raise ValueError('positive integer resource limits required')
    if not value['memory_high_bytes'] <= value['memory_max_bytes'] <= 6*resources.GIB:
        raise ValueError('execution memory ceiling differs')
    if value['reserve_bytes'] < 3*resources.GIB or value['start_reserve_bytes'] < value['memory_max_bytes']+value['reserve_bytes']:
        raise ValueError('execution host reserves below contract')
    if value['disk_floor_bytes'] < 20*resources.GIB or value['wall_seconds'] > 28800:
        raise ValueError('execution disk/wall limits differ')
    paths = value['disk_paths']
    if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)) or any(not isinstance(p, str) or not Path(p).is_absolute() for p in paths):
        raise ValueError('explicit unique guard volumes required')
    if root.stat().st_dev not in {Path(p).stat().st_dev for p in paths}:
        raise ValueError('guard omits artifact volume')
    return value


def job_schema(job):
    if set(job) != {'schema_version', 'kind', 'resources', 'environment_input', 'payload'} or job['schema_version'] != 1 or job['kind'] not in ('fit', 'ranges', 'prices', 'coinmetrics_prices'):
        raise ValueError('execution job schema/kind differs')
    if job['kind'] == 'ranges' and job['payload'] != {}:
        raise ValueError('range job has no implicit payload overrides')
    if job['kind'] in ('prices', 'coinmetrics_prices') and (not isinstance(job['payload'], dict) or set(job['payload']) != {'asset'} or job['payload']['asset'] not in ('BTC', 'ETH')):
        raise ValueError('price job requires one explicit supported asset')


def workspace_binding(root):
    root = Path(root).resolve()
    common = subprocess.check_output(['git', 'rev-parse', '--git-common-dir'], cwd=root, text=True).strip()
    return {'root': str(root), 'ledger': str((root/'research_runs').resolve()),
            'artifacts': str((root/'research_artifacts').resolve()),
            'git_common': str((root/common).resolve())}


def _admitted(args):
    admitted = admit(root=args.root, registration=args.registration,
                     experiment=args.experiment, source=args.source)
    if not admitted.ready:
        raise ValueError('execution inputs not ready')
    if 'execution_workspace' in admitted.inputs:
        layout = admitted.inputs['execution_workspace']
        raw = (admitted.root/layout['path']).read_bytes()
        if digest(raw) != layout['sha256'] or json.loads(raw) != workspace_binding(admitted.root):
            raise ValueError('registered execution workspace/ledger/artifact mapping differs')
    info = admitted.inputs['execution_job']
    raw = (admitted.root/info['path']).read_bytes()
    if digest(raw) != info['sha256']:
        raise ValueError('execution job bytes differ')
    job = json.loads(raw)
    job_schema(job)
    resource_policy(job['resources'], admitted.root)
    source = admitted.experiment['source_files']
    if not required_sources() <= set(source):
        raise ValueError('execution dependency source closure not registered')
    if Path(__file__).resolve() != (admitted.root/'tradingagents/research/onchain_replication/job.py').resolve():
        raise ValueError('execution imported from outside admitted source root')
    return admitted, job


def _base(args):
    return Path(args.root).resolve()/PREFIX/'runs'/args.experiment


def _command(args, mode):
    return [sys.executable, '-B', '-m', MODULE, '--mode', mode, '--root', str(Path(args.root).resolve()),
            '--registration', args.registration, '--experiment', args.experiment, '--source', args.source]


def _once(path, value):
    if path.exists():
        if path.is_symlink() or path.read_bytes() != _encode(value):
            raise ValueError('retained observer bytes differ')
    else:
        _immutable(path, value)


def _terminal(path, claim, claim_sha256, root, status):
    terminal = json.loads(path.read_bytes())
    if terminal.get('status') != status or terminal.get('experiment_id') != claim['experiment_id'] or terminal.get('claim_sha256') != claim_sha256:
        raise ValueError('lifecycle terminal does not bind exact owner claim')
    actual = {p.name: file_hash(p) for p in (path.parent/'outputs').iterdir() if p.is_file()}
    if terminal.get('output_sha256') != actual:
        raise ValueError('lifecycle terminal output bytes differ')
    if status == 'complete':
        if terminal.get('source') != claim['source'] or terminal.get('registration_sha256') != claim['registration_sha256']:
            raise ValueError('completed source/registration differs')
        cells = terminal.get('cells', [])
        ids = [c['id'] for c in cells]
        if len(ids) != len(set(ids)) or set(ids) != set(claim['experiment']['cells']) or terminal.get('cell_count') != len(ids):
            raise ValueError('completed cell denominator differs')
        if any(c.get('status') not in ('complete', 'unavailable') or (c['status'] == 'unavailable' and not c.get('reason')) for c in cells):
            raise ValueError('completed cell dispositions invalid')
        if terminal.get('unavailable_count') != sum(c['status'] == 'unavailable' for c in cells) or set(actual) != set(claim['experiment']['outputs']):
            raise ValueError('completed output/unavailability denominator differs')
    return terminal


def _observer_evidence(base):
    names = ('launch.json', 'guard/live.json', 'guard/final.json',
             'guard/observer-death.json', 'postmortem-cells.json', 'unsealed-journals.json')
    return {name: file_hash(base/name) for name in names if (base/name).exists()}


def launch(args):
    _admitted(args)
    base = _base(args)
    durable_mkdir(base.parent)
    base.mkdir(exist_ok=False)
    sync_directory(base.parent)
    nonce = uuid.uuid4().hex
    _immutable(base/'launch.json', {'experiment': args.experiment, 'source_commit': args.source,
                                  'supervisor_pid': os.getpid(), 'nonce': nonce})
    monitor = subprocess.Popen(_command(args, 'monitor')+['--owner-pid', str(os.getpid()), '--nonce', nonce], cwd=args.root)
    def stop(signum, frame):
        if monitor.poll() is None:
            monitor.terminate()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    monitor.wait()
    result = reconcile(args)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result['status'] == 'complete' else 1


def monitor(args):
    resources.bind_parent_death(args.owner_pid)
    _, job = _admitted(args)
    base = _base(args)
    launch_record = json.loads((base/'launch.json').read_bytes())
    if launch_record != {'experiment': args.experiment, 'source_commit': args.source,
                         'supervisor_pid': args.owner_pid, 'nonce': args.nonce}:
        raise ValueError('execution supervisor identity differs')
    owner = {**launch_record, 'monitor_pid': os.getpid(),
             'monitor_start_ticks': Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]}
    _immutable(base/'owner.json', owner)
    result = resources.guarded_run(_command(args, 'worker'), cwd=args.root, receipt_dir=base/'guard',
        memory_swap_max_bytes=0, owner_identity=owner, **job['resources'])
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    observed = reconcile(args)
    return 0 if result['phase'] == 'complete' and observed['status'] == 'complete' else 1


def execute_source_job(run, kind, payload):
    if kind == 'ranges':
        from .range_source import capture_ranges
        cells, summary, directory = capture_ranges(run)
    elif kind == 'prices':
        from .price_source import capture_admitted_prices
        cells, summary, directory = capture_admitted_prices(run, payload['asset'])
    elif kind == 'coinmetrics_prices':
        from .coinmetrics_prices import capture_admitted_prices
        cells, summary, directory = capture_admitted_prices(run, payload['asset'])
    else:
        raise ValueError('source job kind required')
    run.write_json('cell-ledger.json', cells)
    run.write_json('source-summary.json', summary)
    run.write_json('artifact-index.json', {str(p.relative_to(run.admission.root)): {'sha256': file_hash(p), 'bytes': p.stat().st_size}
        for p in directory.rglob('*') if p.is_file()})
    return cells


def worker(args):
    admitted, job = _admitted(args)
    root, base = admitted.root, _base(args)
    policy = job['resources']
    live = resources.assert_guarded_worker(base/'guard', _command(args, 'worker'),
        required_paths=[Path(p) for p in policy['disk_paths']], wall_seconds=policy['wall_seconds'],
        memory_max_bytes=policy['memory_max_bytes'], memory_high_bytes=policy['memory_high_bytes'])
    owner = json.loads((base/'owner.json').read_bytes())
    if live['owner_identity'] != owner or owner['experiment'] != args.experiment or owner['source_commit'] != args.source:
        raise ValueError('execution worker ownership differs')
    if any(live[k] != v for k, v in policy.items()):
        raise ValueError('execution guard policy differs from registration')
    def stop(signum, frame):
        raise SystemExit('owned execution interrupted; never relaunch this identity')
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    with ResearchRun.start(root=root, registration=args.registration, experiment=args.experiment, source=args.source) as run:
        from .environment import inventory
        if inventory(root, include_torch=job['kind'] == 'fit') != json.loads(run.read_input(job['environment_input'])):
            raise ValueError('registered execution environment differs')
        if job['kind'] in ('ranges', 'prices', 'coinmetrics_prices'):
            cells = execute_source_job(run, job['kind'], job['payload'])
        else:
            import torch
            torch.set_num_threads(2)
            from .job_payload import execute_fit_payload
            from .cells import lifecycle_cell_id
            scientific, _ = execute_fit_payload(run, job['payload'])
            cells = [{**c, 'id': lifecycle_cell_id(c['id']), 'scientific_id': c['id']} for c in scientific]
        if any(c['status'] == 'failed' for c in cells):
            run.fail('one or more finite cells failed; complete ledger retained')
        else:
            run.finish(cells)


def reconcile(args):
    """After process death, close ownership and retain the complete denominator."""
    root, base = Path(args.root).resolve(), _base(args)
    guard_dir = base/'guard'
    if not (guard_dir/'live.json').exists():
        return {'status': 'no_guard_release', 'experiment': args.experiment}
    owner = json.loads((base/'owner.json').read_bytes())
    live = json.loads((guard_dir/'live.json').read_bytes())
    if owner.get('experiment') != args.experiment or owner.get('source_commit') != args.source or live.get('owner_identity') != owner or live.get('monitor_pid') != owner.get('monitor_pid'):
        raise ValueError('observer ownership differs; no process action authorized')
    if live['boot_id'] != Path('/proc/sys/kernel/random/boot_id').read_text().strip() or live['command'] != _command(args, 'worker'):
        raise ValueError('observer boot/command differs')
    if same_process_alive(owner['monitor_pid'], owner['monitor_start_ticks']):
        if owner['monitor_pid'] != os.getpid():
            raise RuntimeError('owner monitor remains active; external reconciliation refused')
        final_path = guard_dir/'final.json'
        if not final_path.exists() or json.loads(final_path.read_bytes()).get('cleanup_verified') is not True:
            raise RuntimeError('monitor may reconcile itself only after terminal cleanup')
    group = Path(live['cgroup']) if live.get('cgroup') else None
    if group is not None:
        if not group.is_relative_to('/sys/fs/cgroup') or group.name != live['unit'] or not group.name.startswith('onchain-replication-'):
            raise ValueError('observer cgroup path differs')
        def populated():
            return group.exists() and dict(line.split() for line in (group/'cgroup.events').read_text().splitlines()).get('populated') != '0'
        deadline = time.monotonic()+20
        while populated() and time.monotonic() < deadline:
            time.sleep(.25)
        if populated():
            subprocess.run(['systemctl', '--user', 'stop', live['unit']], check=True, capture_output=True, timeout=10)
        if populated():
            raise RuntimeError('owned cgroup death unproven; no closure/reuse')
    if (base/'observer.json').exists():
        result = json.loads((base/'observer.json').read_bytes())
        if result['owner_sha256'] != file_hash(base/'owner.json'):
            raise ValueError('prior observer ownership changed')
        if result.get('evidence_sha256') != _observer_evidence(base):
            raise ValueError('prior observer resource or denominator evidence changed')
        run_dir = root/'research_runs'/args.experiment
        if result['status'] == 'not_admitted':
            if (run_dir/'claim.json').exists():
                raise ValueError('claim appeared after not-admitted closure')
        else:
            status = 'failed' if result['status'] == 'failed' else 'complete'
            path = run_dir/(status+'.json')
            claim_path = run_dir/'claim.json'
            claim = json.loads(claim_path.read_bytes())
            if claim['experiment_id'] != args.experiment or claim['source'] != args.source or claim['registration'] != args.registration:
                raise ValueError('prior observer claim differs')
            if file_hash(path) != result['terminal_sha256'] or (run_dir/('complete.json' if status == 'failed' else 'failed.json')).exists():
                raise ValueError('prior observer terminal changed')
            _terminal(path, claim, file_hash(claim_path), root, status)
        return result
    run_dir = root/'research_runs'/args.experiment
    if not (run_dir/'claim.json').exists():
        result = {'status': 'not_admitted', 'owner_sha256': file_hash(base/'owner.json'),
                  'evidence_sha256': _observer_evidence(base)}
        _immutable(base/'observer.json', result)
        return result
    if group is None:
        raise RuntimeError('admitted run has no cgroup death proof')
    claim_path = run_dir/'claim.json'
    claim = json.loads(claim_path.read_bytes())
    if claim['experiment_id'] != args.experiment or claim['source'] != args.source or claim['registration'] != args.registration:
        raise ValueError('observer claim differs')
    if (run_dir/'complete.json').exists():
        terminal = _terminal(run_dir/'complete.json', claim, file_hash(claim_path), root, 'complete')
        if (run_dir/'failed.json').exists():
            raise ValueError('contradictory lifecycle terminals')
        final = json.loads((guard_dir/'final.json').read_bytes()) if (guard_dir/'final.json').exists() else {}
        if final and any(final.get(k) != live.get(k) for k in ('owner_identity', 'monitor_pid', 'boot_id', 'cgroup', 'unit', 'command')):
            raise ValueError('terminal guard ownership differs from verified live receipt')
        good = final.get('phase') == 'complete' and final.get('cleanup_verified') is True and final.get('child_exit_code') == 0 and final.get('limit_reason') is None and all(final.get('memory_events', {}).get(k) == 0 for k in ('oom', 'oom_kill'))
        result = {'status': 'complete' if good else 'resource_verification_failed', 'owner_sha256': file_hash(base/'owner.json'),
                  'terminal_sha256': file_hash(run_dir/'complete.json'), 'cgroup_empty': True,
                  'all_cells_complete': terminal['unavailable_count'] == 0, 'financial_completion': False,
                  'evidence_sha256': _observer_evidence(base)}
        _immutable(base/'observer.json', result)
        return result
    if (run_dir/'failed.json').exists():
        _terminal(run_dir/'failed.json', claim, file_hash(claim_path), root, 'failed')
    recorded = {}
    from .cells import lifecycle_cell_id
    for path in sorted((root/PREFIX/'batches'/args.experiment).glob('cell-*.json')):
        row = json.loads(path.read_bytes())
        registered_id = lifecycle_cell_id(row['id'])
        if registered_id in recorded:
            raise ValueError('duplicate durable cell disposition')
        recorded[registered_id] = {**row, 'id': registered_id, 'scientific_id': row['id']}
    for name in claim['experiment']['cells']:
        path = root/PREFIX/'sources'/args.experiment/(name+'.json')
        if path.exists():
            row = json.loads(path.read_bytes())
            if row['id'] != name or name in recorded:
                raise ValueError('source disposition identity differs')
            recorded[name] = row
    if not set(recorded) <= set(claim['experiment']['cells']):
        raise ValueError('unregistered durable cell disposition')
    cells = [recorded.get(name, {'id': name, 'status': 'unavailable', 'reason': 'owned worker ended before durable cell disposition; no retry'}) for name in claim['experiment']['cells']]
    _once(base/'postmortem-cells.json', cells)
    run = ResearchRun(SimpleNamespace(root=root, experiment_id=args.experiment))
    run._claim_sha256 = file_hash(claim_path)
    if not (run_dir/'failed.json').exists():
        run.fail('outer observer verified owned cgroup death; complete denominator retained')
    _terminal(run_dir/'failed.json', claim, file_hash(claim_path), root, 'failed')
    certificate = {**live, 'phase': 'failed', 'cleanup_verified': True,
                   'qualification': 'owned cgroup death verified by observer; not a successful resource run',
                   'live_sha256': file_hash(guard_dir/'live.json')}
    _once(guard_dir/'observer-death.json', certificate)
    journals = []
    for directory in sorted((root/'research_artifacts/onchain_representations').glob('*/'+args.experiment)):
        if (directory/'complete.json').exists() or (directory/'failed.json').exists():
            continue
        journal_owner = json.loads((directory/'owner.json').read_bytes())
        proof = {'claim_sha256': file_hash(claim_path), 'failed_sha256': file_hash(run_dir/'failed.json'),
                 'owner_sha256': file_hash(base/'owner.json'), 'guard_sha256': file_hash(guard_dir/'observer-death.json'),
                 'guard_file': 'observer-death.json', 'start_sha256': file_hash(directory/'start.json')}
        # Numeric recovery must run under a separately guarded bounded checker;
        # the observer publishes the exact proof but never allocates graph arrays.
        journals.append({'directory': str(directory), 'owner': journal_owner, 'proof': proof,
                         'status': 'requires_bounded_reconciliation'})
    _once(base/'unsealed-journals.json', journals)
    for directory in sorted((root/'research_artifacts/onchain_fit_cells').glob('*/'+args.experiment)):
        if (directory/'complete.json').exists() or (directory/'failed.json').exists():
            continue
        fit = json.loads((directory/'claim.json').read_bytes())
        if fit['experiment_id'] != args.experiment or fit['provenance']['source_commit'] != args.source:
            raise ValueError('fit owner differs during closure')
        _immutable(directory/'failed.json', {'reason': 'outer observer proved worker death; checkpoint bytes retained',
            'last_checkpoint': None, 'next_action': 'Inspect saved checkpoints and register a new continuation; no automatic retry.'})
    result = {'status': 'failed', 'owner_sha256': file_hash(base/'owner.json'), 'terminal_sha256': file_hash(run_dir/'failed.json'),
              'cgroup_empty': True, 'cell_ledger_sha256': file_hash(base/'postmortem-cells.json'),
              'unsealed_journals': len(journals), 'financial_completion': False,
              'evidence_sha256': _observer_evidence(base)}
    _immutable(base/'observer.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('launch', 'monitor', 'worker', 'reconcile'), default='launch')
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--registration', required=True)
    parser.add_argument('--experiment', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--owner-pid', type=int)
    parser.add_argument('--nonce')
    args = parser.parse_args()
    result = globals()[args.mode](args)
    if isinstance(result, dict):
        print(json.dumps(result, sort_keys=True))
    elif result is not None:
        raise SystemExit(result)
