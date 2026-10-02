"""Assemble nonexecutable gate metadata while implementation review continues."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
ORIGINAL = OUT.parent
PREVIOUS = ORIGINAL / 'revision02'


def read(path):
    return json.loads(path.read_bytes())


def pin(path):
    return {'path': str(path.relative_to(ROOT)),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def verify(record):
    path = ROOT / record['path']
    assert pin(path)['sha256'] == record['sha256'], str(path)


def save(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


bindings = read(PREVIOUS / 'bindings01.json')
identity = bindings['experiment_id']
for path in (ROOT / 'research_runs' / identity,
             ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/runs' / identity,
             ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/sources' / identity):
    assert not path.exists() and not path.is_symlink()
for key in ('environment', 'execution_workspace', 'parent_experiment', 'parent_claim',
            'parent_terminal', 'allocation'):
    verify(bindings[key])
for ref in bindings['cumulative_budget_extension'].values():
    verify(ref)

policy = {'schema_version': 1, 'max_file_bytes': 8 * 1024**2,
          'max_json_bytes': 256 * 1024, 'max_allocated_bytes': 160 * 1024**2,
          'max_logical_bytes': 128 * 1024**2, 'max_entries': 128,
          'tail_reserve_bytes': 32 * 1024**2}
job = read(ORIGINAL / 'execution-job.draft.json')
job['resources']['physical_policy'] = policy
save('execution-job.candidate.json', job)

charter = (ORIGINAL / 'CHARTER.draft.md').read_text()
charter = charter.replace('# Neural-only capacity measurement — unadopted charter',
                          '# Neural-only capacity measurement — candidate charter')
charter = charter.replace('Neither an experiment identity nor a launch is reserved.',
    'The designated first adopter is eth-paper-neural-resource-20261002-01. Its\nidentity is specified in reviewed budget metadata; no namespace or launch is reserved.')
charter += '''

## Explicit physical route and remaining release conditions

This candidate selects the proposed version1 physical policy:8MiB per regular
file,256KiB per encoded JSON object,160MiB allocated and128MiB logical across the
exact three owned roots,128 entries and32MiB reserved for failure/terminal tail.
The active logical allowance is96MiB. The existing4MiB checkpoint and64MiB
producer/output limits remain additional limits. These are finite refusal
ceilings, not measured successful peaks or a kernel aggregate filesystem quota.
Independent source/limit review and measured synthetic control overhead remain
required before these proposed values can be admitted.

The selected route must bind the original live authority through the supervisor,
guard, worker and final observer. Root/claim births are established by that
authority, with bounded local messages and no mutable-disk recovery baseline.
If original authority is lost, mutations are refused and the attempt remains
spent; no automatic relaunch or namespace recreation is permitted. Missing or
ambiguous terminal closure requires independent reconciliation, never presumed
successful coverage. Library temporary/cache paths must be explicitly bound to
accounted control subdirectories before imports, with worker readback. This is
configured scratch containment, not a sandbox for arbitrary hostile file writes.
All three canonical parent scaffolds must already exist. Guard and observer final
writes, including failure records, are part of the reserved physical denominator.

The10GiB free-space floor follows the user's separately authorized instruction;
old20GiB profiles and all historical attempts remain unchanged. No input or old
output deletion is authorized. The reviewed cumulative extension preserves33
spent claims and allocates12 body,15 financial,1 neural resource and1 remaining
resource claim. This job uses only the neural resource slot. The unchanged1,420
financial fits receive no credit here. Category allocations require explicit
review even though the budget parser primarily enforces the cumulative ceiling.

The runtime/environment/workspace and immutable original parent bindings are
prepared. Final exact committed source/runtime closure, accepted corrected
physical code, kernel/file-limit smoke evidence, whole-job storage accounting,
independent final gate review, fresh unchanged-input checks and startup RAM/guard
readback remain release conditions. This candidate invokes none of them and is
not executable while source/runtime fields are null.
'''
with (OUT / 'CHARTER.candidate.md').open('x') as stream:
    stream.write(charter)

original = read(ORIGINAL / 'gate-template.draft.json')
gate = deepcopy(original['registry_template'])
experiment = deepcopy(original['experiment_template'])
experiment['charter'] = pin(OUT / 'CHARTER.candidate.md')
experiment['cumulative_budget_extension'] = bindings['cumulative_budget_extension']
for name, record in (('environment', bindings['environment']),
                     ('execution_workspace', bindings['execution_workspace']),
                     ('execution_job', pin(OUT / 'execution-job.candidate.json'))):
    experiment['inputs'][name] = {**record, 'dataset': 'eth'}

# Keep every original compact provenance pin, deduplicating only identical paths.
provenance = read(ORIGINAL / 'provenance-bindings.draft.json')
paths = {item['path']: item['sha256'] for item in experiment['inputs'].values()}
for index, record in enumerate(provenance['metadata_bindings']):
    verify(record)
    if record['path'] in paths:
        assert paths[record['path']] == record['sha256']
    else:
        experiment['inputs'][f'provenance_{index:02d}'] = {
            'path': record['path'], 'sha256': record['sha256'], 'dataset': 'eth'}
        paths[record['path']] = record['sha256']
assert len(provenance['metadata_bindings']) == 43
for proof in provenance['graph_proofs']:
    assert paths[proof['verification']] == proof['sha256']
parent = read(PREVIOUS / 'parent-experiment.json')
assert parent == read(ROOT / bindings['parent_claim']['path'])['experiment']
gate['experiments'] = {bindings['parent']: parent, identity: experiment}
assert experiment['source_files'] is None and experiment['runtime_hashes'] is None
assert len(experiment['cells']) == 9 and len(experiment['windows']) == 9
assert all(item['sha256'] is not None for item in experiment['inputs'].values())
save('gate-candidate.NONEXECUTABLE.json', {
    'execution_admitted': False, 'namespace_reserved': False,
    'status': 'NONEXECUTABLE_PENDING_SOURCE_PHYSICAL_AND_FINAL_REVIEW',
    'experiment_id': identity, 'registry_candidate': gate,
    'required_source_pins': [experiment['charter'],
                             *bindings['cumulative_budget_extension'].values(),
                             bindings['allocation']],
    'unresolved': ['accepted corrected source and complete committed closure',
                   'final runtime hashes', 'physical policy and whole-job accounting acceptance',
                   'kernel/file-limit and final release review',
                   'fresh source/input/admission/host/guard checks'],
    'qualification': 'Explicit invalid wrapper and null source/runtime prevent full admission. Input metadata hashes do not prove unchanged numerical body bytes.'})
save('preparation01.json', {
    'execution_admitted': False, 'namespace_reserved': False,
    'candidate': pin(OUT / 'gate-candidate.NONEXECUTABLE.json'),
    'charter': pin(OUT / 'CHARTER.candidate.md'),
    'job': pin(OUT / 'execution-job.candidate.json'),
    'cell_count': 9, 'window_count': 9,
    'input_count': len(experiment['inputs']),
    'original_metadata_pins_preserved': 43, 'graph_proof_pins_preserved': 9,
    'physical_limits_adopted': False, 'models_or_arrays_executed': False})
print('PASS: nine-cell candidate assembled with original parent, accepted budget, all43 metadata pins/nine graph proofs and explicit physical limits; source/runtime unset; no admission or namespace reservation.')
