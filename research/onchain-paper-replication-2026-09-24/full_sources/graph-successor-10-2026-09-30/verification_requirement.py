"""Verify retained completed package suite without rerunning any computation."""
from pathlib import Path
import hashlib
import json
import subprocess


def verify(root):
    root = Path(root)
    directory = root/'research/onchain-paper-replication-2026-09-24/full_sources/matching-package-integration-2026-09-30'
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    closure = json.loads((directory/'closure01.json').read_bytes())
    bindings_path = directory/'source-bindings.json'
    bindings = json.loads(bindings_path.read_bytes())
    source = closure['source_commit']
    for name, expected in closure['evidence'].items():
        if sha(root/name) != expected:
            raise ValueError('verification evidence changed: '+name)
    if subprocess.check_output(['git', 'show', source+':'+str(bindings_path.relative_to(root))]) != bindings_path.read_bytes():
        raise ValueError('verification manifest differs from tested commit')
    for name, expected in bindings['files'].items():
        if sha(root/name) != expected:
            raise ValueError('tested current source changed: '+name)
        if hashlib.sha256(subprocess.check_output(['git', 'show', source+':'+name])).hexdigest() != expected:
            raise ValueError('tested committed source differs: '+name)
    final = json.loads((directory/'offline01/final.json').read_bytes())
    child = json.loads((directory/'offline01/child_exit.json').read_bytes())
    dispatch = json.loads((directory/'dispatch01.json').read_bytes())
    expected_owner = {'kind': 'matching-package-offline01', 'source_commit': source,
                      'bindings_sha256': sha(bindings_path)}
    if final['owner_identity'] != expected_owner or dispatch['source_commit'] != source:
        raise ValueError('verification owner differs')
    if final['phase'] != 'complete' or final['child_exit_code'] != 0 or child['exit_code'] != 0 or final['cleanup_verified'] is not True or final['limit_reason'] is not None:
        raise ValueError('verification not complete and clean')
    if any(final['memory_events'][k] != 0 for k in ('max', 'oom', 'oom_kill')) or final['memory_events'] != child['terminal_memory_snapshot']['memory_events']:
        raise ValueError('verification resource failure')
    if any(path.exists() for path in (Path(final['cgroup']), Path('/proc', str(final['monitor_pid'])), Path('/proc', str(child['workload_pid'])))):
        raise ValueError('verification owner not absent')
    if closure['status'] != 'complete' or closure['current_and_committed_bindings'] != len(bindings['files']) or len(bindings['files']) != 178:
        raise ValueError('verification closure denominator differs')
    counts = {'standard_passes': 2774, 'subtests_passed': 97, 'neural_passes': 785, 'total_passes': 3559, 'skipped': 2}
    if any(closure[k] != v for k, v in counts.items()):
        raise ValueError('verification test counts differ')
    log = (directory/'offline01/child.log').read_text()
    if '2774 passed, 97 subtests passed in 1059.65s' not in log or '785 passed, 2 skipped in 520.74s' not in log:
        raise ValueError('verification raw summaries differ')
    review = directory/'CLOSURE_REVIEW.md'
    if not review.is_file():
        raise ValueError('independent closure review missing')
    return {'verification_source': source, 'verified_bindings': len(bindings['files']),
            'closure_sha256': sha(directory/'closure01.json'), 'review_sha256': sha(review),
            'bindings_sha256': sha(bindings_path), 'final_sha256': sha(directory/'offline01/final.json'),
            'memory_high_events': final['memory_events']['high'], **counts,
            'qualification': 'Saved named offline verification only; no test, empirical body read or fit rerun.'}
