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
from ..lifecycle import ResearchRun, _immutable, _encode, metadata_scope, current_metadata_scope
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


def resource_policy(value, root, *, pilot_context=None):
    required = {'memory_max_bytes', 'memory_high_bytes', 'reserve_bytes', 'start_reserve_bytes',
                'disk_floor_bytes', 'disk_paths', 'wall_seconds'}
    if set(value) not in (required,required|{'storage_budget'},required|{'physical_policy'},required|{'storage_budget','native_unit_limits'}):
        raise ValueError('execution resource policy fields differ')
    for name in required-{'disk_paths'}:
        if type(value[name]) is not int or value[name] <= 0:
            raise ValueError('positive integer resource limits required')
    if not value['memory_high_bytes'] <= value['memory_max_bytes'] <= 6*resources.GIB:
        raise ValueError('execution memory ceiling differs')
    if value['reserve_bytes'] < 3*resources.GIB or value['start_reserve_bytes'] < value['memory_max_bytes']+value['reserve_bytes']:
        raise ValueError('execution host reserves below contract')
    if value['disk_floor_bytes'] < 10*resources.GIB or value['wall_seconds'] > 28800:
        raise ValueError('execution disk/wall limits differ')
    paths = value['disk_paths']
    if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)) or any(not isinstance(p, str) or not Path(p).is_absolute() for p in paths):
        raise ValueError('explicit unique guard volumes required')
    if root.stat().st_dev not in {Path(p).stat().st_dev for p in paths}:
        raise ValueError('guard omits artifact volume')
    if 'storage_budget' in value:
        from .workflow_storage import StorageWatch
        budget=value['storage_budget']
        if type(budget) is dict and budget.get('schema_version')==2:
            if pilot_context is None:raise ValueError('writable union requires explicit real-pilot selection')
            from ..admission import Admission
            from .real_pilot_import_caller import selected,_read,validate_plan
            ad,execution=pilot_context
            if not isinstance(ad,Admission) or ad.root!=Path(root) or not selected(execution) or execution['kind']!='compact_resource' or execution['resources']!=value:raise ValueError('original real-pilot admission context required')
            selected_plan=next(iter(execution['payload']['representation_jobs'].values()))
            plan=validate_plan(_read(ad,selected_plan['real_pilot_input']))
            if plan['schema_version']!=2 or plan['resource_policy']!=value:raise ValueError('authenticated schema2 policy required')
            from .real_pilot_storage import validate,EXPERIMENT
            if ad.experiment_id!=EXPERIMENT:raise ValueError('fixed real-pilot identity required')
            validate(budget,Path(root))
        else:
            if type(budget) is not dict or set(budget)!={'root','limits'} or type(budget['root']) is not str:
                raise ValueError('registered storage budget schema differs')
            watch=StorageWatch(budget['root'],budget['limits'])
            if not watch.root.is_relative_to(Path(root).resolve()):
                raise ValueError('registered storage root is outside the admitted workspace')
    if 'physical_policy' in value:
        from .neural_physical import validate
        validate(value['physical_policy'])
    if 'native_unit_limits' in value:resources._native_policy(value['native_unit_limits'])
    return value


def job_schema(job):
    if 'native_unit_limits' in job.get('resources',{}) and job.get('kind')!='compact_resource':
        raise ValueError('native-only file limits require compact_resource')
    if 'physical_policy' in job.get('resources',{}) and job.get('kind')!='neural_resource':
        raise ValueError('physical policy is restricted to explicit neural resource jobs')
    if set(job) != {'schema_version', 'kind', 'resources', 'environment_input', 'payload'} or job['schema_version'] != 1 or job['kind'] not in ('fit', 'ranges', 'prices', 'coinmetrics_prices', 'graphs', 'neighborhood_census', 'hub_edge_census', 'neural_resource', 'treatments', 'compact_resource'):
        raise ValueError('execution job schema/kind differs')
    if job['kind']=='compact_resource':
        from . import resource_fixture, real_pilot_import_caller
        route = real_pilot_import_caller if real_pilot_import_caller.selected(job) else resource_fixture
        route.schema(job)
    if job['kind'] in ('graphs','neighborhood_census','hub_edge_census','neural_resource','treatments') and (not isinstance(job['payload'], dict) or set(job['payload']) != {'plan_input'} or not isinstance(job['payload']['plan_input'], str) or not job['payload']['plan_input']):
        raise ValueError('graph/census job requires an explicit registered plan input')
    if job['kind'] in ('neighborhood_census','hub_edge_census') and (type(job['resources'].get('wall_seconds')) is not int or not 0<job['resources']['wall_seconds']<=540):
        raise ValueError('census whole-job wall limit must not exceed 540 seconds')
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
    resource_policy(job['resources'], admitted.root,pilot_context=(admitted,job))
    if job['kind']=='compact_resource':
        from . import resource_fixture, real_pilot_import_caller
        route = real_pilot_import_caller if real_pilot_import_caller.selected(job) else resource_fixture
        route.admitted(admitted,job)
    source = admitted.experiment['source_files']
    if not required_sources() <= set(source):
        raise ValueError('execution dependency source closure not registered')
    if Path(__file__).resolve() != (admitted.root/'tradingagents/research/onchain_replication/job.py').resolve():
        raise ValueError('execution imported from outside admitted source root')
    return admitted, job


