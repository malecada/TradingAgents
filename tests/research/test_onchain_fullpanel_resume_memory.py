"""Synthetic controls; no market data, credentials, network, or large allocations.

The ordinary offline profile mocks user systemd. Tiny real user-unit integration
probes are performed separately on this host, never implicitly by this module.
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

SOURCE = Path(__file__).resolve().parents[2] / 'research/onchain-graph-2026-09-16/fullpanel_resume/memory_guard.py'
spec = importlib.util.spec_from_file_location('fullpanel_memory_tested', SOURCE)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def test_available_requires_kernel_field(tmp_path):
    path = tmp_path / 'meminfo'
    path.write_text('MemFree: 123 kB\nMemAvailable: 456 kB\n')
    assert guard.mem_available(path) == 456 * 1024
    path.write_text('MemFree: 123 kB\n')
    with pytest.raises(RuntimeError):
        guard.mem_available(path)


@pytest.mark.parametrize('key,value', [('memory.max', 'max'), ('memory.high', 'max'), ('memory.swap.max', 'max')])
def test_controls_fail_closed(key, value):
    actual = {'memory.max': '100', 'memory.high': '50', 'memory.swap.max': '0'}
    actual[key] = value
    with pytest.raises(RuntimeError):
        guard._verify_controls(actual, 100, 50, 0)


@pytest.mark.parametrize('kwargs', [dict(memory_max_bytes=9*guard.GIB), dict(memory_high_bytes=7*guard.GIB),
    dict(memory_swap_max_bytes=guard.GIB), dict(reserve_bytes=0), dict(start_reserve_bytes=guard.GIB),
    dict(sample_seconds=2), dict(lease_seconds=1), dict(wait_seconds=-1)])
def test_invalid_limits_do_not_make_receipt(tmp_path, kwargs):
    receipt = tmp_path / 'receipt'
    with pytest.raises(ValueError):
        guard.guarded_run(['true'], cwd=tmp_path, receipt_dir=receipt, **kwargs)
    assert not receipt.exists()


def test_startup_pressure_never_dispatches(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, 'mem_available', lambda: 2*guard.GIB)
    monkeypatch.setattr(guard.subprocess, 'run', lambda *a, **k: pytest.fail('must not dispatch'))
    result = guard.guarded_run(['true'], cwd=tmp_path, receipt_dir=tmp_path/'r', wait_seconds=0)
    assert result['phase'] == 'failed'
    assert 'startup memory reserve' in result['limit_reason']
    assert not (tmp_path/'r/release.json').exists()
    assert json.loads((tmp_path/'r/final.json').read_text()) == result
    with pytest.raises(FileExistsError):
        guard.guarded_run(['true'], cwd=tmp_path, receipt_dir=tmp_path/'r')


def mock_unit(tmp_path, monkeypatch, *, controls=None, memory=None, completed=False):
    receipt = tmp_path/'r'
    values = iter(memory or [20*guard.GIB]*20)
    monkeypatch.setattr(guard, 'mem_available', lambda: next(values))
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        if completed and args[0] == 'systemd-run':
            (receipt/'child_exit.json').write_text(json.dumps({'exit_code': 0,
                'terminal_memory_snapshot': {'memory_current_bytes': 42, 'memory_events': {'oom': 0, 'oom_kill': 0}}}))
        return subprocess.CompletedProcess(args, 0, '', '')
    monkeypatch.setattr(guard.subprocess, 'run', run)
    counts = iter(range(20))
    def properties(unit):
        index = next(counts)
        active = index == 0 or (index == 1 and not completed)
        return {'ControlGroup': '/user.slice/synthetic.service', 'ActiveState': 'active' if active else 'inactive', 'Result': 'success'}
    monkeypatch.setattr(guard, '_properties', properties)
    monkeypatch.setattr(guard, '_read_controls', lambda _: controls or {
        'memory.max': str(6*guard.GIB), 'memory.high': str(4*guard.GIB), 'memory.swap.max': str(guard.GIB//2)})
    monkeypatch.setattr(guard, '_snapshot', lambda _: {'memory_current_bytes': 42, 'memory_events': {'oom': 0, 'oom_kill': 0}})
    return receipt, calls


def test_verified_success_and_kernel_command(tmp_path, monkeypatch):
    receipt, calls = mock_unit(tmp_path, monkeypatch, completed=True)
    result = guard.guarded_run([sys.executable, '-B', '-c', 'pass'], cwd=tmp_path, receipt_dir=receipt)
    assert result['phase'] == 'complete'
    assert result['cleanup_verified']
    assert result['child_exit_code'] == 0
    launch = calls[0]
    for prop in ['MemoryMax=6442450944', 'MemoryHigh=4294967296', 'MemorySwapMax=536870912', 'KillMode=control-group', 'OOMPolicy=kill']:
        assert '--property='+prop in launch
    assert len(result['cpus']) <= 2


def test_bad_readback_keeps_gate_closed_and_stops_unit(tmp_path, monkeypatch):
    receipt, calls = mock_unit(tmp_path, monkeypatch, controls={'memory.max': 'max'}, completed=True)
    result = guard.guarded_run(['true'], cwd=tmp_path, receipt_dir=receipt)
    assert 'kernel memory controls differ' in result['limit_reason']
    assert not (receipt/'release.json').exists()
    assert any('stop' in call for call in calls)


def test_runtime_host_pressure_stops_entire_unit(tmp_path, monkeypatch):
    receipt, calls = mock_unit(tmp_path, monkeypatch, memory=[20*guard.GIB, 20*guard.GIB, guard.GIB])
    result = guard.guarded_run(['true'], cwd=tmp_path, receipt_dir=receipt)
    assert 'runtime memory reserve breached' in result['limit_reason']
    assert (receipt/'release.json').exists()
    assert result['cleanup_verified']
    assert any('stop' in call for call in calls)


def test_stale_lease_never_starts_command(tmp_path, monkeypatch):
    (tmp_path/'live.json').write_text('{"monotonic_seconds": -100}')
    (tmp_path/'release.json').write_text('{}')
    monkeypatch.setattr(guard.os, 'sched_setaffinity', lambda *a: None)
    monkeypatch.setattr(guard.signal, 'signal', lambda *a: None)
    monkeypatch.setattr(guard.subprocess, 'Popen', lambda *a, **k: pytest.fail('stale lease dispatched'))
    assert guard._child(tmp_path, [0], 5, ['true']) == 125


def test_missing_oom_fields_cannot_become_zero(tmp_path):
    (tmp_path/'memory.current').write_text('10')
    (tmp_path/'memory.events').write_text('high 0\noom_kill 0\n')
    with pytest.raises(RuntimeError, match='counters unavailable'):
        guard._snapshot(tmp_path)


def test_short_unit_preserves_pre_release_snapshot(tmp_path, monkeypatch):
    receipt, calls = mock_unit(tmp_path, monkeypatch, completed=True)
    def snapshot(cgroup):
        if (receipt/'release.json').exists():
            raise FileNotFoundError('short unit has exited')
        return {'memory_current_bytes': 42, 'memory_events': {'oom': 0, 'oom_kill': 0}}
    monkeypatch.setattr(guard, '_snapshot', snapshot)
    result = guard.guarded_run(['true'], cwd=tmp_path, receipt_dir=receipt)
    assert result['phase'] == 'complete'
    assert result['memory_events'] == {'oom': 0, 'oom_kill': 0}
    assert result['initial_memory_events'] == result['memory_events']


def test_initial_oom_prevents_release(tmp_path, monkeypatch):
    receipt, calls = mock_unit(tmp_path, monkeypatch, completed=True)
    monkeypatch.setattr(guard, '_snapshot', lambda _: {'memory_current_bytes': 42, 'memory_events': {'oom': 1, 'oom_kill': 0}})
    result = guard.guarded_run(['true'], cwd=tmp_path, receipt_dir=receipt)
    assert 'before workload release' in result['limit_reason']
    assert not (receipt/'release.json').exists()


@pytest.mark.parametrize('terminal', [None, {'memory_current_bytes': 42, 'memory_events': {'oom_kill': 0}},
    {'memory_current_bytes': 42, 'memory_events': {'oom': 1, 'oom_kill': 0}}])
def test_terminal_unknown_or_oom_cannot_pass(tmp_path, monkeypatch, terminal):
    receipt, calls = mock_unit(tmp_path, monkeypatch, completed=True)
    snapshot = guard._snapshot
    def write_terminal(cgroup):
        if (receipt/'release.json').exists():
            (receipt/'child_exit.json').write_text(json.dumps({'exit_code': 0, 'terminal_memory_snapshot': terminal}))
        return snapshot(cgroup)
    monkeypatch.setattr(guard, '_snapshot', write_terminal)
    result = guard.guarded_run(['true'], cwd=tmp_path, receipt_dir=receipt)
    assert result['phase'] == 'failed'
    assert 'terminal child' in result['limit_reason'] or 'kernel OOM event' in result['limit_reason']


@pytest.mark.parametrize('change', ['none', 'stale', 'wrong_cgroup', 'wrong_source', 'missing_release', 'wrong_cpu'])
def test_worker_requires_live_containment(tmp_path, monkeypatch, change):
    base = tmp_path/'research/onchain-graph-2026-09-16/fullpanel_resume'
    receipt = base/'resources/compute'
    receipt.mkdir(parents=True)
    cgroup = Path('/sys/fs/cgroup/user.slice/test.service')
    live = dict(phase='running', command=[sys.executable, '-B', str(base/'run.py'), '--source', 'source'],
        cwd=str(tmp_path), receipt_dir=str(receipt), boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        monotonic_seconds=guard.time.monotonic(), lease_seconds=15, cgroup=str(cgroup), unit=cgroup.name,
        cpus=[0,1], reserve_bytes=3*guard.GIB, start_reserve_bytes=9*guard.GIB)
    if change == 'stale': live['monotonic_seconds'] -= 30
    if change == 'wrong_cgroup': live['cgroup'] = '/other'
    if change == 'wrong_source': live['command'][-1] = 'other'
    if change == 'wrong_cpu': live['cpus'] = [0]
    (receipt/'live.json').write_text(json.dumps(live))
    (receipt/'release.json').write_text(json.dumps({'kernel_controls_verified': change != 'missing_release'}))
    monkeypatch.setattr(guard, '_own_cgroup', lambda: cgroup)
    monkeypatch.setattr(guard.os, 'sched_getaffinity', lambda _: {0,1})
    monkeypatch.setattr(guard, '_read_controls', lambda _: {'memory.max': str(6*guard.GIB), 'memory.high': str(4*guard.GIB), 'memory.swap.max': str(guard.GIB//2)})
    if change == 'none':
        assert guard.assert_guarded_worker(tmp_path, 'source') == live
    else:
        with pytest.raises(RuntimeError):
            guard.assert_guarded_worker(tmp_path, 'source')
