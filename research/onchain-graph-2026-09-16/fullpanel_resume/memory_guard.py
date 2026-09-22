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
            'memory_events': {key: int(value) for key, value in events.items()}}


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


def assert_guarded_worker(root, source):
    """Reject direct empirical execution before the continuation claim is made."""
    root = Path(root).resolve()
    base = root / 'research/onchain-graph-2026-09-16/fullpanel_resume'
    receipt = base / 'resources/compute'
    live = json.loads((receipt / 'live.json').read_text())
    release = json.loads((receipt / 'release.json').read_text())
    command = [sys.executable, '-B', str(base / 'run.py'), '--source', source]
    if live.get('phase') != 'running' or live.get('command') != command or live.get('cwd') != str(root):
        raise RuntimeError('guard command or phase identity differs')
    if live.get('receipt_dir') != str(receipt) or release != {'kernel_controls_verified': True}:
        raise RuntimeError('guard release identity differs')
    if live.get('boot_id') != Path('/proc/sys/kernel/random/boot_id').read_text().strip():
        raise RuntimeError('guard belongs to another boot')
    elapsed = time.monotonic() - live['monotonic_seconds']
    if not 0 < live['lease_seconds'] <= 15 or not 0 <= elapsed <= live['lease_seconds']:
        raise RuntimeError('guard lease expired')
    cgroup = _own_cgroup()
    if str(cgroup) != live.get('cgroup') or cgroup.name != live.get('unit'):
        raise RuntimeError('worker is outside its guard unit')
    _verify_controls(_read_controls(cgroup), 6*GIB, 4*GIB, GIB//2)
    if live.get('reserve_bytes') != 3*GIB or live.get('start_reserve_bytes', 0) < 9*GIB:
        raise RuntimeError('guard host reserve differs')
    cpus = sorted(os.sched_getaffinity(0))
    if cpus != live.get('cpus') or not 0 < len(cpus) <= 2:
        raise RuntimeError('worker CPU affinity differs')
    return live


def _child(receipt, cpus, lease_seconds, command):
    """Systemd main process: child exit triggers KillMode=control-group cleanup."""
    os.sched_setaffinity(0, set(cpus))
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while not stopping:
        try:
            lease = json.loads((receipt / 'live.json').read_text())
            fresh = 0 <= time.monotonic() - lease['monotonic_seconds'] <= lease_seconds
        except (OSError, ValueError, KeyError):
            fresh = False
        if not fresh:
            return 125
        if (receipt / 'release.json').exists():
            break
        time.sleep(.1)
    if stopping:
        return 125
    env = dict(os.environ, PYTHONPATH=str(Path.cwd()), OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2',
               MKL_NUM_THREADS='2', NUMEXPR_NUM_THREADS='2')
    process = subprocess.Popen(command, env=env, start_new_session=True)
    while process.poll() is None:
        try:
            lease = json.loads((receipt / 'live.json').read_text())
            fresh = 0 <= time.monotonic() - lease['monotonic_seconds'] <= lease_seconds
        except (OSError, ValueError, KeyError):
            fresh = False
        if stopping or not fresh:
            # Exiting the unit's main process asks systemd to kill every member,
            # including descendants which deliberately create a new session.
            return 125
        time.sleep(.1)
    code = process.returncode
    _atomic(receipt / 'child_exit.json', {'exit_code': code,
            'terminal_memory_snapshot': _snapshot(_own_cgroup())})
    return code if 0 <= code <= 255 else 1


def guarded_run(command, *, cwd, receipt_dir, memory_max_bytes=6 * GIB,
                memory_high_bytes=4 * GIB, memory_swap_max_bytes=GIB // 2, reserve_bytes=3 * GIB,
                start_reserve_bytes=None, sample_seconds=.25,
                lease_seconds=15., wait_seconds=300.):
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
    if not 0 < memory_high_bytes < memory_max_bytes <= 8 * GIB:
        raise ValueError('require 0 < memory.high < memory.max <= 8GiB')
    if not 0 <= memory_swap_max_bytes <= GIB // 2:
        raise ValueError('require 0 <= memory.swap.max <= 512MiB')
    if reserve_bytes <= 0 or not 0 < sample_seconds <= 1 or lease_seconds < 5 or wait_seconds < 0:
        raise ValueError('invalid reserve, sampling, lease or waiting bound')
    if start_reserve_bytes is None:
        start_reserve_bytes = memory_max_bytes + reserve_bytes
    if start_reserve_bytes < memory_max_bytes + reserve_bytes:
        raise ValueError('startup reserve must cover memory.max plus host reserve')
    cwd = Path(cwd).resolve(strict=True)
    receipt = Path(receipt_dir).absolute()
    receipt.mkdir(parents=True, exist_ok=False)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    unit = f'onchain-resume-{uuid.uuid4().hex}.service'
    begin = time.monotonic()
    state = {'unit': unit, 'receipt_dir': str(receipt), 'command': command,
             'cwd': str(cwd), 'monitor_pid': os.getpid(), 'cpus': cpus,
             'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
             'memory_max_bytes': memory_max_bytes, 'memory_high_bytes': memory_high_bytes,
             'memory_swap_max_bytes': memory_swap_max_bytes, 'reserve_bytes': reserve_bytes,
             'start_reserve_bytes': start_reserve_bytes, 'lease_seconds': lease_seconds,
             'sample_seconds': sample_seconds, 'wait_seconds': wait_seconds,
             'phase': 'waiting_for_host_reserve', 'child_exit_code': None,
             'limit_reason': None, 'peak_sampled_memory_current_bytes': 0,
             'elapsed_time_kill': False, 'retry': False}
    launched = False
    cgroup = None

    def publish():
        state['monotonic_seconds'] = time.monotonic()
        state['elapsed_seconds'] = time.monotonic() - begin
        _atomic(receipt / 'live.json', state)

    try:
        while True:
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
        state['phase'] = 'running'
        publish()
        _atomic(receipt / 'release.json', {'kernel_controls_verified': True})
        while True:
            props = _properties(unit)
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
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--child', type=Path, required=True)
    parser.add_argument('--cpus', required=True)
    parser.add_argument('--lease', type=float, required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    command = arguments.command[1:] if arguments.command[:1] == ['--'] else arguments.command
    raise SystemExit(_child(arguments.child, [int(cpu) for cpu in arguments.cpus.split(',')], arguments.lease, command))