def _base(args):
    return Path(args.root).resolve()/PREFIX/'runs'/args.experiment


def _command(args, mode):
    command=[sys.executable, '-B', '-m', MODULE, '--mode', mode, '--root', str(Path(args.root).resolve()),
            '--registration', args.registration, '--experiment', args.experiment, '--source', args.source]
    if getattr(args,'physical_anchor',None):command+=['--physical-anchor',args.physical_anchor]
    return command


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


def _physical_scope(args,job,*,create=False,launcher=None):
    policy=job['resources'].get('physical_policy')
    if policy is None:return None
    from .neural_physical import Scope
    if create:return Scope.create(args.root,args.experiment,args.source,policy,launcher)
    scope=Scope.open(args.root,args.experiment,args.source,policy,original_anchor=getattr(args,'physical_anchor',None))
    launch_record=scope.read_metadata(_base(args)/'launch.json')
    if scope.anchor['launcher']!={k:launch_record[k] for k in ('nonce','supervisor_pid')}:
        raise ValueError('physical original launcher differs')
    return scope



def _pilot_residual_tail(args,job):
    budget=job['resources'].get('storage_budget')
    if type(budget) is dict and budget.get('schema_version')==2:
        from .real_pilot_storage import validate,residual_check
        validate(budget,Path(args.root));return residual_check(Path(args.root))
    return None

def launch(args):
    _,job=_admitted(args)
    base = _base(args)
    durable_mkdir(base.parent)
    base.mkdir(exist_ok=False)
    sync_directory(base.parent)
    nonce = uuid.uuid4().hex
    scope=_physical_scope(args,job,create=True,launcher={'nonce':nonce,'supervisor_pid':os.getpid()})
    if scope is not None:args.physical_anchor=scope.anchor_hash
    primary=None
    try:
        with metadata_scope(scope):
            _pilot_residual_tail(args,job)
            _immutable(base/'launch.json', {'experiment': args.experiment, 'source_commit': args.source,
                                          'supervisor_pid': os.getpid(), 'nonce': nonce})
            budget=job['resources'].get('storage_budget')
            extra={}
            if type(budget) is dict and budget.get('schema_version')==2:
                from .real_pilot_storage import prepare_environment
                env=resources._native_owned_env(Path(args.root),budget);prepare_environment(Path(args.root),budget,env)
                extra['env']={**os.environ,**env}
            monitor = subprocess.Popen(_command(args, 'monitor')+['--owner-pid', str(os.getpid()), '--nonce', nonce], cwd=args.root,**extra)
            def stop(signum, frame):
                if monitor.poll() is None:
                    monitor.terminate()
            signal.signal(signal.SIGTERM, stop)
            signal.signal(signal.SIGINT, stop)
            monitor_exit=monitor.wait()
            result = reconcile(args)
            if scope is not None and monitor_exit!=0:
                result={'status':'monitor_failed','monitor_exit_code':monitor_exit,'reconciled_disposition':result}
                with scope.terminal_tail():_immutable(base/'monitor-failed.json',result)
            _pilot_residual_tail(args,job)
            print(json.dumps(result, sort_keys=True), flush=True)
            _pilot_residual_tail(args,job)
            return 0 if result['status'] == 'complete' else 1
    except BaseException as error:primary=error;raise
    finally:
        if scope is not None:
            try:scope.close_authority()
            except BaseException as error:
                if primary is not None:
                    primary.add_note('physical authority shutdown: '+repr(error))
                    if isinstance(primary,Exception) and not isinstance(primary,MemoryError) and (not isinstance(error,Exception) or isinstance(error,MemoryError)):raise error from primary
                else:raise


