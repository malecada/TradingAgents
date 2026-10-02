"""Read-only compact-file/count/formula checks. Does not import job or array code."""
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
S = 'research/onchain-paper-replication-2026-09-24/'
F = S + 'full_sources/'

def load(path):
    p = ROOT / path
    assert p.stat().st_size < 2 * 1024 * 1024
    return json.loads(p.read_bytes())

def checked(pin):
    p = ROOT / pin['path']
    assert p.stat().st_size < 2 * 1024 * 1024
    body = p.read_bytes()
    assert hashlib.sha256(body).hexdigest() == pin['sha256'], pin['path']
    if 'bytes' in pin:
        assert len(body) == pin['bytes']

mapping = load(OUT/'resource-cells.draft.json')
physical = load(OUT/'physical-accounting.draft.json')
budget = load(OUT/'budget-reconciliation.draft.json')
inv = load(F+'native-resource-admission-2026-10-01/inputs02.json')
coverage = load(F+'resource-coverage-05-2026-09-30/coverage.json')
lower = load(F+'compact-workflow-accounting-2026-10-02/lower-bound01.json')
scores = load(F+'score-tail-2026-10-01/accounting01.json')
for draft in [mapping, physical, budget]:
    assert draft['execution_admitted'] is False and draft['registration_adopted'] is False
    assert draft['coverage_credit_granted'] == 0 and draft['status'] == 'NONEXECUTABLE_DRAFT'
assert len(inv['inputs']) == 43
assert mapping['compact_input_pins'] == inv['inputs']
for path, pin in inv['inputs'].items():
    checked({'path':path, **pin})
for pin in [mapping['inputs_inventory_pin'], mapping['coverage_pin'], mapping['original_phase_pin'],
            *mapping['original_config_pins'], *physical['input_pins'], physical['sampler_observed_source_pin'],
            budget['existing_draft_pin'],budget['graph09_allocation_pin'],budget['graph10_allocation_pin']]:
    checked(pin)
assert mapping['original_phase_pin']['sha256'] == '0bc95f7e33d97485cd9e2fba6802dde168c26aa162b987ef762f9e28ee3a1522'
old = {r['original_id']:r for r in coverage['requirements'] if r['supported'] is False}
assert len(coverage['requirements']) == 109 and len(old) == 32
assert len({r['original_id'] for r in coverage['requirements']}) == 109
cells = {c['requirement_id']:c for c in mapping['cells']}
assert len(cells) == len(mapping['cells']) == 32 and set(cells) == set(old)
assert {k:c['original_record'] for k,c in cells.items()} == old
assert inv['pending_requirements'] == [c['original_record'] for c in mapping['cells']]
assert Counter(r['stage'] for r in old.values()) == {'neighborhoods':7,'matching':7,'mcm':9,'neural_checkpoint':9}
assert mapping['historical_dispositions_unchanged'] == {'complete':7,'unavailable':102}
assert coverage['supported_resource_requirements'] == mapping['counts']['supported_unchanged'] == 77
expected_weeks = {'2022-01-03','2022-06-13','2022-07-25','2022-11-07','2023-06-05','2024-01-01','2024-03-11','2024-08-05','2024-12-23'}
graphs = {g['week']:g for g in mapping['graphs']}
assert len(graphs) == 9 and set(graphs) == expected_weeks
for graph in graphs.values():
    checked(graph['manifest_pin']); checked(graph['verification_pin'])
    manifest = load(graph['manifest'])
    assert graph['manifest_pin']['sha256'] == graph['manifest_sha256']
    assert graph['graph_hash'] == manifest['graph_hash']
    assert graph['declared_array_members'] == manifest['arrays'] and len(manifest['arrays']) == 5
    assert sum(a['bytes'] for a in manifest['arrays'].values()) == graph['saved_array_file_bytes']
    assert graph['calendar'] == {k:manifest['metadata'][k] for k in ['asset','start_utc','end_utc','available_at']}
    assert graph['calendar']['asset'] == 'ETH'
    start = datetime.fromisoformat(graph['calendar']['start_utc'].replace('Z','+00:00'))
    end = datetime.fromisoformat(graph['calendar']['end_utc'].replace('Z','+00:00'))
    assert start.date().isoformat() == graph['week'] and end-start == timedelta(days=7)
    assert graph['array_members_read'] is False
    required_stages = {'mcm','neural_checkpoint'} if graph['week'] in ['2022-01-03','2022-06-13'] else {'mcm','neural_checkpoint','matching','neighborhoods'}
    assert {cells[c]['original_record']['stage'] for c in graph['pending_requirement_ids']} == required_stages
