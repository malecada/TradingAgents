"""Bind actual public inputs and the reviewed successor caller; no run."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
F = HERE.parent
ENTRY = F/'real-data-pilot-full24-entry01-2026-10-09'
INPUT = F/'real-data-pilot-full24-input-binding01-2026-10-09'
TRANSPORT = F/'real-data-pilot-full24-transport-binding01-2026-10-09'
REVIEW = F/'real-data-pilot-full24-final-entry-review01-2026-10-09'
NAME = 'eth-paper-real-data-end-to-end-resource-20261009-24'


def load(path):
    return json.loads(path.read_bytes())


def ref(path):
    body = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)),
            'sha256': hashlib.sha256(body).hexdigest()}


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


# Preserve the first declaration; the reviewed successor uses this exact name.
original = load(HERE/'CAPACITY_DECLARATION01.json')
capacity = copy.deepcopy(original)
capacity['source_body_pins'] = capacity.pop('source_pins')
assert len(capacity['source_body_pins']) == 365
save(HERE/'CAPACITY_DECLARATION02.json', capacity)
save(HERE/'CAPACITY_FIELD_CORRECTION01.json', {
    'original': ref(HERE/'CAPACITY_DECLARATION01.json'),
    'successor': ref(HERE/'CAPACITY_DECLARATION02.json'),
    'change': 'Rename source_pins to actual preflight24_02 source_body_pins; every value, numeric budget, policy, timestamp and qualification is unchanged.',
    'claim': False})
gate = load(HERE/'gate-DRAFT01.json')
experiment = gate['experiments'][NAME]
inputs = load(HERE/'ALL_INPUT_REFS01.json')
assert len(inputs) == 64
experiment['inputs'] = inputs
experiment['charter'] = ref(HERE/'CHARTER01.md')
for path in (ENTRY/'preflight24_02.py', ENTRY/'root_io24_02.py',
             ENTRY/'MANIFEST02.json', HERE/'CHARTER01.md',
             HERE/'CAPACITY_DECLARATION02.json', HERE/'MATCHING_SCRATCH_RESERVATION01.json',
             F/'real-data-pilot-index-capacity02-2026-10-08/candidate/index_capacity.py',
             F/'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py'):
    r = ref(path)
    experiment['source_files'][r['path']] = r['sha256']
for path, pin in experiment['source_files'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == pin, path
assert experiment['parent'] == 'eth-paper-real-data-end-to-end-resource-20261009-23'
assert not (ROOT/'research_runs'/NAME).exists()
save(ENTRY/'gate01.json', gate)
bound = load(TRANSPORT/'BOUND01.json')
private = bound['private_input']['archive_transport']
assert private['path'] == inputs['archive_transport']['path']
assert private['sha256'] == inputs['archive_transport']['sha256']
binding = {
    'schema_version': 1, 'identity': NAME,
    'status': 'ACTUAL_ENTRY_DRAFT_NOT_RELEASED',
    'gate': ref(ENTRY/'gate01.json'),
    'core_manifest': ref(INPUT/'CORE_MANIFEST03.json'),
    'public_manifest': ref(INPUT/'PUBLIC_MANIFEST04.json'),
    'public_refs': ref(INPUT/'PUBLIC_INPUT_REFS04.json'),
    'capacity_observation': ref(HERE/'CAPACITY_DECLARATION02.json'),
    'transport': private,
    'binding_review': None,
    'transport_binding': ref(TRANSPORT/'BOUND01.json'),
    'preparation': ref(TRANSPORT/'PREPARED01.json'),
    'unbound_archive': ref(TRANSPORT/'UNBOUND_ARCHIVE01.json'),
    'budget_review': ref(F/'mcm-batched-full-pilot-allocation-review01-2026-10-09/EXTENSION95_REVIEW01.json'),
    'prior_outcome_review': ref(F/'real-data-pilot-outcome23-review01-2026-10-09/OUTCOME_REVIEW01.json'),
    'prior_preservation_complete': ref(F/'real-data-pilot-twentythird-failed-increment01-2026-10-09/FRESH_GIT_RECOVERY01.json'),
    'prior_recovery_review': ref(F/'real-data-pilot-outcome23-review01-2026-10-09/returned-git-recovery01/RECOVERY_REVIEW01.json'),
    'transport_source_review': ref(REVIEW/'TRANSPORT_REVIEW01.json'),
    'capacity_source_review': ref(F/'mcm-batched-grouped-capacity-review01-2026-10-09/SOURCE_REVIEW01.json'),
    'currentness_sample': ref(F/'real-data-pilot-full24-currentness01-2026-10-09/RESULT01.json'),
    'remote_storage_sample': ref(HERE/'REMOTE_STORAGE_CHECK01.json'),
    'input_refs': {role: {k: value[k] for k in ('path', 'sha256')}
                   for role, value in inputs.items()}}
save(ENTRY/'BINDING_DRAFT01.json', binding)
save(HERE/'ENTRY_PREPARATION01.json', {
    'status': 'ACTUAL_GATE_AND_BINDING_DRAFT_NOT_RELEASED',
    'gate': ref(ENTRY/'gate01.json'), 'binding_draft': ref(ENTRY/'BINDING_DRAFT01.json'),
    'source_count': len(experiment['source_files']), 'input_count': len(inputs),
    'opaque_input': private, 'claim': False, 'launch': False,
    'qualification': 'No genuine admission, cumulative allowance adoption, empirical claim or native execution. Exact independent entry/binding review, committed availability, actual incremental external recovery and fresh live eligibility remain required.'})
print(json.dumps({'status': 'ACTUAL_ENTRY_DRAFT_NOT_RELEASED',
    'source_count': len(experiment['source_files']), 'input_count': len(inputs),
    'claim': False, 'launch': False}))
