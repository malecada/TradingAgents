"""Prepare the fixed successor's public inputs; no numerical work or authority."""
import copy
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
F = HERE.parent
OLD = 'eth-paper-real-data-end-to-end-resource-20261009-25'
NEW = 'eth-paper-real-data-end-to-end-resource-20261009-26'
OLD_CELL = 'real-eth-seven-graph-joint-update-resource25'
NEW_CELL = 'real-eth-seven-graph-joint-update-resource26'


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'))+'\n').encode()


def save(path, value):
    with path.open('xb') as stream:
        stream.write(raw(value))
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
            'bytes': path.stat().st_size}


def move(value):
    if type(value) is dict:
        return {move(k): move(v) for k, v in value.items()}
    if type(value) is list:
        return [move(v) for v in value]
    if type(value) is str:
        return value.replace(OLD, NEW).replace(OLD_CELL, NEW_CELL).replace(
            'ethpilot-20261009-25', 'ethpilot-20261009-26')
    return value


assert not (ROOT/'research_runs'/NEW).exists()
prior_entry = F/'real-data-pilot-full25-entry01-2026-10-09'
binding = load(prior_entry/'BINDING01.json')
prepared = load(ROOT/binding['preparation']['path'])
prior_public = load(ROOT/binding['public_manifest']['path'])
docs = move(copy.deepcopy(prepared['builder03_result']['inputs']))
docs['archive_policy'] = move(load(ROOT/binding['unbound_archive']['path']))
policy_draft = F/'real-data-pilot-full26-numerical-policy01-2026-10-09/pair_policy-DRAFT01.json'
docs['pair_policy'] = load(policy_draft)
selected = docs['execution_job']['payload']['representation_jobs']['original32']
producer = docs['producer_plan']['producers']['original32']
for role, key in [('pair_policy', 'pair_execution'),
                  ('compact_policy', 'compact_execution'),
                  ('archive_policy', 'compact_archive_execution')]:
    pin = hashlib.sha256(raw(docs[role])).hexdigest()
    for value in (selected, producer):
        value['descriptor'][key]['policy_sha256'] = pin
destination = HERE/'public01'
destination.mkdir(exist_ok=False)
public_refs = {}
for role, value in docs.items():
    pin = save(destination/(role+'.json'), value)
    public_refs[role] = {k: pin[k] for k in ('path', 'sha256')}
    public_refs[role]['dataset'] = 'eth'
refs = copy.deepcopy(load(ROOT/binding['public_refs']['path']))
refs.update(public_refs)
scratch = move(load(ROOT/refs['matching_ordered_edge_scratch']['path']))
scratch_ref = save(HERE/'MATCHING_SCRATCH_RESERVATION01.json', scratch)
refs['matching_ordered_edge_scratch'] = {
    k: scratch_ref[k] for k in ('path', 'sha256')}
refs['matching_ordered_edge_scratch']['dataset'] = 'eth'
assert len(refs) == 64 and len(docs) == 12
save(HERE/'PUBLIC_INPUT_REFS01.json', refs)
public = move(copy.deepcopy(prior_public))
public['source_anchor'] = docs['pair_policy']['numerical_source']['commit']
public['source_pins'] = {name: sha(ROOT/name) for name in public['source_pins']}
public['builder_sha256'] = sha(Path(__file__))
public['public_inputs'] = public_refs
public_ref = save(HERE/'PUBLIC_MANIFEST01.json', public)
core = load(ROOT/binding['core_manifest']['path'])
core['builder_sha256'] = sha(Path(__file__))
for role in core['inputs']:
    core['inputs'][role] = {k: public_refs[role][k] for k in ('path', 'sha256')}
    core['inputs'][role]['bytes'] = (ROOT/public_refs[role]['path']).stat().st_size
save(HERE/'CORE_MANIFEST01.json', core)
capacity = move(load(ROOT/binding['capacity_observation']['path']))
capacity['at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
capacity['source_anchor'] = public['source_anchor']
capacity['source_body_pins'] = public['source_pins']
capacity['basis']['public_source_manifest'] = public_ref
capacity['qualification'] += ' Successor26 reuses the accepted unchanged prospective budget; actual failed25 additions stay in the fresh union baseline. The reviewed admission deduplication and batched-policy normalization change no numerical storage forecast.'
save(HERE/'CAPACITY_DECLARATION01.json', capacity)
save(HERE/'PREPARATION01.json', {
    'status': 'PUBLIC_INPUTS_PREPARED_NOT_BOUND_NOT_REGISTERED_NOT_RELEASED',
    'identity': NEW, 'terminal_parent': OLD, 'inputs': 64, 'public_documents': 12,
    'numerical_source_files': len(docs['pair_policy']['numerical_source']['files']),
    'original_model_training_refs': public['model_training_original_refs'],
    'prior_binding': binding['gate'], 'corrected_policy': {
        'path': str(policy_draft.relative_to(ROOT)), 'sha256': sha(policy_draft)},
    'qualification': 'Only fresh workflow/namespace/cell labels, the complete current193-source policy and descriptor hashes, and three reviewed source pins change. Original graph/dictionary/model/training/numerical limits remain. The opaque connection is deliberately unset until the existing accepted binder supplies it; no empirical authority.'})
print(json.dumps({'identity': NEW, 'inputs': len(refs), 'public_documents': len(docs),
                  'numerical_sources': len(docs['pair_policy']['numerical_source']['files']),
                  'claim': False, 'network': False}))