for cell in cells.values():
    graph = graphs[cell['week']]
    assert cell['requirement_id'] in graph['pending_requirement_ids']
    assert cell['calendar'] == graph['calendar'] and cell['graph_hash'] == graph['graph_hash']
    assert set(cell['prerequisite_ids']) <= set(mapping['prerequisites'])
    assert cell['prospective_source_sha256'] is None and cell['prospective_source_sha256_reason']
    assert cell['prospective_policy_sha256'] is None and cell['prospective_policy_sha256_reason']
    population = cell['original_scientific_population']
    stage = cell['original_record']['stage']
    if stage == 'neural_checkpoint':
        assert population['requires_numerical_mcm_completion'] is False
        assert (population['unique_graphs'],population['batch'],population['lookback'],population['seed']) == (1,16,28,11)
        assert 'mcm_complete_population' not in cell['prerequisite_ids']
    if stage == 'mcm':
        assert population['dictionary_week'] == '2022-01-03' and population['motifs'] == 32
        assert population['prospective_dictionary_choice']['value'] is None
    if stage == 'matching':
        assert population['pair_count'] == 32 and population['sample_count'] == 512
    if stage == 'neighborhoods':
        assert population['sample_count'] == 512 and population['seed'] == 11
assert mapping['original_dictionary_evidence'] == next(r for r in coverage['requirements'] if r['original_id']=='dictionary-2022-01-03')
assert sum(g['nodes'] for g in graphs.values()) == 18046816
assert sum(g['directed_edges'] for g in graphs.values()) == 24381697
assert sum(g['saved_array_file_bytes'] for g in graphs.values()) == 4779690416
assert physical['rows_by_week'] == lower['rows']
for row in physical['rows_by_week']:
    n = graphs[row['week']]['nodes'] * 32
    assert row['cells'] == n and row['minimum_pair_events'] == 2*n
    assert row['minimum_pair_log_payload_bytes'] == 2*n*168
    assert row['retained_score_payload_bytes'] == n*(80+8)
    assert row['two_saved_float32_mcm_payloads_bytes'] == n*4*2
    assert row['selected_persistent_payload_lower_bound_bytes'] == n*(336+88+8)
for key,value in lower['totals'].items():
    assert sum(row[key] for row in physical['rows_by_week']) == value
assert physical['selected_payload_lower_bound_bytes'] == 249479184384
assert physical['score_plus_matrix_payload_after_pair_event_offload_bytes'] == 50819833856+4619984896 == 55439818752
assert scores['totals']['metadata_allowance_bytes'] == (8816+9)*32768 == 289177600
assert physical['user_minimum_local_free_bytes'] == 10*2**30
routes = physical['sampler_routes']
resident = routes['selected_compact_route']
mapped = routes['optional_mapped_route']
assert resident['kernel'] == 'resident-leased-v1'
assert resident['mapped_weights_instantiated'] is False
assert resident['mapped_20gib_floor_applies'] is False
assert resident['retains_sample_graphs_in_memory'] is True
assert resident['direct_array_bytes_per_center'] == 16
assert mapped['entrypoint'] == 'neighborhoods.sample_neighborhoods'
assert mapped['activation_condition'] == 'weight_workspace is not None'
assert mapped['selected_by_current_compact_sampler'] is False
assert mapped['mapped_weights_instantiated_when_condition_true'] is True
assert mapped['mapped_20gib_floor_applies_only_when_activated'] is True
assert mapped['floor_bytes'] == 20*2**30
assert routes['user_minimum_local_free_bytes_all_routes'] == 10*2**30
assert 'current_sampler_minimum_free_before_reservation_bytes' not in physical
assert 'floor_reconciliation' not in mapping['prerequisites']
assert 'sampler_route_resource_admission' in mapping['prerequisites']
for c in mapping['cells']:
    assert 'sampler_route_resource_admission' in c['prerequisite_ids']
    assert 'floor_reconciliation' not in c['prerequisite_ids']