def _resource_worker_limits(job):
    from . import resource_fixture, real_pilot_import_caller
    if real_pilot_import_caller.selected(job):
        return real_pilot_import_caller.worker_limits(job)
    return resource_fixture.worker_limits()


def _resource_limit_receipt(args,job,role,live=None):
    if job['kind']!='compact_resource':raise ValueError('native receipt requires selected compact resource job')
    readback=_resource_worker_limits(job)
    expected=job['resources']['native_unit_limits']
    if expected!={'file_size_bytes':readback['rlimit_fsize']}:raise ValueError('registered process file limit differs')
    if role=='worker' and (live is None or live.get('native_unit_limits')!=expected):raise ValueError('worker native authority missing')
    value={'schema_version':1,'experiment':args.experiment,'source_commit':args.source,'role':role,'pid':os.getpid(),'file_size_limit':[readback['rlimit_fsize']]*2,'before_claim':True,'native_unit':None if live is None else live['unit'],'native_cgroup':None if live is None else live['cgroup']}
    value['native_environment']={key:os.environ.get(key) for key in resources._native_owned_env(Path(args.root),job['resources'].get('storage_budget'))}
    if value['native_environment']!=resources._native_owned_env(Path(args.root),job['resources'].get('storage_budget')):raise ValueError('actual process environment differs from owned routing')
    resources._native_receipt(_base(args),role+'-file-limit.json',value)



def monitor(args):
    resources.bind_parent_death(args.owner_pid)
    _, job = _admitted(args)
    if job['kind']=='compact_resource':_resource_limit_receipt(args,job,'monitor')
    scope=_physical_scope(args,job)
    with metadata_scope(scope):
        base = _base(args)
        launch_record = json.loads((base/'launch.json').read_bytes())
        if launch_record != {'experiment': args.experiment, 'source_commit': args.source,
                             'supervisor_pid': args.owner_pid, 'nonce': args.nonce}:
            raise ValueError('execution supervisor identity differs')
        _pilot_residual_tail(args,job)
        owner = {**launch_record, 'monitor_pid': os.getpid(),
                 'monitor_start_ticks': Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]}
        _immutable(base/'owner.json', owner)
        if 'native_unit_limits' in job['resources']:
            guard_policy={k:v for k,v in job['resources'].items() if k!='native_unit_limits'}
            result = resources.guarded_run(_command(args, 'worker'), cwd=args.root, receipt_dir=base/'guard',
                memory_swap_max_bytes=0, owner_identity=owner, native_unit_limits=job['resources']['native_unit_limits'], **guard_policy)
        else:
            result = resources.guarded_run(_command(args, 'worker'), cwd=args.root, receipt_dir=base/'guard',
                memory_swap_max_bytes=0, owner_identity=owner, **job['resources'])
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if scope is not None:scope.tail=True
        observed = reconcile(args)
        if scope is not None:
            physical=scope.finish()
            print(json.dumps({'physical_final_accounting':physical},sort_keys=True),flush=True)
        _pilot_residual_tail(args,job)
        return 0 if result['phase'] == 'complete' and observed['status'] == 'complete' else 1


def execute_source_job(run, kind, payload):
    if kind == 'graphs':
        from .graph_production import produce_registered_graphs
        cells, summary, directory = produce_registered_graphs(run, payload['plan_input'])
    elif kind == 'treatments':
        from .treatment_production import produce_registered_treatments
        cells, summary, directory = produce_registered_treatments(run, payload['plan_input'])
    elif kind == 'hub_edge_census':
        from .hub_census_production import produce_registered_hub_census
        cells, summary, directory = produce_registered_hub_census(run, payload['plan_input'])
    elif kind == 'neighborhood_census':
        from .census_production import produce_registered_census
        cells, summary, directory = produce_registered_census(run, payload['plan_input'])
    elif kind == 'ranges':
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
    if kind in ('neighborhood_census','hub_edge_census'):
        from .census_production import finalize_registered_storage
        finalize_registered_storage(run,directory,payload['plan_input'])
    return cells


