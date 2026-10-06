"""One finite graph-output preservation entry; retains originals and full recoveries."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.onchain_replication.resources import (
    assert_guarded_worker, guarded_run, mem_available,
)

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ID = 'real-pilot-may30-continuation-preservation-20261006-01'
GIB = 1024**3


def body(ref):
    relative = Path(ref['path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('relative evidence path required')
    path = ROOT / relative
    if path.resolve(strict=True) != path or not path.is_file() or path.stat().st_size > 4 * 1024**2:
        raise ValueError('canonical bounded evidence required')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise ValueError('frozen evidence changed: ' + ref['path'])
    return raw


def load(ref, name):
    raw = body(ref)
    path = ROOT / ref['path']
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), vars(module))
    return module


def publish(name, value):
    with (HERE / name).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def frozen():
    envelope_raw = (HERE / 'envelope01.json').read_bytes()
    envelope = json.loads(envelope_raw)
    if (envelope['identity'] != ID
            or envelope['local_only_evidence'] != [envelope['connection']['path']]
            or envelope['connection']['path'] in envelope['source_files']):
        raise ValueError('fixed identity/local-only connection binding differs')
    for path, sha in envelope['source_files'].items():
        body({'path': path, 'sha256': sha})
    for ref in envelope['evidence']:
        body(ref)
    if inventory(ROOT) != json.loads(body(envelope['environment'])):
        raise ValueError('installed runtime inventory differs')
    selection = json.loads(body(envelope['selection']))
    if selection['identity'] != ID:
        raise ValueError('fixed selected identity differs')
    return envelope, selection, hashlib.sha256(envelope_raw).hexdigest()


def worker():
    envelope, selection, digest = frozen()
    observation = json.loads((HERE / 'preflight01.json').read_bytes())
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if observation['head'] != head or observation['envelope_sha256'] != digest:
        raise ValueError('actual source/preflight changed')
    def guard():
        value = assert_guarded_worker(HERE / 'guard01', sys.orig_argv,
            required_paths=[ROOT], wall_seconds=14400,
            memory_max_bytes=256 * 1024**2, memory_high_bytes=192 * 1024**2,
            disk_floor_bytes=10 * GIB)
        expected = {'root': str(HERE), 'limits': {'max_allocated_bytes': 5 * GIB,
            'max_logical_bytes': 5 * GIB, 'max_entries': 4096,
            'max_depth': 16, 'max_scan_seconds': 5}}
        if (value['memory_swap_max_bytes'] != 0 or value['reserve_bytes'] != 3 * GIB
                or value['start_reserve_bytes'] != int(3.5 * GIB)
                or value['storage_budget'] != expected):
            raise ValueError('genuine selected native reserve/storage differs')
        return value
    guard()
    transport_module = load(envelope['transport'], 'reviewed_graph_preservation_transport')
    transport = transport_module.Transport(json.loads(body(envelope['connection'])),
        rate=262144, maximum_payload_bytes=8 * GIB)
    helper = load(envelope['helper'], 'reviewed_graph_preservation_helper')
    helper.preserve_selected(ROOT, HERE, selection, transport, guard)


def launch():
    envelope, selection, digest = frozen()
    release_path = HERE / 'RELEASE_REVIEW01.json'
    release = json.loads(release_path.read_bytes())
    if release.get('decision') != 'accepted' or release['envelope_sha256'] != digest:
        raise ValueError('exact independent source/entry release missing')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    for path in ('envelope01.json', 'RELEASE_REVIEW01.json'):
        relative = str((HERE / path).relative_to(ROOT))
        if subprocess.check_output(['git', 'show', head + ':' + relative], cwd=ROOT) != (HERE / path).read_bytes():
            raise ValueError('entry envelope/review not committed')
    for path, sha in {**envelope['source_files'], **release['evidence']}.items():
        if path not in envelope['local_only_evidence']:
            if hashlib.sha256(subprocess.check_output(['git', 'show', head + ':' + path], cwd=ROOT)).hexdigest() != sha:
                raise ValueError('released evidence not committed: ' + path)
        body({'path': path, 'sha256': sha})
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    if branch != 'research/onchain-paper-replication-2026-09-24':
        raise ValueError('branch differs')
    if subprocess.check_output(['git', 'ls-remote', '--exit-code', 'origin', 'refs/heads/' + branch], cwd=ROOT, text=True).split()[0] != head:
        raise ValueError('actual external Git source differs')
    for name in ('preflight01.json', 'launch-attempt01.json', 'guard01', 'intent.json', 'complete.json', 'failed.json', 'outer-exit01.json'):
        if os.path.lexists(HERE / name):
            raise FileExistsError('one-use identity already reserved: ' + name)
    if subprocess.check_output(['systemctl', '--user', 'list-units', '--state=active,activating', '--no-legend', 'onchain-replication-*.service'], text=True).strip():
        raise ValueError('another native job is active')
    for claim in (ROOT / 'research_runs').glob('*/claim.json'):
        if not claim.with_name('complete.json').exists() and not claim.with_name('failed.json').exists():
            if claim.is_symlink() or not claim.is_file() or claim.stat().st_size > 4 * 1024**2:
                raise ValueError('active claim metadata is not bounded regular data')
            program = json.loads(claim.read_bytes()).get('program_id')
            if not isinstance(program, str) or not program:
                raise ValueError('active claim program is unknown')
            if program == 'onchain-paper-replication-2026-09-24':
                raise ValueError('another replication claim is active')
    available, free = mem_available(), shutil.disk_usage(ROOT).free
    if available < int(3.5 * GIB) or free < 10 * GIB + selection['total_bytes'] + 16 * 1024**2:
        raise ValueError('fresh reserve/full retained-recovery scratch unavailable')
    observation = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'identity': ID, 'head': head, 'envelope_sha256': digest,
        'host_mem_available_bytes': available, 'disk_free_bytes': free,
        'count': selection['count'], 'selected_bytes': selection['total_bytes']}
    publish('preflight01.json', observation)
    publish('launch-attempt01.json', observation)
    result = None
    selected = 1
    fatal = None
    try:
        result = guarded_run([str(ROOT / '.venv/bin/python'), '-B', str(HERE / 'entry01.py'), '--worker'],
            cwd=ROOT, receipt_dir=HERE / 'guard01', memory_max_bytes=256 * 1024**2,
            memory_high_bytes=192 * 1024**2, memory_swap_max_bytes=0,
            reserve_bytes=3 * GIB, start_reserve_bytes=int(3.5 * GIB),
            disk_paths=[ROOT], disk_floor_bytes=10 * GIB, wall_seconds=14400,
            storage_budget={'root': str(HERE), 'limits': {'max_allocated_bytes': 5 * GIB,
                'max_logical_bytes': 5 * GIB, 'max_entries': 4096, 'max_depth': 16, 'max_scan_seconds': 5}})
        selected = 0 if result['phase'] == 'complete' and result['child_exit_code'] == 0 and result['cleanup_verified'] is True else 1
    except BaseException as error:
        fatal = error
    finally:
        publish('outer-exit01.json', {'identity': ID, 'entry_selected_exit_code': selected,
            'guard_phase': None if result is None else result.get('phase'),
            'guard_child_exit_code': None if result is None else result.get('child_exit_code'),
            'cleanup_verified': None if result is None else result.get('cleanup_verified'),
            'fatal_type': None if fatal is None else type(fatal).__name__,
            'qualification': 'Actual returned native fields; null remains unknown. Tool exit is separate. Never retry this identity.'})
    if fatal is not None:
        raise fatal
    raise SystemExit(selected)


if __name__ == '__main__':
    if sys.argv[1:] == ['--worker']:
        worker()
    elif not sys.argv[1:]:
        launch()
    else:
        raise ValueError('unsupported one-use entry')
