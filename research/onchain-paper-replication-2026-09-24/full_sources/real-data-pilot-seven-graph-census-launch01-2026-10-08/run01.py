"""One-use topology preparation, using the existing native resource guard.

No ResearchRun, financial trial, original dictionary or numerical pilot is run.
The committed request pins the caller/helper/inputs and this exact output root.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--root', required=True)
    args.add_argument('--request', required=True)
    args.add_argument('--request-sha256', required=True)
    selected = args.parse_args()
    root = Path(selected.root).resolve(strict=True)
    request_path = Path(selected.request).resolve(strict=True)
    if digest(request_path) != selected.request_sha256:
        raise ValueError('committed request digest differs')
    request = json.loads(request_path.read_bytes())
    for role, ref in request['sources'].items():
        path = root / ref['path']
        if path.is_symlink() or path.stat().st_size != ref['bytes'] or digest(path) != ref['sha256']:
            raise ValueError('selected source differs: ' + role)
    current = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, check=True,
                             capture_output=True, text=True).stdout.strip()
    active = subprocess.run(['systemctl', '--user', 'list-units', '--state=running,activating',
                             '--no-legend', '--no-pager', 'onchain-replication-*'],
                            check=True, capture_output=True, text=True).stdout.strip()
    if active:
        raise ValueError('another native replication unit is active')
    owned = root / request['output_root']
    owned.mkdir(parents=True, exist_ok=False)
    with (owned / 'launch.json').open('x') as stream:
        json.dump({'pid': os.getpid(), 'source_commit': current,
                   'identity': request['identity'], 'request_sha256': selected.request_sha256,
                   'classification': 'topology-only data preparation; no scientific trial'},
                  stream, indent=2, sort_keys=True)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    sys.path.insert(0, str(root))
    from tradingagents.research.onchain_replication.resources import guarded_run
    limits = request['limits']
    command = [str(root / '.venv/bin/python'), '-B', str(root / request['sources']['caller']['path']),
               '--root', str(root), '--settings', str(root / request['settings']['path']),
               '--settings-sha256', request['settings']['sha256'], '--output', str(owned / 'results')]
    result = guarded_run(command, cwd=owned, receipt_dir=owned / 'guard',
        memory_max_bytes=limits['memory_bytes'], memory_high_bytes=limits['memory_bytes'],
        memory_swap_max_bytes=0, reserve_bytes=limits['host_reserve_bytes'],
        start_reserve_bytes=limits['host_reserve_bytes'], sample_seconds=.25,
        lease_seconds=60., wait_seconds=0., disk_paths=(root,),
        disk_floor_bytes=limits['disk_floor_bytes'], wall_seconds=limits['wall_seconds'],
        storage_budget={'root': str(owned), 'limits': limits['storage']},
        native_unit_limits={'file_size_bytes': limits['file_size_bytes']})
    for role, ref in request['sources'].items():
        if digest(root / ref['path']) != ref['sha256']:
            raise ValueError('selected source changed during preparation: ' + role)
    if result['phase'] != 'complete' or result['child_exit_code'] != 0:
        raise RuntimeError('topology preparation failed; original outputs retained')
    print(json.dumps({'identity': request['identity'], 'phase': result['phase'],
                      'child_exit_code': result['child_exit_code']}))


if __name__ == '__main__':
    main()
