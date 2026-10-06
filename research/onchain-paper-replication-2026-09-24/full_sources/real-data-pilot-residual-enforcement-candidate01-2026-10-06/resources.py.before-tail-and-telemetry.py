"""Fail-closed local user-unit memory containment; no empirical logic.

Each invocation owns a new receipt directory and unit. A gated child cannot
start the requested command until kernel memory controls have been read back.
The child lease makes loss of the external monitor terminal, not an orphan run.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time
import uuid

GIB = 1024 ** 3


def mem_available(path=Path('/proc/meminfo')):
    for line in path.read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) * 1024
    raise RuntimeError('MemAvailable is unavailable')


def _atomic(path, value):
    lifecycle=sys.modules.get('tradingagents.research.lifecycle')
    scope=None if lifecycle is None else lifecycle.current_metadata_scope()
    if scope is not None:return scope.atomic(path,value)
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def _systemctl(*args, check=True):
    return subprocess.run(['systemctl', '--user', *args], check=check,
                          capture_output=True, text=True, timeout=10)


def _properties(unit):
    result = _systemctl('show', unit, '--property=ControlGroup,ActiveState,SubState,ExecMainStatus,Result')
    return dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)


def _read_controls(cgroup):
    return {key: (cgroup / key).read_text().strip()
            for key in ('memory.max', 'memory.high', 'memory.swap.max')}


def _verify_controls(actual, maximum, high, swap):
    expected = {'memory.max': str(maximum), 'memory.high': str(high), 'memory.swap.max': str(swap)}
    if actual != expected:
        raise RuntimeError(f'kernel memory controls differ: {actual!r}, expected {expected!r}')


def _snapshot(cgroup):
    events = dict(line.split() for line in (cgroup / 'memory.events').read_text().splitlines())
    if not {'oom', 'oom_kill'} <= events.keys():
        raise RuntimeError('kernel OOM event counters unavailable')
    return {'memory_current_bytes': int((cgroup / 'memory.current').read_text()),
            'memory_events': {key: int(value) for key, value in events.items()},
            'optional_memory_telemetry': _telemetry(cgroup)}


def _telemetry(cgroup):
    """Best-effort observations only; never alter admission or pressure policy."""
    def one(path):
        value = {'path': str(path), 'pressure': None, 'anon_bytes': None,
                 'file_bytes': None, 'swap_current_bytes': None,
                 'kernel_peak_bytes': None, 'unavailable': {}}
        try:
            peak = int((path / 'memory.peak').read_text())
            if peak < 0:
                raise ValueError('negative kernel memory peak')
            value['kernel_peak_bytes'] = peak
        except (OSError, ValueError) as exc:
            value['unavailable']['kernel_peak_bytes'] = type(exc).__name__
        try:
            value['pressure'] = (path / 'memory.pressure').read_text().strip()
        except OSError as exc:
            value['unavailable']['pressure'] = type(exc).__name__
        try:
            stats = dict(line.split() for line in (path / 'memory.stat').read_text().splitlines())
            value['anon_bytes'], value['file_bytes'] = int(stats['anon']), int(stats['file'])
        except (OSError, ValueError, KeyError) as exc:
            value['unavailable']['memory_stat'] = type(exc).__name__
        try:
            value['swap_current_bytes'] = int((path / 'memory.swap.current').read_text())
        except (OSError, ValueError) as exc:
            value['unavailable']['swap_current_bytes'] = type(exc).__name__
        return value
    ancestor = next((p for p in cgroup.parents
                     if p.name.startswith('user@') and p.name.endswith('.service')), None)
    return {'unit': one(cgroup), 'user_ancestor': one(ancestor) if ancestor else None,
            'qualification': 'Optional last observations; unavailable is unknown, not zero. '
                             'Kernel peak is the last memory.peak readback for that cgroup lifetime, '
                             'including charged file cache; the ancestor is not workload-only. '
                             'A last read before abrupt termination need not be the final lifetime peak. '
                             'No PSI policy change.'}


def _own_cgroup():
    for line in Path('/proc/self/cgroup').read_text().splitlines():
        if line.startswith('0::/'):
            return Path('/sys/fs/cgroup') / line[3:].lstrip('/')
    raise RuntimeError('unified child cgroup unavailable')


def _terminal_snapshot(value):
    snapshot = value.get('terminal_memory_snapshot')
    if not isinstance(snapshot, dict):
        raise RuntimeError('terminal child memory snapshot unavailable')
    events = snapshot.get('memory_events', {})
    if any(type(events.get(key)) is not int or events[key] < 0 for key in ('oom', 'oom_kill')):
        raise RuntimeError('terminal child OOM counters unavailable')
    if type(snapshot.get('memory_current_bytes')) is not int or snapshot['memory_current_bytes'] < 0:
        raise RuntimeError('terminal child memory accounting unavailable')
    return snapshot


def verify_cpu_tree(cgroup,cpus):
    allowed=set(cpus)
    if len(allowed)!=2:raise RuntimeError('exactly two CPU IDs required')
    observed={}
    for procs in [cgroup/'cgroup.procs',*cgroup.rglob('cgroup.procs')]:
        try:pids=procs.read_text().split()
        except FileNotFoundError:continue
        for pid in pids:
            try:threads=list((Path('/proc')/pid/'task').iterdir())
            except (FileNotFoundError,ProcessLookupError):continue
            for thread in threads:
                try:mask=set(os.sched_getaffinity(int(thread.name)))
                except ProcessLookupError:continue
                if not mask or not mask<=allowed:raise RuntimeError('thread widened CPU affinity beyond registered two CPUs')
                observed[thread.name]=sorted(mask)
    return observed


def _native_receipt(directory,name,value):
    # Pure metadata only: usable by monitor before any numerical import.
    from tradingagents.research.onchain_replication.owned_io import _cleanup
    import stat
    raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
    if len(raw)>65536 or '/' in name or name in ('','.','..'):raise ValueError('bounded native receipt required')
    directory=Path(directory);parent=fd=None
    try:
        if directory.resolve()!=directory:raise ValueError('native receipt parent redirected')
        parent=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        original=os.fstat(parent)
        fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
        opened=os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink!=1:raise ValueError('native receipt file differs')
        offset=0
        while offset<len(raw):
            wrote=os.write(fd,raw[offset:])
            if wrote<=0:raise OSError('native receipt short write')
            offset+=wrote
        os.fsync(fd);os.fsync(parent)
        now=directory.stat();child=os.stat(name,dir_fd=parent,follow_symlinks=False)
        if directory.resolve()!=directory or (now.st_dev,now.st_ino)!=(original.st_dev,original.st_ino) or (child.st_dev,child.st_ino,child.st_nlink,child.st_size)!=(opened.st_dev,opened.st_ino,1,len(raw)):raise ValueError('native receipt path changed')
    finally:
        _cleanup(tuple((lambda descriptor=descriptor:os.close(descriptor)) for descriptor in (fd,parent) if descriptor is not None))


def _native_policy(value):
    if value is None:return None
    if type(value) is not dict or set(value)!={'file_size_bytes'} or type(value['file_size_bytes']) is not int or not 0<value['file_size_bytes']<2**63:
        raise ValueError('native unit file limit schema differs')
    return dict(value)


def _native_owned_env(cwd,storage_budget=None):
    root=Path(cwd);base=root/'fixture_runtime'
    result={'PYTHONPATH':str(root),'TMPDIR':str(base/'tmp'),'XDG_CACHE_HOME':str(base/'cache'),'TORCH_HOME':str(base/'torch'),'MPLCONFIGDIR':str(base/'matplotlib'),'HF_HOME':str(base/'hf'),'TORCH_EXTENSIONS_DIR':str(base/'torch-extensions'),'PYTHONDONTWRITEBYTECODE':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','OPENBLAS_NUM_THREADS':'2','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','NUMEXPR_NUM_THREADS':'2'}
    if storage_budget is not None and storage_budget.get('schema_version')==2:
        from tradingagents.research.onchain_replication.real_pilot_storage import validate,environment
        validate(storage_budget,root);return environment(root,result)
    return result


def _native_seconds(text):
    factors={'us':0.000001,'ms':0.001,'s':1,'min':60,'h':3600}
    total=0
    for part in text.split():
        unit=next((u for u in factors if part.endswith(u) and part[:-len(u)].isdigit()),None)
        if unit is None:raise ValueError('unsupported native duration readback')
        total+=int(part[:-len(unit)])*factors[unit]
    if not text or total<=0:raise ValueError('missing native duration readback')
    return total


def _native_ready(policy,ready,properties,wall_seconds,cwd,storage_budget=None):
    policy=_native_policy(policy);expected=policy['file_size_bytes']
    if ready.get('native_environment')!=_native_owned_env(cwd,storage_budget):raise ValueError('native child environment differs')
    limits=ready.get('file_size_limit')
    if ready.get('native_unit_limits')!=policy or type(limits) is not list or len(limits)!=2 or any(type(v) is not int or v!=expected for v in limits):
        raise ValueError('native child file limit readback differs')
    if any(properties.get(k)!=str(expected) for k in ('LimitFSIZE','LimitFSIZESoft')):
        raise ValueError('native unit file limit readback differs')
    if _native_seconds(properties.get('RuntimeMaxUSec',''))!=wall_seconds:raise ValueError('native unit wall readback differs')


def _child(receipt,cpus,lease_seconds,command,physical=False,physical_context=None,native_unit_limits=None):
    native_unit_limits=_native_policy(native_unit_limits)
    if physical and native_unit_limits is not None:raise ValueError('physical and native-only limits cannot be combined')
    if not physical:
        if native_unit_limits is None:return _child_legacy(receipt,cpus,lease_seconds,command)
        return _child_legacy(receipt,cpus,lease_seconds,command,native_unit_limits=native_unit_limits)
    from tradingagents.research.lifecycle import metadata_scope
    from tradingagents.research.onchain_replication.neural_physical import Scope,verify_file_limit
    import resource
    if not isinstance(physical_context,str) or len(physical_context)>8192:raise ValueError('physical original child context missing/bounded extent differs')
    context=json.loads(physical_context);policy=context['policy']
    scope=Scope.open(Path.cwd(),context['experiment'],context['source'],policy,original_anchor=context['anchor'])
    scope.verify_environment()
    live=scope.read_metadata(receipt/'live.json')
    if live['physical_policy']!=policy:raise ValueError('physical child policy differs from original context')
    verify_file_limit(policy['max_file_bytes'],resource.getrlimit(resource.RLIMIT_FSIZE))
    with metadata_scope(scope):return _child_legacy(receipt,cpus,lease_seconds,command)


def _child_legacy(receipt, cpus, lease_seconds, command, native_unit_limits=None):
    """Main process writes its terminal before systemd kills surviving descendants."""
    stopping=False;code=125;reason='not released';process=None
    lease_rejection=None
    def stop(signum,frame):
        nonlocal stopping
        stopping=True
    def fresh():
        nonlocal lease_rejection
        sampled=timestamp=age=None
        phase='read_or_decode'
        try:
            lease=json.loads((receipt/'live.json').read_text())
            phase='sample_clock';sampled=time.monotonic()
            phase='timestamp_key';timestamp=lease['monotonic_seconds']
            phase='age_predicate';age=sampled-timestamp
            accepted=0<=age<=lease_seconds
            if accepted:return True
            category=('negative_age' if age<0 else
                      'expired_age' if age>lease_seconds else 'unordered_age')
            error=None
        except (OSError,ValueError,KeyError) as caught:
            category=('read_error' if isinstance(caught,OSError) else
                      'missing_timestamp' if isinstance(caught,KeyError) else 'value_error')
            error={'type':type(caught).__name__,
                   'errno':caught.errno if isinstance(caught,OSError) else None}
        # Only actual rejection adds evidence; no second clock/read or new retry.
        # Nonfinite/unavailable values stay null, never fabricated timestamps.
        def observed(value):
            return value if type(value) in (int,float) and -float('inf')<value<float('inf') else None
        lease_rejection={'schema_version':1,'category':category,'phase':phase,
                         'sampled_monotonic_seconds':observed(sampled),
                         'parsed_monotonic_seconds':observed(timestamp),
                         'observed_age_seconds':observed(age),
                         'lease_seconds':lease_seconds,'read_or_value_error':error}
        return False
    try:
        os.sched_setaffinity(0,set(cpus))
        ready={'pid':os.getpid(),'cpus':sorted(os.sched_getaffinity(0))}
        lifecycle=sys.modules.get('tradingagents.research.lifecycle')
        scope=None if lifecycle is None else lifecycle.current_metadata_scope()
        if scope is not None or native_unit_limits is not None:
            import resource
            ready['file_size_limit']=list(resource.getrlimit(resource.RLIMIT_FSIZE))
        if native_unit_limits is not None:
            expected=_native_policy(native_unit_limits)['file_size_bytes']
            if ready['file_size_limit']!=[expected,expected]:raise ValueError('inherited native file limit differs')
            ready['native_unit_limits']=dict(native_unit_limits)
            budget=json.loads((receipt/'live.json').read_text()).get('storage_budget')
            ready['native_environment']={key:os.environ.get(key) for key in _native_owned_env(Path.cwd(),budget)}
            if ready['native_environment']!=_native_owned_env(Path.cwd(),budget):raise ValueError('inherited native environment differs')
        _atomic(receipt/'cpu_ready.json',ready)
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
        while not stopping:
            if not fresh():reason='monitor lease lost before release';return code
            if (receipt/'release.json').exists():break
            time.sleep(.1)
        if stopping:reason='signal before release';return code
        env=dict(os.environ,PYTHONPATH=str(Path.cwd()),OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2')
        process=subprocess.Popen(command,env=env,start_new_session=True)
        while process.poll() is None:
            if stopping or not fresh():
                reason='signal' if stopping else 'monitor lease lost during workload'
                return code
            time.sleep(.1)
        code=process.returncode;reason='workload exited'
        return code if 0<=code<=255 else 1
    except BaseException as error:
        reason=type(error).__name__+': '+str(error)
        return code
    finally:
        try:snapshot=_snapshot(_own_cgroup());snapshot_error=None
        except Exception as error:snapshot=None;snapshot_error=repr(error)
        _atomic(receipt/'child_exit.json',{'exit_code':code,'reason':reason,'workload_pid':None if process is None else process.pid,'terminal_memory_snapshot':snapshot,'snapshot_error':snapshot_error,**({'lease_rejection':lease_rejection} if lease_rejection is not None else {})})


def _native_select(primary,later,io):
    """First actual fatal precedes synthetic cleanup uncertainty and ordinary errors."""
    if primary is not None and io._fatal(primary):return primary
    try:
        causes=io._flatten(tuple(e for e in (primary,later) if e is not None))
        actual=next((e for e in causes if io._fatal(e)),None)
        if actual is not None:return actual
        if isinstance(primary,io.CleanupFailure):return primary
        if isinstance(later,io.CleanupFailure):return later
        return primary if primary is not None else later
    except BaseException as selection_error:
        if later is not None and io._fatal(later):return later
        return selection_error


def _native_reason(state,error,io):
    # Store the original before any diagnostic formatting or attachment.
    selected=error
    try:
        state['phase']='failed'
        state['limit_reason']=state.get('limit_reason') or 'selected native guard failed; see raised exception'
        text=type(error).__name__+': '+str(error)
        if state['limit_reason']=='selected native guard failed; see raised exception':state['limit_reason']=text
    except BaseException as diagnostic:selected=_native_select(selected,diagnostic,io)
    return selected


def _native_finalize(state,primary,actions,io):
    """Attempt every independent action once; retain the original actual fatal."""
    failed=False
    for name,action in actions:
        try:
            state['phase']='complete' if primary is None and state.get('limit_reason') is None else 'failed'
            action()
        except BaseException as error:
            failed=True
            primary=_native_select(primary,error,io)
            primary=_native_select(primary,_native_reason(state,error,io),io)
    if primary is not None:state['phase']='failed'
    return primary,failed


def _native_write(path, state, io, *, max_bytes=None):
    if max_bytes is None:
        with io._opened(path,'xb') as stream:
            raw=json.dumps(state,indent=2,sort_keys=True).encode()+b'\n'
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        return
    if type(max_bytes) is not int or not 0 < max_bytes < 2**63:
        raise ValueError('explicit admitted native receipt byte limit required')
    raw=bytearray()
    for part in json.JSONEncoder(indent=2,sort_keys=True).iterencode(state):
        encoded=part.encode()
        if len(encoded)>max_bytes-len(raw)-1:
            raise ValueError('native receipt encoded byte limit exceeded; state not published')
        raw.extend(encoded)
    raw.extend(b'\n')
    with io._opened(path,'xb') as stream:
        count=stream.write(raw)
        if count!=len(raw):
            raise OSError('native receipt short write; partial retained')
        stream.flush();os.fsync(stream.fileno())


def _native_sync(path,io):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:io._cleanup((lambda:os.close(fd),))


def _native_atomic(path,state,io,*,max_bytes=None):
    temporary=path.with_suffix('.tmp')
    _native_write(temporary,state,io,max_bytes=max_bytes)
    temporary.replace(path)
    _native_sync(path.parent,io)


def guarded_run(command, *, cwd, receipt_dir, memory_max_bytes=6 * GIB,
                memory_high_bytes=5 * GIB, memory_swap_max_bytes=0, reserve_bytes=3 * GIB,
                start_reserve_bytes=None, sample_seconds=.25,
                lease_seconds=15., wait_seconds=30., disk_paths=(), disk_floor_bytes=20*GIB, wall_seconds=28800., owner_identity=None, storage_budget=None, physical_policy=None, native_unit_limits=None):
    """Run one command, or fail closed; return a durable resource receipt.

    No retry occurs. Startup waits at most wait_seconds for MemAvailable >=
    start_reserve_bytes (default cap + reserve). Runtime reserve pressure kills
    the entire unit. No elapsed workload limit is imposed. Existing receipt
    directories are rejected; live state is atomically replaced within this new
    invocation only. final.json is exclusive. CPU affinity is inherited by all
    ordinary children; malicious workload code is outside this guard's scope.
    """
    native_unit_limits=_native_policy(native_unit_limits)
    if native_unit_limits is not None and physical_policy is not None:raise ValueError('conflicting file-limit authorities')
    if not command or not all(isinstance(item, str) and item for item in command):
        raise ValueError('command must be a nonempty string argument list')
    if not 0 < memory_high_bytes <= memory_max_bytes <= 8 * GIB:
        raise ValueError('require 0 < memory.high <= memory.max <= 8GiB')
    if not 0 <= memory_swap_max_bytes <= GIB // 2:
        raise ValueError('require 0 <= memory.swap.max <= 512MiB')
    if reserve_bytes <= 0 or not 0 < sample_seconds <= 1 or lease_seconds < 5 or wait_seconds < 0:
        raise ValueError('invalid reserve, sampling, lease or waiting bound')
    if start_reserve_bytes is None:
        start_reserve_bytes = memory_max_bytes + reserve_bytes
    if start_reserve_bytes < memory_max_bytes + reserve_bytes:
        raise ValueError('startup reserve must cover memory.max plus host reserve')
    if wall_seconds<=0 or disk_floor_bytes<0:raise ValueError('invalid wall/disk limits')
    from tradingagents.research.lifecycle import current_metadata_scope
    physical_scope=current_metadata_scope()
    if physical_scope is not None and physical_policy is None:raise ValueError('cannot disable selected physical scope')
    if physical_policy is not None:
        from tradingagents.research.onchain_replication.neural_physical import validate
        validate(physical_policy)
        if storage_budget is not None or physical_scope is None or physical_scope.policy!=physical_policy:
            raise ValueError('selected physical scope required; legacy storage watcher cannot be combined')
        if not isinstance(owner_identity,dict) or owner_identity.get('experiment')!=physical_scope.anchor['experiment'] or owner_identity.get('source_commit')!=physical_scope.anchor['source']:
            raise ValueError('physical guard original owner differs')
    storage_watch=None
    if storage_budget is not None:
        from .workflow_storage import StorageWatch
        if type(storage_budget) is dict and storage_budget.get('schema_version')==2:
            from tradingagents.research.onchain_replication.real_pilot_storage import WritableUnion,EXPERIMENT
            if native_unit_limits is None or not isinstance(owner_identity,dict) or owner_identity.get('experiment')!=EXPERIMENT:raise ValueError('union requires fixed real-pilot native owner')
            storage_watch=WritableUnion(storage_budget,Path(cwd))
        else:
            if type(storage_budget) is not dict or set(storage_budget)!={'root','limits'}:
                raise ValueError('storage budget schema differs')
            storage_watch=StorageWatch(storage_budget['root'],storage_budget['limits'])
    native_metadata_bytes=getattr(storage_watch,'native_metadata_bytes',None)
    disk_paths=tuple(Path(p).resolve(strict=True) for p in disk_paths)
    cwd = Path(cwd).resolve(strict=True)
    receipt = Path(receipt_dir).absolute()
    receipt.mkdir(parents=True, exist_ok=False)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    unit = f'onchain-replication-{uuid.uuid4().hex}.service'
    begin = time.monotonic()
    state = {'unit': unit, 'receipt_dir': str(receipt), 'command': command,
             'cwd': str(cwd), 'monitor_pid': os.getpid(), 'cpus': cpus,'owner_identity':owner_identity,
             'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
             'memory_max_bytes': memory_max_bytes, 'memory_high_bytes': memory_high_bytes,
             'memory_swap_max_bytes': memory_swap_max_bytes, 'reserve_bytes': reserve_bytes,
             'start_reserve_bytes': start_reserve_bytes, 'lease_seconds': lease_seconds,
             'sample_seconds': sample_seconds, 'wait_seconds': wait_seconds,
             'cpu_enforcement':'inherited two-CPU affinity with per-thread cgroup readback',
             'cpu_quota_controller_available':False,
             'disk_paths':[str(p) for p in disk_paths], 'disk_floor_bytes':disk_floor_bytes,'wall_seconds':wall_seconds,
             'phase': 'waiting_for_host_reserve', 'child_exit_code': None,
             'limit_reason': None, 'peak_sampled_memory_current_bytes': 0,
             'elapsed_time_kill': False, 'retry': False,
             'minimum_sampled_disk_free_bytes': {},
             'disk_minimum_qualification': 'Sampled whole-volume free-space minimum per guarded path; includes unnamed temporary files and unrelated activity. Not a kernel quota, continuous minimum or per-job attribution.'}
    if physical_policy is not None:state['physical_policy']=physical_policy
    if native_unit_limits is not None:state['native_unit_limits']=native_unit_limits
    launched = False
    cgroup = None
    selected_primary = None
    selected_body_error = None
    selected_finalization_failed = False
    if native_unit_limits is not None:
        from tradingagents.research.onchain_replication import owned_io as native_io

    if storage_watch is not None:
        if hasattr(storage_watch,'budget'):
            state['storage_budget']=storage_watch.budget
            state['storage_watched_root_identities']=storage_watch.identities
        else:
            state['storage_budget']={'root':str(storage_watch.root),'limits':dict(storage_watch.limits)}
            state['storage_root_identity']=list(storage_watch.identity)
        state['storage_enforcement']='Sampled stop on observed breach; not a hard filesystem quota. Scan-time checks cannot preempt blocked metadata syscalls. Guard receipts and writer overshoot require separate reserved allowance.'

    def observe_storage():
        if storage_watch is None:return
        try:
            observation=storage_watch.check()
        except BaseException as error:
            if native_unit_limits is not None:
                selected=_native_reason(state,error,native_io)
                try:
                    if hasattr(error,'observation'):state.setdefault('storage_breach',dict(error.observation))
                except BaseException as diagnostic:selected=_native_select(selected,diagnostic,native_io)
                raise selected
            try:
                state['storage_last_error']=type(error).__name__+': '+str(error)
                if hasattr(error,'observation'):state.setdefault('storage_breach',dict(error.observation))
            except BaseException as diagnostic:
                if not isinstance(error,Exception) or isinstance(error,MemoryError):raise error
                if not isinstance(diagnostic,Exception) or isinstance(diagnostic,MemoryError):raise diagnostic from error
                error.add_note('storage failure diagnostics unavailable: '+repr(diagnostic))
            raise
        state['storage_observation']=observation
        for key in ('allocated_bytes','logical_file_bytes','entries'):
            peak='storage_peak_'+key
            state[peak]=max(state.get(peak,0),observation[key])

    def boundaries():
        if physical_policy is not None:
            state['physical_observation']=physical_scope.check()
            log=receipt/'child.log'
            if log.exists() and log.stat().st_size>=physical_policy['max_file_bytes']:
                state['child_log_limit_reached']=True
                raise RuntimeError('bounded child.log file limit reached; output may be incomplete')
        observe_storage()
        state['disk_free_bytes']={str(p):shutil.disk_usage(p).free for p in disk_paths}
        for path, free in state['disk_free_bytes'].items():
            previous = state['minimum_sampled_disk_free_bytes'].get(path, free)
            state['minimum_sampled_disk_free_bytes'][path] = min(previous, free)
        if any(v<disk_floor_bytes for v in state['disk_free_bytes'].values()):raise RuntimeError('disk floor breached')
        if time.monotonic()-begin>wall_seconds:raise RuntimeError('registered wall-clock limit exceeded')

    def stopped(signum,frame):raise InterruptedError('guard received signal '+str(signum))
    if native_unit_limits is not None:prior_signals={}
    else:prior_signals={sig:signal.signal(sig,stopped) for sig in (signal.SIGTERM,signal.SIGINT)}

    def publish():
        state['monotonic_seconds'] = time.monotonic()
        state['elapsed_seconds'] = time.monotonic() - begin
        if native_unit_limits is not None:_native_atomic(receipt/'live.json',state,native_io,max_bytes=native_metadata_bytes)
        else:_atomic(receipt / 'live.json', state)

    try:
        if native_unit_limits is not None:
            prior_signals={sig:signal.getsignal(sig) for sig in (signal.SIGTERM,signal.SIGINT)}
            for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,stopped)
        while True:
            boundaries()
            state['host_mem_available_bytes'] = mem_available()
            publish()
            if state['host_mem_available_bytes'] >= start_reserve_bytes:
                break
            if time.monotonic() - begin >= wait_seconds:
                raise RuntimeError('host startup memory reserve unavailable')
            time.sleep(sample_seconds)
        state['phase'] = 'verifying_cgroup'
        publish()
        args = ['systemd-run', '--user', '--quiet', '--unit=' + unit,
                '--property=Type=exec', '--property=KillMode=control-group',
                '--property=TimeoutStopSec=2s', '--property=SendSIGKILL=yes',
                '--property=MemoryAccounting=yes', '--property=OOMPolicy=kill',
                '--property=CPUQuota=200%', '--property=CPUQuotaPeriodSec=100ms',
                '--property=MemoryMax=' + str(memory_max_bytes),
                '--property=MemoryHigh=' + str(memory_high_bytes),
                '--property=MemorySwapMax=' + str(memory_swap_max_bytes), '--property=TasksMax=64',
                '--property=WorkingDirectory=' + str(cwd),
                '--property=StandardOutput=append:' + str(receipt / 'child.log'),
                '--property=StandardError=append:' + str(receipt / 'child.log'),
                sys.executable, '-B', str(Path(__file__).resolve()), '--child', str(receipt),
                '--cpus', ','.join(map(str, cpus)), '--lease', str(lease_seconds), '--', *command]
        if physical_policy is not None:
            position=args.index(sys.executable)
            args[position:position]=['--property=LimitFSIZE='+str(physical_policy['max_file_bytes']),
                                     '--setenv=PYTHONPATH='+str(cwd)]+['--setenv='+key+'='+value for key,value in physical_scope.environment().items()]
            position=args.index('--',args.index('--lease'))
            context={'experiment':physical_scope.anchor['experiment'],'source':physical_scope.anchor['source'],
                     'policy':physical_policy,'anchor':physical_scope.anchor_hash}
            args[position:position]=['--physical','--physical-context',json.dumps(context,sort_keys=True)]
        if native_unit_limits is not None:
            position=args.index(sys.executable)
            args[position:position]=['--property=LimitFSIZE='+str(native_unit_limits['file_size_bytes']),'--property=RuntimeMaxSec='+str(wall_seconds)]+['--setenv='+key+'='+value for key,value in _native_owned_env(cwd,storage_budget).items()]
            position=args.index('--',args.index('--lease'))
            args[position:position]=['--native-file-limit',str(native_unit_limits['file_size_bytes'])]
        # Even an uncertain dispatch is cleaned up using this unique identity.
        launched = True
        subprocess.run(args, check=True, capture_output=True, text=True, timeout=10)
        props = _properties(unit)
        relative = props.get('ControlGroup', '')
        if not relative.startswith('/user.slice/') or '..' in Path(relative).parts:
            raise RuntimeError('unexpected or missing user cgroup')
        cgroup = Path('/sys/fs/cgroup') / relative.lstrip('/')
        state['cgroup'] = str(cgroup)
        ready_deadline=time.monotonic()+5
        while not (receipt/'cpu_ready.json').exists():
            if time.monotonic()>ready_deadline:raise RuntimeError('child affinity readback unavailable')
            time.sleep(.05)
        state['cpu_thread_readback']=verify_cpu_tree(cgroup,cpus)
        ready=json.loads((receipt/'cpu_ready.json').read_bytes())
        if ready.get('cpus')!=cpus or state['cpu_thread_readback'].get(str(ready.get('pid')))!=cpus:raise RuntimeError('ready process lacks cgroup CPU readback')
        if physical_policy is not None:
            from tradingagents.research.onchain_replication.neural_physical import verify_file_limit
            verify_file_limit(physical_policy['max_file_bytes'],ready.get('file_size_limit',()))
        if native_unit_limits is not None:
            selected=_systemctl('show',unit,'--property=LimitFSIZE,LimitFSIZESoft,RuntimeMaxUSec')
            state['native_unit_properties']=dict(line.split('=',1) for line in selected.stdout.splitlines() if '=' in line)
            _native_ready(native_unit_limits,ready,state['native_unit_properties'],wall_seconds,cwd,storage_budget)
            state['native_environment']=ready['native_environment']
        state['kernel_controls'] = _read_controls(cgroup)
        _verify_controls(state['kernel_controls'], memory_max_bytes, memory_high_bytes, memory_swap_max_bytes)
        state.update(_snapshot(cgroup))
        state['initial_memory_events'] = dict(state['memory_events'])
        state['peak_sampled_memory_current_bytes'] = state['memory_current_bytes']
        if state['memory_events']['oom'] or state['memory_events']['oom_kill']:
            raise RuntimeError('kernel OOM event occurred before workload release')
        state['host_mem_available_bytes'] = mem_available()
        if state['host_mem_available_bytes'] < start_reserve_bytes:
            raise RuntimeError('host reserve fell during cgroup setup')
        boundaries()
        state['phase'] = 'running'
        publish()
        if native_unit_limits is not None:_native_atomic(receipt/'release.json',{'kernel_controls_verified':True},native_io,max_bytes=native_metadata_bytes)
        else:_atomic(receipt / 'release.json', {'kernel_controls_verified': True})
        while True:
            boundaries()
            props = _properties(unit)
            if cgroup.exists():state['cpu_thread_readback']=verify_cpu_tree(cgroup,cpus)
            state['unit_properties'] = props
            try:
                state.update(_snapshot(cgroup))
                state['peak_sampled_memory_current_bytes'] = max(
                    state['peak_sampled_memory_current_bytes'], state['memory_current_bytes'])
            except FileNotFoundError:
                props = _properties(unit)
                state['unit_properties'] = props
                if props.get('ActiveState') in ('active', 'activating'):
                    raise RuntimeError('active unit lost resource accounting')
            state['host_mem_available_bytes'] = mem_available()
            publish()
            if props.get('ActiveState') not in ('active', 'activating'):
                if (receipt / 'child_exit.json').exists():
                    child_exit = json.loads((receipt / 'child_exit.json').read_text())
                    state['child_exit_code'] = child_exit['exit_code']
                    terminal = _terminal_snapshot(child_exit)
                    state['terminal_memory_snapshot'] = terminal
                    state.update(terminal)
                    state['peak_sampled_memory_current_bytes'] = max(
                        state['peak_sampled_memory_current_bytes'], state['memory_current_bytes'])
                if props.get('Result') != 'success' or state['child_exit_code'] != 0:
                    raise RuntimeError('child or unit failed: ' + str(props))
                if state['memory_events']['oom'] or state['memory_events']['oom_kill']:
                    raise RuntimeError('kernel OOM event occurred during workload')
                break
            if state['host_mem_available_bytes'] < reserve_bytes:
                raise RuntimeError('host runtime memory reserve breached')
            time.sleep(sample_seconds)
    except BaseException as exc:
        if native_unit_limits is not None:
            selected_primary=selected_body_error=exc
            selected_primary=_native_reason(state,selected_primary,native_io)
        else:
            state['limit_reason'] = f'{type(exc).__name__}: {exc}'
            if physical_policy is not None:
                selected_primary=exc
                selected_body_error=exc
    finally:
        if physical_policy is not None:
            from tradingagents.research.onchain_replication.neural_physical import _sync
            physical_scope.tail=True
            def retain(error):
                nonlocal selected_primary, selected_finalization_failed
                selected_finalization_failed = True
                if selected_primary is None:selected_primary=error
                elif error is not selected_primary:
                    if isinstance(selected_primary,Exception) and not isinstance(selected_primary,MemoryError) and (not isinstance(error,Exception) or isinstance(error,MemoryError)):
                        error.__cause__=selected_primary;selected_primary=error
                    else:selected_primary.add_note('selected guard finalization failure: '+repr(error))
                state['limit_reason']=state['limit_reason'] or type(error).__name__+': '+str(error)
                state['phase']='failed'
            for sig in (signal.SIGTERM,signal.SIGINT):
                try:signal.signal(sig,signal.SIG_IGN)
                except BaseException as error:retain(error)
            if launched:
                try:
                    stopped=_systemctl('stop',unit,check=False);after=_properties(unit)
                    if after.get('ActiveState') not in ('inactive','failed'):raise RuntimeError('unit did not stop: '+str(after))
                    state['cleanup_unit_properties']=after;state['cleanup_stop_returncode']=stopped.returncode
                    if cgroup is not None and cgroup.exists() and 'populated 1' in (cgroup/'cgroup.events').read_text():raise RuntimeError('unit cgroup remains populated after stop')
                    state['cleanup_verified']=True
                except BaseException as error:
                    state['cleanup_verified']=False;state['cleanup_error']=str(error);retain(error)
            try:state['physical_final_observation']=physical_scope.check(tail=True)
            except BaseException as error:retain(error)
            state['phase']='complete' if state['limit_reason'] is None else 'failed'
            # Every independent evidence action is attempted, even after fatal cleanup.
            try:publish()
            except BaseException as error:retain(error)
            try:physical_scope.immutable(receipt/'final.json',state)
            except BaseException as error:retain(error)
            try:_sync(receipt)
            except BaseException as error:retain(error)
            for sig,previous in prior_signals.items():
                try:signal.signal(sig,previous)
                except BaseException as error:retain(error)
        elif native_unit_limits is not None:
            # Signals, stop, readback, storage, evidence and restores are separate
            # cleanup attempts. No physical scope is fabricated for this route.
            actions=[]
            for sig in (signal.SIGTERM,signal.SIGINT):
                actions.append(('ignore-signal-'+str(sig),lambda sig=sig:signal.signal(sig,signal.SIG_IGN)))
            stop_state={}
            if launched:
                state['cleanup_verified']=False
                def stop_unit():
                    result=_systemctl('stop',unit,check=False)
                    state['cleanup_stop_returncode']=result.returncode;stop_state['stop']=True
                def read_unit():
                    after=_properties(unit);state['cleanup_unit_properties']=after
                    if after.get('ActiveState') not in ('inactive','failed'):raise RuntimeError('native unit did not stop')
                    stop_state['unit']=True
                def read_cgroup():
                    if cgroup is not None and cgroup.exists() and 'populated 1' in (cgroup/'cgroup.events').read_text():
                        raise RuntimeError('native unit cgroup remains populated after stop')
                    stop_state['cgroup']=True
                def verify_stop():
                    if set(stop_state)!={'stop','unit','cgroup'}:raise RuntimeError('native stop/readback is incomplete')
                    state['cleanup_verified']=True
                actions.extend((('stop-unit',stop_unit),('read-unit',read_unit),('read-cgroup',read_cgroup),('verify-stop',verify_stop)))
            actions.append(('observe-storage',observe_storage))
            def final_disk():
                state['disk_free_bytes']={str(p):shutil.disk_usage(p).free for p in disk_paths}
                for path, free in state['disk_free_bytes'].items():
                    previous = state['minimum_sampled_disk_free_bytes'].get(path, free)
                    state['minimum_sampled_disk_free_bytes'][path] = min(previous, free)
                if any(v<disk_floor_bytes for v in state['disk_free_bytes'].values()):raise RuntimeError('native final disk floor breached')
            actions.append(('final-disk-floor',final_disk))
            actions.append(('publish',publish))
            # Restore signals before the immutable final attempt, so failures
            # already known at that boundary are represented as failed.
            for sig,previous in prior_signals.items():
                actions.append(('restore-signal-'+str(sig),lambda sig=sig,previous=previous:signal.signal(sig,previous)))
            actions.extend((('final-receipt',lambda:_native_write(receipt/'final.json',state,native_io,max_bytes=native_metadata_bytes)),
                ('directory-sync',lambda:_native_sync(receipt,native_io))))
            selected_primary,selected_finalization_failed=_native_finalize(state,selected_primary,actions,native_io)
            if selected_finalization_failed:
                # An immutable final body may precede a late close/fsync error.
                # It never overrides this failed invocation and additive marker.
                tail=(('failed-live',publish),('failed-marker',lambda:_native_write(receipt/'native-finalization-failed.json',state,native_io,max_bytes=native_metadata_bytes)),
                    ('failed-directory-sync',lambda:_native_sync(receipt,native_io)))
                selected_primary,_=_native_finalize(state,selected_primary,tail,native_io)
        else:
            signal.signal(signal.SIGTERM,signal.SIG_IGN);signal.signal(signal.SIGINT,signal.SIG_IGN)
            if launched:
                try:
                    stopped = _systemctl('stop', unit, check=False)
                    after = _properties(unit)
                    if after.get('ActiveState') not in ('inactive', 'failed'):
                        raise RuntimeError('unit did not stop: ' + str(after))
                    state['cleanup_unit_properties'] = after
                    state['cleanup_stop_returncode'] = stopped.returncode
                    if cgroup is not None and cgroup.exists():
                        events = (cgroup / 'cgroup.events').read_text()
                        if 'populated 1' in events:
                            raise RuntimeError('unit cgroup remains populated after stop')
                    state['cleanup_verified'] = True
                except Exception as exc:
                    state['cleanup_verified'] = False
                    state['cleanup_error'] = str(exc)
                    state['limit_reason'] = state['limit_reason'] or 'unit cleanup failed'
            try:observe_storage()
            except Exception as exc:state['limit_reason']=state['limit_reason'] or f'{type(exc).__name__}: {exc}'
            state['phase'] = 'complete' if state['limit_reason'] is None else 'failed'
            publish()
            with (receipt / 'final.json').open('x') as stream:
                json.dump(state, stream, indent=2, sort_keys=True)
                stream.write('\n')
                stream.flush()
                os.fsync(stream.fileno())
    if physical_policy is not None:
        if selected_primary is not None and (selected_finalization_failed or selected_primary is not selected_body_error or not isinstance(selected_primary,Exception) or isinstance(selected_primary,MemoryError)):
            raise selected_primary
    elif native_unit_limits is not None:
        if selected_primary is not None and (selected_finalization_failed or selected_primary is not selected_body_error
                or native_io._fatal(selected_primary) or isinstance(selected_primary,native_io.CleanupFailure)):
            raise selected_primary
    else:
        fd=os.open(receipt,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
        for sig,previous in prior_signals.items():signal.signal(sig,previous)
    return state


def assert_guarded_worker(receipt,command,*,required_paths,wall_seconds,
                          memory_max_bytes=6*GIB,memory_high_bytes=5*GIB,
                          disk_floor_bytes=20*GIB):
    if not 0<memory_high_bytes<=memory_max_bytes<=6*GIB:
        raise ValueError('worker memory contract outside admitted ceiling')
    if isinstance(disk_floor_bytes,bool) or not isinstance(disk_floor_bytes,int) or disk_floor_bytes<10*GIB:
        raise ValueError('worker disk contract below admitted 10 GiB floor')
    receipt=Path(receipt).resolve(strict=True)
    live=json.loads((receipt/'live.json').read_bytes())
    if live['command']!=command or live['phase']!='running':raise RuntimeError('guard command identity differs')
    if not json.loads((receipt/'release.json').read_bytes()).get('kernel_controls_verified'):raise RuntimeError('guard not released')
    if live['boot_id']!=Path('/proc/sys/kernel/random/boot_id').read_text().strip():raise RuntimeError('guard boot mismatch')
    if not 0<=time.monotonic()-live['monotonic_seconds']<=live['lease_seconds']:raise RuntimeError('guard lease expired')
    if str(_own_cgroup())!=live['cgroup'] or set(os.sched_getaffinity(0))!=set(live['cpus']):raise RuntimeError('guard containment differs')
    _verify_controls(_read_controls(_own_cgroup()),memory_max_bytes,memory_high_bytes,0)
    verify_cpu_tree(_own_cgroup(),live['cpus'])
    if not required_paths or not live['disk_paths']:raise RuntimeError('guard disk volumes unbound')
    covered={Path(p).stat().st_dev for p in live['disk_paths']}
    if not {Path(p).stat().st_dev for p in required_paths}<=covered:raise RuntimeError('guard misses required volume')
    if not 0<live['wall_seconds']<=wall_seconds<=28800:raise RuntimeError('guard wall limit differs')
    if live['reserve_bytes']<3*GIB or live['disk_floor_bytes']<disk_floor_bytes:raise RuntimeError('guard reserve below protocol')
    if live['start_reserve_bytes']<memory_max_bytes+live['reserve_bytes']:raise RuntimeError('guard startup reserve below contract')
    if 'physical_policy' in live:
        import resource
        from tradingagents.research.onchain_replication.neural_physical import verify_file_limit
        verify_file_limit(live['physical_policy']['max_file_bytes'],resource.getrlimit(resource.RLIMIT_FSIZE))
    if 'native_unit_limits' in live:
        import resource
        expected=_native_policy(live['native_unit_limits'])['file_size_bytes']
        if resource.getrlimit(resource.RLIMIT_FSIZE)!=(expected,expected):raise RuntimeError('native worker file limit differs')
        if {key:os.environ.get(key) for key in _native_owned_env(Path.cwd(),live.get('storage_budget'))}!=_native_owned_env(Path.cwd(),live.get('storage_budget')):raise RuntimeError('native worker environment differs')
    return live


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--child', type=Path, required=True)
    parser.add_argument('--cpus', required=True)
    parser.add_argument('--lease', type=float, required=True)
    parser.add_argument('--physical', action='store_true')
    parser.add_argument('--physical-context')
    parser.add_argument('--native-file-limit',type=int)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    command = arguments.command[1:] if arguments.command[:1] == ['--'] else arguments.command
    raise SystemExit(_child(arguments.child, [int(cpu) for cpu in arguments.cpus.split(',')], arguments.lease, command, arguments.physical, arguments.physical_context, None if arguments.native_file_limit is None else {'file_size_bytes':arguments.native_file_limit}))


def bind_parent_death(owner_pid):
    """Linux parent-death signal plus race check; call before any child launch."""
    import ctypes
    if ctypes.CDLL(None,use_errno=True).prctl(1,signal.SIGTERM,0,0,0)!=0:raise OSError(ctypes.get_errno(),'cannot bind parent death signal')
    if os.getppid()!=owner_pid:raise RuntimeError('supervisor disappeared before monitor binding')
