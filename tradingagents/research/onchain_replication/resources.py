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
                 'file_bytes': None, 'swap_current_bytes': None, 'unavailable': {}}
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
            'qualification': 'Optional last observations; unavailable is unknown, not zero. No PSI policy change.'}


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


def _child(receipt, cpus, lease_seconds, command):
    """Main process writes its terminal before systemd kills surviving descendants."""
    stopping=False;code=125;reason='not released';process=None
    def stop(signum,frame):
        nonlocal stopping
        stopping=True
    def fresh():
        try:
            lease=json.loads((receipt/'live.json').read_text())
            return 0<=time.monotonic()-lease['monotonic_seconds']<=lease_seconds
        except (OSError,ValueError,KeyError):return False
    try:
        os.sched_setaffinity(0,set(cpus))
        _atomic(receipt/'cpu_ready.json',{'pid':os.getpid(),'cpus':sorted(os.sched_getaffinity(0))})
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
        _atomic(receipt/'child_exit.json',{'exit_code':code,'reason':reason,'workload_pid':None if process is None else process.pid,'terminal_memory_snapshot':snapshot,'snapshot_error':snapshot_error})


def guarded_run(command, *, cwd, receipt_dir, memory_max_bytes=6 * GIB,
                memory_high_bytes=5 * GIB, memory_swap_max_bytes=0, reserve_bytes=3 * GIB,
                start_reserve_bytes=None, sample_seconds=.25,
                lease_seconds=15., wait_seconds=30., disk_paths=(), disk_floor_bytes=20*GIB, wall_seconds=28800., owner_identity=None):
    """Run one command, or fail closed; return a durable resource receipt.

    No retry occurs. Startup waits at most wait_seconds for MemAvailable >=
    start_reserve_bytes (default cap + reserve). Runtime reserve pressure kills
    the entire unit. No elapsed workload limit is imposed. Existing receipt
    directories are rejected; live state is atomically replaced within this new
    invocation only. final.json is exclusive. CPU affinity is inherited by all
    ordinary children; malicious workload code is outside this guard's scope.
    """
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
             'elapsed_time_kill': False, 'retry': False}
    launched = False
    cgroup = None

    def boundaries():
        state['disk_free_bytes']={str(p):shutil.disk_usage(p).free for p in disk_paths}
        if any(v<disk_floor_bytes for v in state['disk_free_bytes'].values()):raise RuntimeError('disk floor breached')
        if time.monotonic()-begin>wall_seconds:raise RuntimeError('registered wall-clock limit exceeded')

    def stopped(signum,frame):raise InterruptedError('guard received signal '+str(signum))
    prior_signals={sig:signal.signal(sig,stopped) for sig in (signal.SIGTERM,signal.SIGINT)}

    def publish():
        state['monotonic_seconds'] = time.monotonic()
        state['elapsed_seconds'] = time.monotonic() - begin
        _atomic(receipt / 'live.json', state)

    try:
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
        _atomic(receipt / 'release.json', {'kernel_controls_verified': True})
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
        state['limit_reason'] = f'{type(exc).__name__}: {exc}'
    finally:
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
        state['phase'] = 'complete' if state['limit_reason'] is None else 'failed'
        publish()
        with (receipt / 'final.json').open('x') as stream:
            json.dump(state, stream, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
    fd=os.open(receipt,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    for sig,previous in prior_signals.items():signal.signal(sig,previous)
    return state


def assert_guarded_worker(receipt,command,*,required_paths,wall_seconds,
                          memory_max_bytes=6*GIB,memory_high_bytes=5*GIB):
    if not 0<memory_high_bytes<=memory_max_bytes<=6*GIB:
        raise ValueError('worker memory contract outside admitted ceiling')
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
    if live['reserve_bytes']<3*GIB or live['disk_floor_bytes']<20*GIB:raise RuntimeError('guard reserve below protocol')
    if live['start_reserve_bytes']<memory_max_bytes+live['reserve_bytes']:raise RuntimeError('guard startup reserve below contract')
    return live


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--child', type=Path, required=True)
    parser.add_argument('--cpus', required=True)
    parser.add_argument('--lease', type=float, required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    command = arguments.command[1:] if arguments.command[:1] == ['--'] else arguments.command
    raise SystemExit(_child(arguments.child, [int(cpu) for cpu in arguments.cpus.split(',')], arguments.lease, command))


def bind_parent_death(owner_pid):
    """Linux parent-death signal plus race check; call before any child launch."""
    import ctypes
    if ctypes.CDLL(None,use_errno=True).prctl(1,signal.SIGTERM,0,0,0)!=0:raise OSError(ctypes.get_errno(),'cannot bind parent death signal')
    if os.getppid()!=owner_pid:raise RuntimeError('supervisor disappeared before monitor binding')
