"""One-use finite synthetic oracle launcher using the reviewed native guard."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import resource
import runpy
import stat
import subprocess
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
GIB = 1024**3
LIMITS = {'memory_max_bytes': GIB, 'memory_high_bytes': GIB,
          'memory_swap_max_bytes': 0, 'reserve_bytes': 3*GIB,
          'start_reserve_bytes': 4*GIB, 'wall_seconds': 120,
          'disk_floor_bytes': 10*GIB, 'file_limit_bytes': 4*1024**2,
          'allocated_stop_bytes': 64*1024**2, 'logical_stop_bytes': 64*1024**2}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def immutable(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()
    if len(raw) > 1024**2:
        raise ValueError('bounded metadata required')
    with Path(path).open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())

def verify(spec):
    if spec['status'] != 'released_single_tiny_engineering_attempt' or spec['limits'] != LIMITS:
        raise ValueError('exact reviewed release required')
    mode = spec['mode']
    if mode not in ('red', 'green') or spec['identity'] != 'neural-streamed-gat-oracle-'+mode+'-20261002-01':
        raise ValueError('identity/mode differs')
    if spec['oracle_file'] != 'oracle02.py':
        raise ValueError('only reviewed corrected oracle02 is selectable')
    if sys.prefix != str(ROOT/'.venv') or platform.python_version() != '3.13.13':
        raise ValueError('pinned interpreter required')
    versions = {d.metadata['Name']: d.version for d in importlib.metadata.distributions() if d.metadata['Name']}
    if versions != spec['installed_distribution_versions']:
        raise ValueError('distribution metadata changed')
    total = 0
    for name, expected in spec['source_files'].items():
        path = ROOT/name
        if path.resolve() != path or not path.is_relative_to(ROOT) or path.stat().st_nlink != 1 or not stat.S_ISREG(path.stat().st_mode):
            raise ValueError('source path/type/link differs')
        total += path.stat().st_size
        if path.stat().st_size > 4*1024**2 or total > 16*1024**2 or sha(path) != expected:
            raise ValueError('source bytes/capacity differ')
    if sha(__file__) != spec['launcher_sha256']:
        raise ValueError('launcher bytes differ')
    if any(name in sys.modules for name in ('torch', 'numpy')):
        raise ValueError('numerical import occurred before native release')

def load(path, expected):
    if path.resolve() != path or path.stat().st_size > 2*1024**2 or sha(path) != expected:
        raise ValueError('exact release object differs')
    spec = json.loads(path.read_bytes())
    verify(spec)
    return spec

def worker(spec):
    owned = HERE/'owned'/spec['identity']
    os.chdir(HERE)
    sys.path.insert(0, str(HERE))
    sys.argv = [str(HERE/spec['oracle_file']), '--mode', spec['mode'],
                '--report', str(owned/'oracle-report.json')]
    runpy.run_path(str(HERE/spec['oracle_file']), run_name='__main__')

def launch(path, spec, expected):
    owned = HERE/'owned'/spec['identity']
    if owned.exists() or owned.is_symlink():
        raise ValueError('identity already reserved; inspect it, never invoke again')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, timeout=10).strip()
    # All selected source must actually be committed under this exact HEAD.
    for name, expected_source in spec['source_files'].items():
        raw = subprocess.check_output(['git', 'show', head+':'+name], cwd=ROOT, timeout=10)
        if hashlib.sha256(raw).hexdigest() != expected_source:
            raise ValueError('selected committed source differs')
    (HERE/'owned').mkdir(exist_ok=True)
    owned.mkdir()
    immutable(owned/'reservation.json', {'identity': spec['identity'], 'head': head,
              'release_sha256': expected, 'started_utc': datetime.now(timezone.utc).isoformat()})
    for name in ('tmp', 'cache'):
        (owned/name).mkdir()
    environment = {'PYTHONPATH': str(ROOT), 'PYTHONDONTWRITEBYTECODE': '1',
                   'TMPDIR': str(owned/'tmp'), 'XDG_CACHE_HOME': str(owned/'cache'),
                   'TORCH_HOME': str(owned/'cache/torch'), 'OMP_NUM_THREADS': '2',
                   'MKL_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2'}
    resource.setrlimit(resource.RLIMIT_FSIZE, (4*1024**2, 4*1024**2))
    sys.path.insert(0, str(ROOT))
    from tradingagents.research.onchain_replication import resources
    real = resources.subprocess
    def run(args, **kwargs):
        if args[0] != 'systemd-run':
            return real.run(args, **kwargs)
        changed = [args[0], '--property=LimitFSIZE=4194304', '--property=RuntimeMaxSec=120s',
                   *['--setenv='+key+'='+value for key, value in sorted(environment.items())], *args[1:]]
        result = real.run(changed, **kwargs)
        unit = next(arg.split('=',1)[1] for arg in args if arg.startswith('--unit='))
        answer = real.run(['systemctl', '--user', 'show', unit,
                          '--property=LimitFSIZE,LimitFSIZESoft,RuntimeMaxUSec,CPUQuotaPerSecUSec,ControlGroup,MainPID'],
                          check=True, capture_output=True, text=True, timeout=10)
        properties = dict(line.split('=',1) for line in answer.stdout.splitlines() if '=' in line)
        immutable(owned/'native-unit-controls.json', properties)
        if properties.get('LimitFSIZE') != '4194304' or properties.get('LimitFSIZESoft') != '4194304' or properties.get('RuntimeMaxUSec') not in ('2min', '120s', '120000000'):
            raise ValueError('native file/runtime readback differs')
        return result
    result = None; primary = None
    resources.subprocess = SimpleNamespace(run=run, Popen=real.Popen)
    try:
        result = resources.guarded_run(
            [sys.executable, '-B', str(Path(__file__).resolve()), '--worker', str(path), expected],
            cwd=HERE, receipt_dir=owned/'guard', memory_max_bytes=GIB, memory_high_bytes=GIB,
            memory_swap_max_bytes=0, reserve_bytes=3*GIB, start_reserve_bytes=4*GIB,
            wait_seconds=0, wall_seconds=120, sample_seconds=.25,
            disk_paths=[owned], disk_floor_bytes=10*GIB,
            storage_budget={'root': str(owned), 'limits': {'max_allocated_bytes': 64*1024**2,
                'max_logical_bytes': 64*1024**2, 'max_entries': 12000, 'max_depth': 32, 'max_scan_seconds': 2}})
        if not result.get('cleanup_verified'):
            raise RuntimeError('descendant cleanup unverified')
        if any(result.get('memory_events',{}).get(key,0) != result.get('initial_memory_events',{}).get(key,0) for key in ('oom','oom_kill','oom_group_kill')):
            raise RuntimeError('tiny oracle suffered an OOM event')
        verify(spec)
        report = json.loads((owned/'oracle-report.json').read_bytes())
        if spec['mode'] == 'red':
            if report['status'] != 'failed' or report['error']['message'] != 'RESOURCE_EDGE_WIDE_SAVED_TENSORS' or result.get('child_exit_code') != 1 or result.get('cleanup_unit_properties',{}).get('Result') != 'exit-code':
                raise RuntimeError('RED did not reach only the expected resource sentinel')
        elif report['status'] != 'passed' or result['phase'] != 'complete':
            raise RuntimeError('GREEN did not pass inside native limits')
    except BaseException as error:
        primary = error
    finally:
        resources.subprocess = real
    try:
        immutable(owned/'launcher-terminal.json', {
            'identity': spec['identity'], 'status': 'expected_red' if primary is None and spec['mode']=='red' else 'passed' if primary is None else 'failed',
            'error': None if primary is None else repr(primary), 'head': head,
            'guard_phase': None if result is None else result.get('phase'),
            'cleanup_verified': False if result is None else result.get('cleanup_verified',False),
            'retry': False, 'finished_utc': datetime.now(timezone.utc).isoformat()})
    except BaseException as error:
        fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
        if primary is None:
            primary=error
        elif fatal(error) and not fatal(primary):
            error.__cause__=primary; primary=error
        else:
            primary.add_note('terminal publication failure: '+type(error).__name__)
    if primary is not None:
        raise primary
    return 0

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode', choices=('--run','--worker'))
    parser.add_argument('spec', type=Path); parser.add_argument('sha256')
    args=parser.parse_args(['--', *sys.argv[1:]])
    path=args.spec.resolve(strict=True); spec=load(path,args.sha256)
    return launch(path,spec,args.sha256) if args.mode=='--run' else worker(spec)

if __name__=='__main__':
    raise SystemExit(main())
