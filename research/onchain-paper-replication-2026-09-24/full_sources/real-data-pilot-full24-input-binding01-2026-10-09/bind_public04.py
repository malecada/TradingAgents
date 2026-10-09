"""Join concrete public inputs and descriptors. Opaque transport stays unbound."""
import copy
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
F = HERE.parent
OLD = F / 'real-data-pilot-final23-2026-10-09'
NAME = 'eth-paper-real-data-end-to-end-resource-20261009-24'
OLD_NAME = 'eth-paper-real-data-end-to-end-resource-20261009-23'


def load(path):
    return json.loads(path.read_bytes())


def raw(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('xb') as out:
        out.write(raw(value))


assert not (ROOT / 'research_runs' / NAME).exists()
gate = load(OLD / 'gate03.json')
entry = gate['experiments'][OLD_NAME]


def public(role):
    assert role in {'execution_job','pilot','producer_plan','resource_population_plan','archive_policy','pair_policy','original_import'}
    ref = entry['inputs'][role]
    path = ROOT / ref['path']
    assert sha(path) == ref['sha256']
    return load(path)


core = load(HERE / 'CORE_MANIFEST03.json')
docs = {}
for role, ref in core['inputs'].items():
    assert sha(ROOT / ref['path']) == ref['sha256']
    docs[role] = load(ROOT / ref['path'])
for role in ('execution_job','pilot','producer_plan','resource_population_plan','archive_policy','pair_policy','original_import'):
    docs[role] = public(role)
job, pilot, plan = (docs[x] for x in ('execution_job','pilot','producer_plan'))
resource = job['resources']
budget = resource['storage_budget']
assert budget['limits']['max_logical_bytes'] == 16*1024**3
assert budget['limits']['max_allocated_bytes'] == 20*1024**3
budget['experiment'] = NAME
budget['roots'][1] = str(ROOT / 'research_runs' / NAME)
pilot['resource_policy'] = copy.deepcopy(resource)
pilot.pop('partial_progress', None)
pilot.pop('scoring_diagnostic', None)
pilot['outputs'].pop('diagnostic', None)
pilot['cell_id'] = 'real-eth-seven-graph-joint-update-resource24'
assert pilot['seed'] == 11 and pilot['batch_size'] == 16 and pilot['lookback_days'] == 28
assert len(pilot['graph_inputs']) == 7
docs['archive_policy']['remote_namespace'] = 'ethpilot-20261009-24'
pair = docs['pair_policy']
anchor = subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip()
pins = {path:sha(ROOT/path) for path in pair['numerical_source']['files']}
pair['numerical_source'] = {'commit':anchor, 'files':pins}
selected = job['payload']['representation_jobs']['original32']
item = plan['producers'][selected['producer']]
for value in (selected, item):
    descriptor = value['descriptor']
    for key, role in (('compact_execution','compact_policy'),
                      ('compact_archive_execution','archive_policy'),
                      ('pair_execution','pair_policy')):
        descriptor[key]['policy_sha256'] = hashlib.sha256(raw(docs[role])).hexdigest()
    assert descriptor['original_dictionary_import']['sha256'] == entry['inputs']['original_import']['sha256']
    assert descriptor['original_dictionary_stage']['sha256'] == entry['inputs']['original_import_stage']['sha256']
    assert descriptor['required_graphs'] == sorted(pilot['graph_inputs'])
    assert descriptor['configs']['dictionary']['sample_count'] == 512
    assert descriptor['configs']['dictionary']['size'] == 32
# Complete public transport template; the reviewed opaque binder alone supplies
# the existing connection. No credential or prior private transport is decoded.
limits = load(HERE / 'TRANSPORT_LIMITS03.json')
docs['archive_transport'] = dict(limits, schema_version=2,
    format='archive-dispatch-v1', typed_payload_input='typed_payload', connection=None)
destination = HERE / 'public04'
destination.mkdir(exist_ok=False)
for role, value in docs.items():
    save(destination / (role + '.json'), value)
refs = copy.deepcopy(entry['inputs'])
for role in docs:
    path = destination / (role + '.json')
    refs[role] = {'path':str(path.relative_to(ROOT)), 'sha256':sha(path), 'dataset':'eth'}
source_pins = load(F/'mcm-batched-pilot-input-templates02-2026-10-09/draft02/SOURCE_PINS.json')['value']
assert all(sha(ROOT/path) == digest for path,digest in source_pins.items())
save(HERE / 'PUBLIC_INPUT_REFS04.json', refs)
save(HERE / 'PUBLIC_MANIFEST04.json', {
    'status':'PUBLIC_INPUTS_BOUND_OPAQUE_TRANSPORT_PENDING_NOT_RELEASED',
    'experiment':NAME, 'full_pilot_cell':pilot['cell_id'], 'source_anchor':anchor,
    'public_input_count':len(docs), 'all_input_roles':len(refs),
    'source_pins':source_pins, 'builder_sha256':sha(Path(__file__)),
    'public_inputs':{role:refs[role] for role in docs},
    'model_training_original_refs':{role:entry['inputs'][role] for role in ('model','training')},
    'unchanged_genuine_import_refs':{role:entry['inputs'][role] for role in ('original_import','original_import_stage')},
    'qualification':'Public metadata bound only. Transport template connection=None is deliberately invalid until the accepted opaque binder supplies its actual connection and source request. Final registry, currentness/resource/namespace, whole preservation and exact release remain required.',
    'claim':False, 'launch':False})
print(json.dumps({'status':'PUBLIC_INPUTS_BOUND_OPAQUE_TRANSPORT_PENDING_NOT_RELEASED',
                  'public_inputs':len(docs), 'all_roles':len(refs), 'claim':False}))