assert 'sampler_route_resource_admission' in budget['required_before_adoption']
for k in ['direct_weight_allowance_bytes','retained_sample_ram_allowance_bytes','active_index_ram_allowance_bytes',
          'numpy_choice_scratch_bytes','whole_sampler_peak_rss_bytes','whole_sampler_disk_allowance_bytes']:
    assert resident[k]['value'] is None and resident[k]['reason']
assert mapped['reserved_workspace_bytes']['value'] is None and mapped['reserved_workspace_bytes']['reason']
for row in routes['direct_array_arithmetic_by_single_graph']:
    assert row['centers'] == graphs[row['week']]['nodes']
    assert row['weights_plus_probability_bytes'] == 16 * row['centers']
assert len(routes['direct_array_arithmetic_by_single_graph']) == 9
assert routes['conditional_nine_graph_union_direct_array_bytes'] == 18046816*16 == 288749056
for label, pin in routes['source_observation_pins'].items():
    checked(pin)
    observed = (OUT/'observed-source'/f'{label}.py').read_bytes()
    assert hashlib.sha256(observed).hexdigest() == pin['sha256']
old_dir = OUT.parent/'revision01-original'
old_manifest = (old_dir/'SHA256SUMS').read_bytes()
assert old_manifest == (OUT.parent/'SHA256SUMS').read_bytes()
for line in old_manifest.decode().splitlines():
    sha,name=line.split('  ',1)
    assert hashlib.sha256((old_dir/name).read_bytes()).hexdigest() == sha
    assert (old_dir/name).read_bytes() == (OUT.parent/name).read_bytes()
for draft in [mapping,physical,budget]:
    assert draft['draft_revision'] == 2
    assert draft['revision01_manifest_sha256'] == hashlib.sha256(old_manifest).hexdigest()
original_mapping=json.loads((old_dir/'resource-cells.draft.json').read_bytes())
assert mapping['graphs'] == original_mapping['graphs']
assert mapping['counts'] == original_mapping['counts']
for new,original in zip(mapping['cells'],original_mapping['cells'],strict=True):
    assert {k:v for k,v in new.items() if k!='prerequisite_ids'} == {k:v for k,v in original.items() if k!='prerequisite_ids'}
for allowance in physical['allowances'].values():
    assert allowance['value'] is None and allowance['reason']
for component in physical['components']:
    assert component['unknown_reason']
    for key in ['physical_local_retained_bytes','physical_remote_retained_bytes','peak_local_scratch_bytes','checkpoint_allowance_bytes','transfer_allowance_bytes','cumulative_growth_allowance_bytes']:
        assert component[key] is None
old_budget = load(F+'native-resource-admission-2026-10-01/budget-allocation.draft.json')
assert budget['existing_draft_preserved'] == old_budget
assert (budget['spent_preserved'],budget['remaining_missing_body_batches'],budget['remaining_financial_batches'],budget['proposed_new_resource_slots']) == (33,12,15,1)
assert 33+12+15 == budget['previous_ceiling'] == 60
assert 33+12+15+1 == budget['proposed_cumulative_ceiling'] == 61
assert budget['refunds'] == budget['new_financial_fits'] == 0
assert budget['maximum_unique_fits_unchanged'] == mapping['financial_fit_count_unchanged'] == 1420
assert budget['adopted_amendment_sha256'] is None and budget['adopted_amendment_sha256_reason']
print(json.dumps({'status':'REVISION02_PASS','selected_route':'resident-leased-v1','selected_route_mapped_floor':False,'optional_mapped_activation':'weight_workspace is not None','original_evidence_bytes_preserved':True,'compact_input_pins_verified':43,'pending_cells_preserved':32,'graphs':9,'supported_unchanged':77,'original_requirements':109,'pending_by_stage':{'neighborhoods':7,'matching':7,'mcm':9,'neural_checkpoint':9},'logical_payload_bytes':249479184384,'cumulative_draft_ceiling':61,'array_body_reads':0,'execution_admitted':False}, sort_keys=True))
