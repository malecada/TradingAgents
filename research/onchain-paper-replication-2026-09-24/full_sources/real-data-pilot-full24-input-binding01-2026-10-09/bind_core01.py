"""Bind actual public full-pilot core inputs; no claims, private config or arrays."""
import copy
import hashlib
import json
from pathlib import Path
from tradingagents.research.onchain_replication import (
    compact_mcm_batched, compact_policy, real_pilot_reservations,
    resource_binding, typed_payload_policy)

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
F = HERE.parent
OLD = F / 'real-data-pilot-final23-2026-10-09'
DRAFT = F / 'mcm-batched-pilot-input-templates02-2026-10-09/draft02'
NAME = 'eth-paper-real-data-end-to-end-resource-20261009-24'


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


assert not (ROOT / 'research_runs' / NAME).exists()
manifest = load(DRAFT / 'MANIFEST.json')
for name, digest in manifest['files'].items():
    assert sha(DRAFT / name) == digest
templates = {p.name.split('.')[0]: load(p)['template']
             for p in DRAFT.glob('*.template.json')}
gate = load(OLD / 'gate03.json')
old = gate['experiments']['eth-paper-real-data-end-to-end-resource-20261009-23']


def old_public(role):
    # Explicit allowlist prevents private connection/transport or numerical reads.
    assert role in {'compact_policy', 'archive_policy', 'original_import_stage', 'pair_policy'}
    ref = old['inputs'][role]
    path = ROOT / ref['path']
    assert sha(path) == ref['sha256']
    return load(path)


capacity = load(F / 'mcm-batched-grouped-capacity01-2026-10-09/CAPACITY01.json')
mcm = copy.deepcopy(templates['mcm_policy'])
output = copy.deepcopy(templates['mcm_output_policy'])
typed = copy.deepcopy(templates['typed_payload'])
compact = old_public('compact_policy')
archive = old_public('archive_policy')
pair = old_public('pair_policy')
stage = old_public('original_import_stage')
graphs = capacity['graphs']
assert set(graphs) == set(typed['graphs'])
assert sum(g['cells'] for g in graphs.values()) == 415968128
# These are logical policy allowances. Their minima preserve all old history;
# they are not a claim about simultaneous physical occupation.
mcm['batched']['max_offload_metadata_bytes'] = max(g['work_body_bytes'] for g in graphs.values()) + 4 * 8192
mcm['batched']['max_offload_entries'] = max(g['work_inventory_entries'] for g in graphs.values()) + 16
old_typed_ref = old['inputs']['typed_payload']
assert sha(ROOT / old_typed_ref['path']) == old_typed_ref['sha256']
old_typed = load(ROOT / old_typed_ref['path'])
typed['max_control_bytes'] = max(old_typed['max_control_bytes'],
    capacity['typed_success_expected_body_memory_envelope_bytes'] + 2 * 131072)
for key, graph in typed['graphs'].items():
    for kind in typed_payload_policy.LEGACY_KINDS:
        assert graph['kinds'][kind] == old_typed['graphs'][key]['kinds'][kind]
typed_payload_policy.validate(typed)
for g in graphs.values():
    compact_mcm_batched.validate(mcm, g['cells'])
# Existing original logical owner/stage budgets are retained if larger.
reservation = real_pilot_reservations.validate(compact, stage, mcm, output,
    archive, typed, pair, sorted(graphs))
assert reservation['batched_schema'] == 6
assert reservation['physical_capacity_admitted'] is False
assert reservation['pair_occurrences'] == {k:g['cells'] for k,g in graphs.items()}
# Bind the actual prior freshness policy, changing only the encoded claim cap.
transport = copy.deepcopy(load(OLD / 'INPUT_DRAFT02.json')['protocol']['transport_limits'])
transport['control_history']['success_control_bytes'] = 16384
transport['namespace'] = 'ethpilot-20261009-24'
from tradingagents.research.onchain_replication.archive_control_history import capacity as history_capacity
commands = transport['max_commands'] + capacity['totals']['policy_commands']
history = history_capacity(commands, transport['control_history'])
transport['max_commands'] = commands
transport['max_control_bytes'] = max(transport['max_control_bytes'], history['control_bytes'])
transport['max_diagnostic_bytes'] = max(transport['max_diagnostic_bytes'], history['diagnostic_bytes'])
# Retain the old cumulative rounded allowance and add grouped IO without refunds.
transport['max_payload_bytes'] += capacity['totals']['logical_transport_bytes'] + 2 * 65536 * capacity['totals']['typed_chunks']
destination = HERE / 'core01'
destination.mkdir(exist_ok=False)
for role, value in {'mcm_policy':mcm,'mcm_output_policy':output,
                    'typed_payload':typed,'compact_policy':compact}.items():
    write(destination / (role + '.json'), value)
write(HERE / 'TRANSPORT_LIMITS01.json', transport)
write(HERE / 'CORE_CHECK01.json', {
    'status':'CORE_METADATA_VALIDATED_NOT_RELEASED', 'experiment':NAME,
    'original_graphs':7, 'original_cells':415968128, 'groups':6352,
    'installed_reservation_result':reservation,
    'history_policy_correction':'Actual prior1000ms/4096callbacks preserved; only healthy control cap16384 changes. Capacity02/template draft10000/10000 values are not selected.',
    'logical_allowances_not_physical_forecast':True,
    'full_input_binding_complete':False, 'whole_capacity_admitted':False,
    'claim':False, 'launch':False})
write(HERE / 'CORE_MANIFEST01.json', {
    'status':'DRAFT_NOT_RELEASED', 'builder_sha256':sha(Path(__file__)),
    'inputs':{p.stem:{'path':str(p.relative_to(ROOT)), 'sha256':sha(p), 'bytes':p.stat().st_size}
              for p in sorted(destination.iterdir())},
    'source':{str((ROOT/'tradingagents/research/onchain_replication'/n).relative_to(ROOT)):
              sha(ROOT/'tradingagents/research/onchain_replication'/n)
              for n in ('compact_mcm_batched.py','batched_pilot_reservations.py','real_pilot_reservations.py','typed_payload_policy.py')},
    'scope':'Four actual public full-pilot core inputs; genuine transport binding, descriptors, runtime/source/currentness and final registration/release remain separate.'})
print(json.dumps({'status':'CORE_METADATA_VALIDATED_NOT_RELEASED',
                  'cells':415968128, 'groups':6352, 'claim':False}))
