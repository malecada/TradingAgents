"""Close this completed profile using compact metadata and file extents only.

No checkpoint array body is opened, no algorithm is repeated, and no process is
launched or stopped. Failed/partial runs require a separately qualified closure.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = 'e6417c6f2f59c1ccf9fdb9ffd2af4c5b59020977'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def raw(path):
    require(path.suffix != '.npy', 'array body read forbidden')
    require(path.is_file() and not path.is_symlink(), str(path))
    require(path.stat().st_size <= 4 * 1024**2, 'compact input limit')
    return path.read_bytes()


def sha(path):
    return hashlib.sha256(raw(path)).hexdigest()


def read(path):
    return json.loads(raw(path))


def main():
    require(not (HERE / 'closure01.json').exists(), 'closure identity already exists')
    final = read(HERE / 'guard01/final.json')
    child = read(HERE / 'guard01/child_exit.json')
    owner = read(HERE / 'owner-observation01.json')
    result = read(HERE / 'result.json')
    require(final['phase'] == 'complete' and final['child_exit_code'] == 0
            and final['cleanup_verified'] is True and child['exit_code'] == 0,
            'successful terminal guard required')
    require(final['monitor_pid'] == owner['monitor_pid']
            and final['unit'] == owner['unit'], 'owner join')
    require(not Path(final['cgroup']).exists(), 'cgroup remains')
    proc = Path('/proc') / str(owner['monitor_pid']) / 'stat'
    if proc.exists():
        ticks = int(proc.read_text().rsplit(')', 1)[1].split()[19])
        require(ticks != owner['start_ticks'], 'exact monitor remains')
    props = subprocess.run(['systemctl', '--user', 'show', owner['unit'],
                            '-p', 'ActiveState', '-p', 'SubState'],
                           capture_output=True, text=True, check=False)
    require('ActiveState=inactive' in props.stdout and 'SubState=dead' in props.stdout,
            'unit inactivity not established')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT)
            .decode().strip() == SOURCE, 'frozen HEAD differs')
    bindings = read(HERE / 'bindings.json')
    require(len(bindings) == 100, 'source binding count')
    for path, digest in bindings.items():
        require(sha(ROOT / path) == digest, 'current binding: ' + path)
        committed = subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=ROOT)
        require(hashlib.sha256(committed).hexdigest() == digest, 'committed binding: ' + path)
    lines = [json.loads(line) for line in raw(HERE / 'guard01/child.log').splitlines()]
    names = [f'annealing-{n:02}' for n in range(4, 49, 4)] + ['checkpoint01', 'checkpoint02']
    require(len(lines) == 15 and lines[-1] == {'result': result}, 'raw log/result join')
    require(set(result['checkpoints']) == set(names), 'checkpoint set')
    checkpoints = {}
    for name, logged in zip(names, lines[:-1], strict=True):
        receipt = read(HERE / (name + '-receipt.json'))
        require(receipt == result['checkpoints'][name]
                and logged == {'checkpoint': name, **receipt}, 'checkpoint receipt/log join')
        directory = HERE / name
        outer = read(directory / 'manifest.json')
        require(sha(directory / 'manifest.json') == receipt['manifest_sha256'], 'outer hash')
        require(sha(directory / 'annealing/manifest.json') == outer['annealing_sha256'], 'annealing join')
        ann = read(directory / 'annealing/manifest.json')
        require(outer['phase'] == receipt['phase']
                and ann['iterations'] == receipt['annealing_iterations'], 'phase/iteration join')
        for field, entry in ann['files'].items():
            require((directory / 'annealing' / (field + '.npy')).stat().st_size == entry['bytes'], 'array extent')
        hard = None
        if outer['hardening_sha256'] is not None:
            require(sha(directory / 'hardening/manifest.json') == outer['hardening_sha256'], 'hardening join')
            hard = read(directory / 'hardening/manifest.json')
            require(hard['input_sha256'] == outer['matrix_sha256'] == result['soft_matrix_sha256'], 'matrix identity join')
            require((directory / 'hardening/order.npy').stat().st_size == hard['order_bytes'], 'rank extent')
        files = [p for p in directory.rglob('*') if p.is_file()]
        require(all(not p.is_symlink() for p in files), 'checkpoint symlink')
        extents = {str(p.relative_to(directory)): p.stat().st_size for p in files}
        expected_members = {'manifest.json', 'annealing/manifest.json',
                            'annealing/V.npy', 'annealing/M.npy', 'annealing/Q.npy'}
        if hard is not None:
            expected_members |= {'hardening/manifest.json', 'hardening/order.npy'}
        require(set(extents) == expected_members, 'checkpoint member denominator')
        require(sum(extents.values()) == receipt['logical_bytes'] <= 128 * 1024**2,
                'logical extent join or per-checkpoint limit')
        if name.startswith('annealing-'):
            require(outer['phase'] == 'annealing' and hard is None, 'intermediate phase')
        if name == 'checkpoint02':
            require(outer['phase'] == 'done' and ann['phase'] == 'done'
                    and ann['iterations'] == 48 and hard is not None
                    and hard['phase'] == 'done'
                    and hard['cursor'] == result['hardening_entries_scanned']
                    and 0 < hard['cursor'] <= 4_000_000
                    and len(hard['pairs']) == result['selected_pairs'], 'final state joins')
        checkpoints[name] = dict(metadata_hashes={str(p.relative_to(directory)): sha(p) for p in files if p.suffix == '.json'},
                                 file_extents=extents, iterations=ann['iterations'], phase=outer['phase'],
                                 selected_pairs=None if hard is None else len(hard['pairs']),
                                 cursor=None if hard is None else hard['cursor'])
    hard = read(HERE / 'checkpoint02/hardening/manifest.json')
    pairs = hard['pairs']
    require(len(pairs) == 2000 and sorted(p[0] for p in pairs) == list(range(2000))
            and sorted(p[1] for p in pairs) == list(range(2000)), 'complete bijection')
    permutation = dict(pairs)
    conserved = sum(permutation[i+1] == permutation[i]+1 for i in range(1999))
    expected = (conserved / (2 * 1999) + 1) / 2
    require(result['conserved_directed_chain_edges'] == conserved
            and abs(result['score'] - expected) <= 1e-12
            and abs(result['independent_chain_score'] - expected) <= 1e-12, 'independent objective')
    require(result['matching_iterations'] == 48 and result['annealing_calls'] == 49
            and result['annealing_operations'] == 195820096
            and result['edge_pair_updates'] == 191808048, 'full schedule counters')
    require(result['selected_pairs'] == 2000 and result['final_mapping_explicitly_closed'] is True,
            'worker finalization evidence')
    total = sum(r['logical_bytes'] for r in result['checkpoints'].values())
    require(total == result['total_checkpoint_logical_bytes'] and total <= 2 * 1024**3, 'total checkpoint extent')
    evidence_names = ['bindings.json', 'REVIEW.md', 'LIVE_REVIEW.md', 'preflight01.json',
                      'owner-observation01.json', 'started.json', 'result.json',
                      'guard01/final.json', 'guard01/child.log', 'guard01/child_exit.json', 'reconcile.py']
    record = dict(at=datetime.now(timezone.utc).isoformat(), source=SOURCE,
                  bindings_verified=len(bindings), evidence={p: sha(HERE / p) for p in evidence_names},
                  exact_owner_and_cgroup_absent=True, owner=owner,
                  guard_summary={k: final[k] for k in ('elapsed_seconds', 'peak_sampled_memory_current_bytes', 'memory_events', 'child_exit_code', 'cleanup_verified')},
                  checkpoints=checkpoints, conserved_edges_from_metadata=conserved,
                  objective_from_metadata=expected, total_checkpoint_logical_bytes=total,
                  qualification='Compact metadata and stat reconciliation only. NPY hashes/restores and mapping closure are guarded-worker evidence. No algorithm repetition, real-hub, full-pipeline, GPU, financial or controlled-speedup claim.')
    with (HERE / 'closure01.json').open('x') as file:
        json.dump(record, file, indent=2); file.write('\n'); file.flush(); os.fsync(file.fileno())
    print(json.dumps({'closure': 'complete', 'bindings': len(bindings), 'conserved_edges': conserved, 'score': expected, 'checkpoint_bytes': total}))


if __name__ == '__main__':
    main()