def worker(args):
    admitted, job = _admitted(args)
    if job['kind']=='compact_resource':
        _resource_worker_limits(job)
    scope=_physical_scope(args,job)
    if scope is not None:scope.verify_environment()
    with metadata_scope(scope):
        root, base = admitted.root, _base(args)
        policy = job['resources']
        live = resources.assert_guarded_worker(base/'guard', _command(args, 'worker'),
            required_paths=[Path(p) for p in policy['disk_paths']], wall_seconds=policy['wall_seconds'],
            memory_max_bytes=policy['memory_max_bytes'], memory_high_bytes=policy['memory_high_bytes'],
            disk_floor_bytes=policy['disk_floor_bytes'])
        owner = json.loads((base/'owner.json').read_bytes())
        if live['owner_identity'] != owner or owner['experiment'] != args.experiment or owner['source_commit'] != args.source:
            raise ValueError('execution worker ownership differs')
        if any(live[k] != v for k, v in policy.items()):
            raise ValueError('execution guard policy differs from registration')
        if job['kind']=='compact_resource':_resource_limit_receipt(args,job,'worker',live)
        def stop(signum, frame):
            raise SystemExit('owned execution interrupted; never relaunch this identity')
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        with ResearchRun.start(root=root, registration=args.registration, experiment=args.experiment, source=args.source) as run:
            from .environment import inventory
            if inventory(root, include_torch=job['kind'] in ('fit','neural_resource','compact_resource')) != json.loads(run.read_input(job['environment_input'])):
                raise ValueError('registered execution environment differs')
            if job['kind'] == 'neural_resource':
                from .neural_resource import produce_registered_neural_resource, finalize_storage
                cells, summary, directory = produce_registered_neural_resource(run, job['payload']['plan_input'])
                run.write_json('cell-ledger.json', cells)
                run.write_json('resource-summary.json', summary)
                run.write_json('artifact-index.json', {str(p.relative_to(root)): {'sha256': file_hash(p), 'bytes': p.stat().st_size}
                    for p in directory.rglob('*') if p.is_file()})
                finalize_storage(run, directory, job['payload']['plan_input'])
            elif job['kind']=='compact_resource':
                from . import resource_fixture, real_pilot_import_caller
                route = real_pilot_import_caller if real_pilot_import_caller.selected(job) else resource_fixture
                cells=route.execute(run,job['payload'])
            elif job['kind'] in ('ranges', 'prices', 'coinmetrics_prices', 'graphs', 'neighborhood_census', 'hub_edge_census', 'treatments'):
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
                if job['kind']=='neural_resource':raise RuntimeError('neural resource job failed; no retry')
            else:
                run.finish(cells)


def _incomplete_representation(directory,root):
    """Record missing construction metadata after worker death; never infer owner."""
    import stat
    names=('owner.json','start.json','claim.json')
    if all((directory/name).exists() for name in names):return None
    if directory.resolve()!=directory or not directory.is_dir() or directory.stat().st_dev!=root.stat().st_dev:
        raise ValueError('incomplete representation path/device differs')
    present={};missing=[]
    for name in names:
        path=directory/name
        if not path.exists() and not path.is_symlink():missing.append(name);continue
        info=path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_dev!=root.stat().st_dev or info.st_size>65536:
            raise ValueError('incomplete representation metadata type/extent differs')
        present[name]=file_hash(path)
    return {'directory':str(directory),'status':'incomplete_construction_requires_review',
            'missing_metadata':missing,'retained_metadata_sha256':present,
            'owner_verified':False,'automatic_reuse_allowed':False}


def reconcile(args):
    if current_metadata_scope() is not None:return _reconcile(args)
    if getattr(args,'physical_anchor',None) or os.path.lexists(_base(args)/'physical-anchor.json'):
        raise ValueError('physical external reconciliation lacks original live parent scope; no disk authority fallback')
    return _reconcile(args)


def _reconcile(args):
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
    # Preserve authenticated treatment rows after a later worker failure.
    from .treatment_production import recover_treatment_rows
    treatment_rows = recover_treatment_rows(root, args.experiment, args.source,
        file_hash(claim_path), claim['experiment']['cells'], claim['inputs'],
        claim['experiment']['source_files'])
    if set(treatment_rows) & set(recorded):
        raise ValueError('duplicate durable treatment disposition')
    recorded.update(treatment_rows)
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
        incomplete = _incomplete_representation(directory, root)
        if incomplete is not None:
            journals.append(incomplete)
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
    parser.add_argument('--physical-anchor')
    args = parser.parse_args()
    result = globals()[args.mode](args)
    if isinstance(result, dict):
        print(json.dumps(result, sort_keys=True))
    elif result is not None:
        raise SystemExit(result)
