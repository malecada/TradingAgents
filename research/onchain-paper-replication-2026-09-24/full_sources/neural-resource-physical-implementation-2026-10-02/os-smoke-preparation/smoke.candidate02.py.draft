"""NONEXECUTABLE preparation until a separately reviewed finalized spec exists.

Direct engineering exercise of the actual selected Scope/guard APIs. No neural
runner, ResearchRun, data arrays, financial registration or historical identity.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import uuid


def terminal_primary(failures):
    """Keep the first fatal, promoting it over an earlier ordinary failure."""
    primary = None
    for error in failures:
        if primary is None:
            primary = error
        elif error is not primary:
            if isinstance(primary, Exception) and not isinstance(primary, MemoryError) and (
                    not isinstance(error, Exception) or isinstance(error, MemoryError)):
                error.__cause__ = primary
                primary = error
            else:
                primary.add_note('additional terminal failure: ' + repr(error))
    return primary


def terminal_publications(scope, immutable, disposition):
    failures = []
    try:
        if scope.check(tail=True)['claim_sha256'] is not None:
            immutable(scope.roots['lifecycle']/'failed.json', disposition)
    except BaseException as error:
        failures.append(error)
    try:
        immutable(scope.base/'observer.json', disposition)
    except BaseException as error:
        failures.append(error)
    try:
        scope.finish()
    except BaseException as error:
        failures.append(error)
    if failures:
        raise terminal_primary(failures)


def checked_spec(path,expected):
    data=path.read_bytes()
    if len(data)>65536 or hashlib.sha256(data).hexdigest()!=expected:raise ValueError('exact reviewed smoke spec differs')
    spec=json.loads(data)
    if spec['status']!='reviewed_for_single_engineering_execution':raise ValueError('preparation only; smoke execution is not enabled')
    root=Path(spec['isolated_root']).resolve(strict=True)
    if root!=Path(spec['isolated_root']) or spec['source_commit'] is None or spec['source_files'] is None:
        raise ValueError('reviewed isolated source identity missing')
    if spec['experiment']!='synthetic-neural-physical-os-20261002-01':raise ValueError('fresh engineering identity differs')
    actual={str(p.relative_to(root)) for p in (root/'tradingagents/research/onchain_replication').glob('*.py')}
    actual|={str(p.relative_to(root)) for p in (root/'tradingagents/research').glob('*.py')}
    actual.add('tradingagents/__init__.py')
    if actual!=set(spec['source_files']):raise ValueError('complete source closure differs')
    for name,sha in spec['source_files'].items():
        candidate=root/name
        if candidate.resolve()!=candidate or candidate.stat().st_size>10*1024**2:raise ValueError('source path/type/extent differs')
        if hashlib.sha256(candidate.read_bytes()).hexdigest()!=sha:raise ValueError('frozen source bytes differ: '+name)
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=spec['driver_sha256']:raise ValueError('driver bytes differ')
    sys.path.insert(0,str(root))
    return spec,root


def worker(spec,root,command,anchor):
    from tradingagents.research.lifecycle import metadata_scope,_immutable
    from tradingagents.research.onchain_replication.neural_physical import Scope
    from tradingagents.research.onchain_replication import resources
    scope=Scope.open(root,spec['experiment'],spec['source_commit'],spec['physical_policy'],original_anchor=anchor)
    scope.verify_environment()
    guard=scope.base/'guard';limits=spec['guard']
    live=resources.assert_guarded_worker(guard,command,required_paths=[root],
        wall_seconds=limits['wall_seconds'],memory_max_bytes=limits['memory_max_bytes'],
        memory_high_bytes=limits['memory_high_bytes'],disk_floor_bytes=limits['disk_floor_bytes'])
    with metadata_scope(scope):
        life=scope.birth('lifecycle')
        _immutable(life/'claim.json',{'experiment_id':spec['experiment'],'source':spec['source_commit'],
            'classification':'engineering fixture only; NOT a ResearchRun or empirical claim'})
        output=scope.birth('producer')
        with (output/'invented.bin').open('xb') as stream:
            stream.write(bytes(8192));stream.flush();os.fsync(stream.fileno())
        _immutable(output/'before-log-probe.json',{'bytes':8192,'cpu_affinity':sorted(os.sched_getaffinity(0)),
            'file_size_limit':list(resource.getrlimit(resource.RLIMIT_FSIZE)),
            'cgroup':live['cgroup'],'scope_claim_sha256':scope.check()['claim_sha256'],
            'scratch_mapping':scope.environment(),'purpose':'fixed artificial bytes only'})
        # Exactly17 calls of at most4096 bytes; no unbounded output loop.
        signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
        sent=0;failure=None
        for _ in range(17):
            try:sent+=os.write(1,b'X'*4096)
            except OSError as error:
                failure={'type':type(error).__name__,'errno':error.errno};break
        # This may be absent if the guard wins the expected containment race.
        _immutable(output/'after-log-probe.json',{'sent_bytes':sent,'error':failure,'attempted_max_bytes':69632})
    return 77  # Intended engineering failure; never financial completion.


def controller(spec,root,args):
    from tradingagents.research.lifecycle import metadata_scope,_immutable
    from tradingagents.research.onchain_replication.neural_physical import Scope,PREFIX
    from tradingagents.research.onchain_replication.neural_authority import process_start
    from tradingagents.research.onchain_replication import resources
    experiment=spec['experiment'];base=root/PREFIX/'runs'/experiment
    paths=[base,root/'research_runs'/experiment,root/PREFIX/'sources'/experiment]
    if any(os.path.lexists(p) for p in paths):raise ValueError('smoke identity already reserved; no retry')
    for path in paths:
        if not path.parent.is_dir() or path.parent.resolve()!=path.parent:raise ValueError('canonical parent scaffold missing')
    if len(os.sched_getaffinity(0))<2:raise ValueError('two CPUs unavailable')
    if resources.mem_available()<spec['guard']['start_reserve_bytes']:raise ValueError('startup memory unavailable; no reservation')
    if __import__('shutil').disk_usage(root).free<spec['guard']['disk_floor_bytes']:raise ValueError('disk floor unavailable; no reservation')
    base.mkdir(exist_ok=False)
    launcher={'nonce':uuid.uuid4().hex,'supervisor_pid':os.getpid()}
    scope=Scope.create(root,experiment,spec['source_commit'],spec['physical_policy'],launcher)
    primary=None
    try:
        command=[sys.executable,'-B',str(Path(__file__).resolve()),'--spec',str(args.spec.resolve()),
                 '--spec-sha256',args.spec_sha256,'--worker','--anchor',scope.anchor_hash]
        with metadata_scope(scope):
            owner={'experiment':experiment,'source_commit':spec['source_commit'],**launcher,
                   'monitor_pid':os.getpid(),'monitor_start_ticks':process_start(os.getpid())}
            _immutable(base/'launch.json',{'classification':'engineering only',**owner})
            _immutable(base/'owner.json',owner)
            result=resources.guarded_run(command,cwd=root,receipt_dir=base/'guard',
                owner_identity=owner,disk_paths=[root],physical_policy=spec['physical_policy'],**spec['guard'])
            scope.tail=True
            log=base/'guard/child.log'
            expected=(result.get('phase')=='failed' and result.get('cleanup_verified') is True
                and result.get('child_log_limit_reached') is True and log.is_file()
                and log.stat().st_size==spec['physical_policy']['max_file_bytes'])
            disposition={'classification':'engineering-only expected log-cap failure','status':'failed',
                         'expected_containment_observed':expected,'guard_phase':result.get('phase'),
                         'cleanup_verified':result.get('cleanup_verified'),'automatic_retry':False}
            # Independent best-effort terminal publications. Preserve fatal priority.
            terminal_publications(scope, _immutable, disposition)
            return 0 if expected else 1
    except BaseException as error:primary=error;raise
    finally:
        try:scope.close_authority()
        except BaseException as error:
            if primary is None:raise
            primary.add_note('authority shutdown: '+repr(error))
            if isinstance(primary,Exception) and not isinstance(primary,MemoryError) and (not isinstance(error,Exception) or isinstance(error,MemoryError)):raise error from primary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--spec-sha256',required=True);parser.add_argument('--worker',action='store_true');parser.add_argument('--anchor')
    args=parser.parse_args();spec,root=checked_spec(args.spec,args.spec_sha256)
    command=[sys.executable,'-B',str(Path(__file__).resolve()),'--spec',str(args.spec.resolve()),
             '--spec-sha256',args.spec_sha256,'--worker','--anchor',args.anchor] if args.worker else None
    raise SystemExit(worker(spec,root,command,args.anchor) if args.worker else controller(spec,root,args))
