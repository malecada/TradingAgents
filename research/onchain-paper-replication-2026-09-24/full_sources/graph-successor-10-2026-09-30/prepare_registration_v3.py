"""Append verified source closure once; never execute or reopen a graph job."""
from pathlib import Path
import copy
import hashlib
import json
from verification_requirement import verify

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
NAME = 'eth-paper-graph-resource-20260930-10'
PACKAGE = ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/matching-package-integration-2026-09-30'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    for path in (HERE/'gate-v3.json', HERE/'gate-v3-derivation.json',
                 ROOT/'research_runs'/NAME,
                 ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME,
                 ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME):
        if path.exists() or path.is_symlink():
            raise FileExistsError('reserved or generated identity: '+str(path))
    proof = verify(ROOT)
    original = json.loads((HERE/'gate-v2.json').read_bytes())
    gate = copy.deepcopy(original)
    experiment = gate['experiments'][NAME]
    for name, expected in experiment['source_files'].items():
        if sha(ROOT/name) != expected:
            raise ValueError('old source pin changed: '+name)
    for item in experiment['inputs'].values():
        if sha(ROOT/item['path']) != item['sha256']:
            raise ValueError('old input changed: '+item['path'])
    derivation = json.loads((PACKAGE/'package-derivation.json').read_bytes())
    for name, record in derivation.items():
        if sha(ROOT/name) != record['new_sha256']:
            raise ValueError('reviewed package source differs: '+name)
        experiment['source_files'][name] = record['new_sha256']
    for name in ('preflight03.py', 'verification_requirement.py',
                 'prepare_registration_v3.py', 'PRELAUNCH_ROUTE_V3.md'):
        path = HERE/name
        experiment['source_files'][str(path.relative_to(ROOT))] = sha(path)
    refs = {'prelaunch_v3_prior_gate': HERE/'gate-v2.json',
            'prelaunch_v3_amendment': HERE/'PRELAUNCH_ROUTE_V3.md'}
    for name in ('source-bindings.json', 'dispatch01.json', 'closure01.json',
                 'PACKAGE_REVIEW.md', 'OFFLINE_RELEASE_REVIEW.md', 'LIVE_REVIEW.md',
                 'CLOSURE_REVIEW.md', 'offline01/final.json', 'offline01/child_exit.json',
                 'offline01/child.log'):
        refs['package_verification_'+name.replace('/', '_').replace('.', '_')] = PACKAGE/name
    for name, path in refs.items():
        if name in experiment['inputs']:
            raise ValueError('input name reused')
        experiment['inputs'][name] = {**reference(path), 'dataset': 'eth'}
    from tradingagents.research.onchain_replication.job import required_sources
    if not required_sources() <= set(experiment['source_files']):
        raise ValueError('required source closure incomplete')
    for name, old in original['experiments'].items():
        if name != NAME and gate['experiments'][name] != old:
            raise ValueError('inherited experiment changed')
    if {k:v for k,v in experiment.items() if k not in ('inputs', 'source_files')} != {k:v for k,v in original['experiments'][NAME].items() if k not in ('inputs', 'source_files')}:
        raise ValueError('scientific or budget fields changed')
    write(HERE/'gate-v3.json', gate)
    write(HERE/'gate-v3-derivation.json', {'original_gate': reference(HERE/'gate-v2.json'),
        'new_gate': reference(HERE/'gate-v3.json'), 'experiment': NAME,
        'inherited_experiments_unchanged': len(gate['experiments'])-1,
        'source_pins': len(experiment['source_files']), 'input_pins': len(experiment['inputs']),
        'added_source_pins': sorted(set(experiment['source_files'])-set(original['experiments'][NAME]['source_files'])),
        'added_inputs': sorted(refs), 'package_verification': proof,
        'qualification': 'Source closure preparation only; no admission, budget adoption, temp check or graph launch.'})
    print(json.dumps({'source_pins': len(experiment['source_files']), 'input_pins': len(experiment['inputs']),
                      'gate_sha256': sha(HERE/'gate-v3.json')}))
