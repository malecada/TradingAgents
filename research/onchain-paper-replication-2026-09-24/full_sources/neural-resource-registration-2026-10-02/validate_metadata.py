"""Read compact metadata and retain provenance bindings; never admit a run."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
STUDY = ROOT/'research/onchain-paper-replication-2026-09-24'


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


plan = load(OUT/'plan.draft.json')
wrapper = load(OUT/'gate-template.draft.json')
job = load(OUT/'execution-job.draft.json')
extension = load(OUT/'extension.draft.json')
assert wrapper['execution_admitted'] is False
assert wrapper['experiment_id'] is None and wrapper['registry_template']['experiments'] == {}
assert extension['initial_experiment'] is None
assert load(OUT/'extension-review.pending.json')['decision'] == 'pending'
assert extension['cumulative_ceiling'] == 33+12+15+2 == 62
assert len(extension['claims']) == 16 and extension['base_family']['prior_attempts'] == 17
assert job['kind'] == 'neural_resource' and job['payload'] == {'plan_input': 'neural_plan'}
assert job['resources']['memory_max_bytes'] == 6*1024**3
assert job['resources']['start_reserve_bytes'] == 9*1024**3
assert job['resources']['disk_floor_bytes'] == 10*1024**3
assert plan['graph_activation_checkpointing'] is False
assert plan['limits']['max_output_bytes'] >= 9*plan['limits']['max_checkpoint_bytes']+1024**2
template = wrapper['experiment_template']
assert template['cells'] == [c['cell_id'] for c in plan['cells']]
assert len(set(template['cells'])) == 9
for name, item in template['inputs'].items():
    if item['sha256'] is None:
        assert name in ('environment', 'execution_workspace')
    else:
        assert sha(ROOT/item['path']) == item['sha256'], name
for record in extension['claims']:
    base = ROOT/'research_runs'/record['experiment']
    assert sha(base/'claim.json') == record['claim_sha256']
    terminal = base/(record['terminal_status']+'.json')
    assert sha(terminal) == record['terminal_sha256']
    assert load(terminal)['claim_sha256'] == record['claim_sha256']
source = load(STUDY/'full_sources/native-resource-admission-2026-10-01/inputs02.json')
bindings = []
for name, item in sorted(source['inputs'].items()):
    path = ROOT/name
    assert path.suffix in ('.json', '.md'), 'Refuse non-metadata body: '+name
    assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256']
    bindings.append({'path': name, **item})
for cell, graph in zip(plan['cells'], source['graphs'], strict=True):
    assert cell['week'] == graph['week']
    assert cell['graph_hash'] == graph['graph_hash']
    assert cell['expected_nodes'] == graph['nodes']
    assert cell['expected_edges'] == graph['directed_edges']
    assert graph['verification'] in source['inputs']
    assert graph['saved_array_file_bytes'] < plan['limits']['max_graph_bytes']
assert len(bindings) == 43
with (OUT/'provenance-bindings.draft.json').open('x') as f:
    json.dump({'execution_admitted': False, 'metadata_bindings': bindings,
               'graph_proofs': [{'week': g['week'], 'verification': g['verification'],
                  'sha256': source['inputs'][g['verification']]['sha256']} for g in source['graphs']],
               'final_gate_requirement': 'Carry the relevant exact original graph/provenance/history proof pins into final inputs/source closure and independently validate their semantic applicability before admission.',
               'array_bodies_read': False}, f, sort_keys=True, indent=2)
    f.write('\n')
print('PASS: nine exact metadata cells/windows/config;43preserved compact pins;nine graph proof pins;16closed replication claim hashes;62draft arithmetic;explicit nonexecution sentinels;no array/model/guard/admission execution.')
