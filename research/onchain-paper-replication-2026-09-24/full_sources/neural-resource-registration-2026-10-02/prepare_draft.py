"""One-shot metadata-only prospective registration preparation; no admission."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[4]
STUDY = ROOT / 'research/onchain-paper-replication-2026-09-24'
OUT = Path(__file__).resolve().parent


def raw_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': raw_hash(path)}


def save(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


observed_path = STUDY / 'full_sources/neural-resource-readiness-2026-10-02/observations.json'
observed = json.loads(observed_path.read_text())
recount_path = STUDY / 'full_sources/budget-recount-2026-10-02/recount01.json'
recount = json.loads(recount_path.read_text())
old_gate = json.loads((STUDY / 'full_sources/graph-successor-09-2026-09-30/gate.json').read_text())
allocation_path = STUDY / 'full_sources/neural-resource-readiness-2026-10-02/budget-split.draft.json'
inputs = {'model': {**pin(STUDY / 'config/model.json'), 'dataset': 'eth'}}
cells, windows, bindings = [], [], []
for row in observed['neural_cells']:
    path = ROOT / row['graph_manifest']
    assert raw_hash(path) == row['graph_manifest_sha256']
    metadata = json.loads(path.read_text())
    assert metadata['graph_hash'] == row['graph_hash']
    name = 'graph_' + row['week'].replace('-', '_')
    inputs[name] = {**pin(path), 'dataset': 'eth'}
    cells.append({'cell_id': row['original_requirement']['original_id'],
                  'week': row['week'], 'graph_input': name,
                  'graph_hash': row['graph_hash'],
                  'graph_config_hash': metadata['metadata']['graph_config_hash'],
                  'node_order_sha256': metadata['arrays']['node_ids']['sha256'],
                  'expected_nodes': row['nodes'], 'expected_edges': row['directed_edges']})
    start = datetime.fromisoformat(row['week']).replace(tzinfo=timezone.utc)
    windows.append({'dataset': 'eth', 'start': start.isoformat().replace('+00:00', 'Z'),
                    'end': (start + timedelta(days=7)).isoformat().replace('+00:00', 'Z'),
                    'availability': 'existing'})
    bindings.append({**pin(path), 'array_members': metadata['arrays'],
                     'original_requirement': row['original_requirement'],
                     'array_bodies_opened': False})
assert len(cells) == len({x['cell_id'] for x in cells}) == 9
assert max(x['saved_graph_file_bytes'] for x in observed['neural_cells']) < 1024**3

# Refusal ceilings for a capacity measurement, not estimates that it fits.
plan = {'schema_version': 1, 'model_input': 'model',
        'graph_activation_checkpointing': False, 'cells': cells,
        'limits': {'max_graph_bytes': 1024**3, 'max_checkpoint_bytes': 4*1024**2,
                   'max_output_bytes': 64*1024**2, 'cooperative_cell_seconds': 600}}
save('plan.draft.json', plan)
resources = {'memory_max_bytes': 6*1024**3, 'memory_high_bytes': 5*1024**3,
             'reserve_bytes': 3*1024**3, 'start_reserve_bytes': 9*1024**3,
             'disk_floor_bytes': 10*1024**3, 'disk_paths': [str(ROOT)],
             'wall_seconds': 7200}
execution = {'schema_version': 1, 'kind': 'neural_resource', 'resources': resources,
             'environment_input': 'environment', 'payload': {'plan_input': 'neural_plan'}}
save('execution-job.draft.json', execution)
inputs['neural_plan'] = {**pin(OUT / 'plan.draft.json'), 'dataset': 'eth'}
inputs['execution_job'] = {**pin(OUT / 'execution-job.draft.json'), 'dataset': 'eth'}
for name in ('environment', 'execution_workspace'):
    inputs[name] = {'path': None, 'sha256': None, 'dataset': 'eth',
                    'unresolved_reason': 'Freeze and review after corrected source acceptance; not a prospective-data binding.'}
template = {'family': 'paper', 'parent': 'eth-paper-resource-pilot-20260924-02',
            'question': 'Can the nine retained weekly graphs complete the original one-graph synthetic neural update and exact checkpoint roundtrip under the fresh enforced resource contract?',
            'charter': {**pin(OUT / 'CHARTER.draft.md')},
            'stage': 'development', 'reuse': 'exploratory', 'windows': windows,
            'selection': None, 'source_files': None, 'runtime_hashes': None,
            'inputs': inputs, 'cells': [x['cell_id'] for x in cells],
            'outputs': ['cell-ledger.json', 'resource-summary.json', 'artifact-index.json'],
            'cumulative_budget_extension': {'extension': None, 'review': None}}
save('gate-template.draft.json', {'status': 'NONEXECUTABLE_UNADOPTED', 'experiment_id': None,
     'execution_admitted': False, 'registry_template': {'schema_version': 1,
     'program_id': old_gate['program_id'], 'families': old_gate['families'],
     'datasets': old_gate['datasets'], 'experiments': {}}, 'experiment_template': template,
     'source_closure_rule': 'All job.required_sources plus exact charter/config/budget/review and runtime dependency closure, committed and independently reviewed before admission.',
     'unresolved': ['corrected source acceptance and exact execution commit',
                    'exact final identity, environment and workspace binding',
                    'substantive charter/limit/graph preservation and comparability review',
                    'accepted exact budget extension and fresh all-terminal snapshot check',
                    'live startup RAM and guarded same-device input/output admission',
                    'synthetic checkpoint-size evidence; observed physical disk accounting and guard overhead']})
claims = [{'experiment': x['experiment'], 'claim_sha256': x['claim_sha256'],
           'terminal_status': x['status'], 'terminal_sha256': x['terminal_sha256']}
          for x in recount['claims'] if x['group'] == 'replication']
assert len(claims) == 16 and old_gate['families']['paper']['prior_attempts'] + len(claims) == 33
save('extension.draft.json', {'schema_version': 1, 'program_id': old_gate['program_id'],
     'base_family': old_gate['families']['paper'], 'cumulative_ceiling': 62,
     'consumed_before': 33, 'initial_experiment': None, 'allocation': pin(allocation_path),
     'claims': claims, 'reason': 'Two independently schedulable retained-graph resource claims replace the one proposed resource slot; nine neural requirements can be measured independently of the other23. Existing failures and the original family are unchanged; no new financial fit or fresh-sample claim.'})
save('extension-review.pending.json', {'schema_version': 1, 'decision': 'pending',
     'extension_sha256': raw_hash(OUT/'extension.draft.json'), 'reviewer': None,
     'scope': 'Must review final non-null adopter, exact source/charter/allocation and complete closed-claim snapshot before adoption.'})
v = os.statvfs(ROOT)
memory = {line.split(':')[0]: int(line.split()[1])*1024
          for line in Path('/proc/meminfo').read_text().splitlines()
          if line.startswith(('MemTotal:', 'MemAvailable:'))}
save('preparation01.json', {'status': 'metadata_only_draft', 'execution_admitted': False,
     'time_utc': datetime.now(timezone.utc).isoformat(), 'observation_pin': pin(observed_path),
     'recount_pin': pin(recount_path), 'allocation_pin': pin(allocation_path),
     'graph_bindings': bindings, 'metadata_input_count': len(inputs),
     'free_bytes': v.f_bavail*v.f_frsize, 'memory': memory,
     'startup_memory_required_bytes': resources['start_reserve_bytes'],
     'startup_ram_sufficient_at_observation': memory['MemAvailable'] >= resources['start_reserve_bytes'],
     'maximum_checkpoint_payload_all_cells_bytes': 9*plan['limits']['max_checkpoint_bytes'],
     'output_refusal_ceiling_bytes': plan['limits']['max_output_bytes'],
     'array_bodies_read': False, 'model_imported': False,
     'qualifications': ['Limits are prospective refusal ceilings, not measured peaks or success predictions.',
                        'The source/runtime/guard/budget checks were not invoked; no lifecycle or launch namespace was created.',
                        'Existing graph bytes already occupy storage; do not subtract them again from free space.',
                        'The nulls make this wrapper deliberately nonexecutable, not a valid existing-data registration.']})
print('PASS: nine metadata-bound cells; explicit original model/population;16replication+17prior=33;62ceiling; no admission or array/model execution.')
