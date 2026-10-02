"""Freeze the reviewed successor metadata; no admission or empirical execution."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PARENT = HERE.parent
DRAFT = PARENT / 'neural-pressure-successor-preparation-2026-10-02'
PHASE = PARENT / 'neural-phase-integration-preparation02-2026-10-02'
IDENTITY = 'eth-paper-neural-resource-20261002-03'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    assert sha(HERE / 'REVIEW_SOURCE01.md') == '19ee3d5f23f9970f8f88816b18c89b9c503af20d711b072d56694c2fe9c2893d'
    assert sha(PHASE / 'REMOTE_RECOVERY01.json') == 'd585230841e7bee5f3854ead927ffac51f0372e70468484cc21a1c5a32a5c53a'
    manifest = json.loads((HERE / 'source-manifest01.json').read_bytes())
    for name, expected in {**manifest['dynamic_source_files'], **manifest['refs']}.items():
        assert sha(ROOT / name) == expected, name
    for prefix in ('research_runs', 'research_artifacts/onchain-paper-replication-2026-09-24/runs',
                   'research_artifacts/onchain-paper-replication-2026-09-24/sources'):
        assert not os.path.lexists(ROOT / prefix / IDENTITY)
    gate = copy.deepcopy(json.loads((DRAFT / 'gate.draft.json').read_bytes()))
    selected = gate['experiments'][IDENTITY]
    selected['charter'] = pin(HERE / 'CHARTER.md')
    for name, filename in [('execution_job', 'execution-job.json'), ('launch_scheduling', 'launch_scheduling.json'),
                           ('resource_amendment', 'resource-amendment.json')]:
        selected['inputs'][name] = {**pin(HERE / filename), 'dataset': 'eth'}
    references = {
        'accepted_phase_integration_proof': PHASE / 'execution-result01.json',
        'accepted_phase_integration_review': PHASE / 'REVIEW_EXECUTION01.md',
        'phase_retention_addendum': PHASE / 'RETENTION_ADDENDUM01.json',
        'phase_remote_recovery': PHASE / 'REMOTE_RECOVERY01.json',
        'accepted_storage_observation_review': PARENT / 'storage-publication-observation-2026-10-02/REVIEW_CANDIDATE03.md',
        'final_source_release_review': HERE / 'REVIEW_SOURCE01.md',
        'final_source_manifest': HERE / 'source-manifest01.json',
        'final_phase_integration': HERE / 'INTEGRATION01.json',
        'accepted_budget_allocation': DRAFT / 'allocation.json',
        'accepted_budget_review_report': DRAFT / 'REVIEW_BUDGET01.md',
    }
    for name, path in references.items():
        selected['inputs'][name] = {**pin(path), 'dataset': 'eth'}
    selected['cumulative_budget_extension'] = {
        'extension': pin(DRAFT / 'extension.json'),
        'review': pin(DRAFT / 'review.accepted01.json'),
    }
    assert selected['cumulative_budget_extension']['extension']['sha256'] == '3cc6e3eb8bf4b12d5d5efce5f03c108000b8a739eeda4e5f5b1431d071199a53'
    assert selected['cumulative_budget_extension']['review']['sha256'] == '948c4fd7f015d35ff4f3751db36b0e7530e52d1268780eac14abea08e09b8c73'
    paths = sorted(list((ROOT / 'tradingagents/research/onchain_replication').glob('*.py'))
                   + list((ROOT / 'tradingagents/research').glob('*.py')) + [ROOT / 'tradingagents/__init__.py'])
    assert len(paths) == manifest['dynamic_python_count'] == 133
    selected['source_files'] = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    selected['runtime_hashes'] = dict(manifest['runtime_hashes'])
    extra = [HERE / name for name in ('CHARTER.md', 'resource-amendment.json', 'execution-job.json',
             'launch_scheduling.json', 'readiness.py', 'launch_once.py', 'source-manifest01.json',
             'INTEGRATION01.json', 'REVIEW_SOURCE01.md', 'prepare_gate01.py')]
    extra += list(references.values())
    for item in selected['inputs'].values():
        path = ROOT / item['path']
        assert sha(path) == item['sha256'], item['path']
        if subprocess.run(['git', 'ls-files', '--error-unmatch', '--', item['path']],
                          cwd=ROOT, capture_output=True).returncode == 0:
            extra.append(path)
    for path in extra:
        selected['source_files'][str(path.relative_to(ROOT))] = sha(path)
    ancestor = selected['parent']
    ancestry = []
    while ancestor is not None:
        actual = json.loads((ROOT / 'research_runs' / ancestor / 'claim.json').read_bytes())['experiment']
        assert gate['experiments'][ancestor] == actual
        ancestry.append(ancestor)
        ancestor = actual['parent']
    assert len(ancestry) == 3 and len(selected['cells']) == len(selected['windows']) == 9
    save(HERE / 'gate.json', gate)
    source = '0' * 40
    claim = {
        'schema_version': 1, 'program_id': gate['program_id'], 'experiment_id': IDENTITY,
        'started_at': '2026-10-02T23:59:59.123456+00:00', 'source': source,
        'registration': str((HERE / 'gate.json').relative_to(ROOT)),
        'registration_sha256': sha(HERE / 'gate.json'), 'design_source': source,
        'bindings': None, 'bindings_sha256': None, 'inputs': selected['inputs'],
        'family': gate['families'][selected['family']], 'experiment': selected,
        'effective_attempt_budget': 63,
        'windows': [{**window, 'identity': gate['datasets'][window['dataset']]['identity'], 'state': 'exposed'}
                    for window in selected['windows']],
        'prior_exposures': [{**exposure, 'identity': dataset['identity']}
                           for dataset in gate['datasets'].values() for exposure in dataset['exposures']],
    }
    encode = lambda value: (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    claim_bytes = len(encode(claim))
    rpc_bytes = len(encode({'anchor_sha256': '0' * 64, 'op': 'claim', 'value': claim}))
    assert max(claim_bytes, rpc_bytes) <= 262144
    save(HERE / 'preparation01.json', {
        'status': 'FINAL_GATE_REVIEW_REQUIRED_NOT_ADMITTED', 'identity': IDENTITY,
        'gate': pin(HERE / 'gate.json'), 'charter': pin(HERE / 'CHARTER.md'),
        'resource_amendment': pin(HERE / 'resource-amendment.json'),
        'dynamic_python_count': len(paths), 'source_pin_count': len(selected['source_files']),
        'input_count': len(selected['inputs']), 'runtime_count': len(selected['runtime_hashes']),
        'ancestry': ancestry, 'claim_preview_bytes': claim_bytes, 'rpc_preview_bytes': rpc_bytes,
        'json_limit_bytes': 262144, 'proposed_effective_budget': 63, 'spent': 34,
        'qualification': 'Metadata-only assembly and conservative full claim/RPC preview. Actual committed-HEAD admission and exact shape must pass before launch; source-only review is not a final gate review. No numerical input, namespace reservation or job execution.',
    })
    print(json.dumps({'gate_sha256': sha(HERE / 'gate.json'), 'source_pin_count': len(selected['source_files']),
                      'input_count': len(selected['inputs']), 'claim_preview_bytes': claim_bytes,
                      'rpc_preview_bytes': rpc_bytes, 'empirical_execution': False}))


if __name__ == '__main__':
    main()
