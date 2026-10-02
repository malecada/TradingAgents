"""Nonexecuting preparation: read compact metadata only; write this new folder only."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
STUDY = 'research/onchain-paper-replication-2026-09-24/'
FULL = STUDY + 'full_sources/'

def read(name):
    path = ROOT / name
    assert path.stat().st_size < 2 * 1024 * 1024, name
    return path.read_bytes()

def load(name):
    return json.loads(read(name))

def pin(name):
    body = read(name)
    return {'path': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}

def unknown(reason):
    return {'value': None, 'reason': reason}

def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

inventory_path = FULL + 'native-resource-admission-2026-10-01/inputs02.json'
coverage_path = FULL + 'resource-coverage-05-2026-09-30/coverage.json'
lower_path = FULL + 'compact-workflow-accounting-2026-10-02/lower-bound01.json'
score_path = FULL + 'score-tail-2026-10-01/accounting01.json'
budget_path = FULL + 'native-resource-admission-2026-10-01/budget-allocation.draft.json'
phase_path = STUDY + 'pilot_successor_02/phase.py'
inv, coverage, lower, scores, budget = map(load, [inventory_path, coverage_path, lower_path, score_path, budget_path])
# These are the 43 compact files reviewed previously, not graph array bodies.
for name, expected in inv['inputs'].items():
    actual = pin(name)
    assert actual['bytes'] == expected['bytes'] and actual['sha256'] == expected['sha256'], name

common = {
    'status': 'NONEXECUTABLE_DRAFT', 'execution_admitted': False,
    'registration_adopted': False, 'coverage_credit_granted': 0,
    'schema_version': 1,
}
prerequisites = {
    'fresh_identity_and_budget': 'Independently review and commit a new cumulative61 amendment and fresh identity; graph09 and all historical terminal identities remain unavailable for reuse.',
    'source_runtime_policy_freeze': 'Freeze exact prospective source/runtime and all producer, matching, archive, guard and retention policy hashes after integration review.',
    'array_identity_and_availability': 'Join saved array evidence, then freshly verify required graph members and availability under the admitted bounded route; no graph rebuild and no credit from this metadata draft.',
    'outer_resource_guard': 'Freeze aggregate RAM, CPU, wall, local disk and transfer reservations including parent graph, dictionary, model/autograd, buffers and guard overhead.',
    'physical_storage_and_terminal_route': 'Resolve local/remote placement, retained score/checkpoint/event lifetimes, archive read budget and post-owner-close verification; verify full-content throughput and failure retention.',
    'floor_reconciliation': 'Keep authorized10GiB floor; current sampler requires20GiB plus reserved workspace. A prospective reviewed policy decision is required; this draft relaxes neither check.',
    'exact_cell_disposition': 'Retain every original status/reason. Give independent credit only to measured and verified exact requirements, preserve partial/unavailable failures.',
    'hub_capacity_amendment': 'Resolve observed701309nodes/712125inducededges against10000node extraction cap without truncation.',
    'pair_capacity_amendment': 'Resolve observed4207854hubpairentries against4000000pair cap and prove complete native memory/work bounds without truncation.',
    'sample_identity': 'Freeze original512samples, seed11, weakonehop induced directed graph and exact selected-center/sample identities, or record prospective change with no automatic original credit.',
    'matching_population': 'Original matching is32ordered pairs zip(samples[:32],samples[32:64]); preserve these inputs and literal matching config or review non-equivalence.',
    'dictionary_reuse_decision': 'Original all-week MCM reuses2022-01-03 dictionary. Prospective native dictionary choice is unresolved and cannot silently become per-week dictionaries.',
    'mcm_complete_population': 'Original MCM is every node of the week graph by32fixed dictionary motifs, float32 saved output. Freeze complete cells and checkpoint/publication preservation.',
    'neural_population_and_capacity': 'Original neural stress uses random synthetic float32MCM, one graph repeated16x28, synthetic prices/labels, seed11 and one optimization/checkpoint step; freeze exact model and working allowance without claiming chronological capacity.',
}
base_ids = list(prerequisites)[:7]
stage_ids = {
    'neighborhoods': ['hub_capacity_amendment', 'sample_identity'],
    'matching': ['hub_capacity_amendment', 'pair_capacity_amendment', 'sample_identity', 'matching_population'],
    'mcm': ['hub_capacity_amendment', 'pair_capacity_amendment', 'dictionary_reuse_decision', 'mcm_complete_population'],
    'neural_checkpoint': ['neural_population_and_capacity'],
}
populations = {
    'neighborhoods': {'asset': 'ETH', 'sample_count': 512, 'seed': 11,
        'candidate_population': 'all centers in this one saved week graph; weak one-hop induced subgraph retaining directed edges and center',
        'sampling': 'without replacement; equal initial candidate mass; halve remaining centers inside selected neighborhood',
        'original_training_start': 'graph.start_utc', 'original_training_end': '2026-01-01T00:00:00Z',
        'original_maximum_neighborhood_nodes': 10000, 'truncation_allowed': False},
    'matching': {'asset': 'ETH', 'sample_count': 512, 'seed': 11, 'pair_count': 32,
        'ordered_pairs': 'zip(sample.graphs[:32],sample.graphs[32:64],strict=True)',
        'max_pair_entries': 4000000, 'truncation_allowed': False,
        'qualification': 'This32pair resource measurement is not all node-by-motif MCM evaluations.'},
    'mcm': {'asset': 'ETH', 'node_population': 'every node in this exact saved week graph',
        'motifs': 32, 'saved_dtype': 'float32', 'dictionary_week': '2022-01-03',
        'dictionary_reuse_across_all_weeks': True,
        'prospective_dictionary_choice': unknown('Coordinator scientific reuse decision and exact admitted dictionary content identity remain unresolved.')},
    'neural_checkpoint': {'asset': 'ETH', 'seed': 11, 'unique_graphs': 1, 'batch': 16, 'lookback': 28,
        'mcm_input': 'synthetic numpy PCG64 random float32 with shape(nodes,32)',
        'requires_numerical_mcm_completion': False, 'prices': 'torch.linspace(-1,1,16*28).reshape(16,28,1)',
        'labels': 'torch.arange(16)%2', 'optimizer': 'Adam lr0.001', 'steps': 1,
        'loss': 'cross_entropy', 'checkpoint_epoch': 1, 'checkpoint_batch': 0,
        'qualification': 'Repeated-one-graph synthetic capacity/checkpoint stress only; not chronological multiweek training, actual MCM inference or financial validity.'},
}
graphs = {}
for graph in inv['graphs']:
    manifest = load(graph['manifest'])
    graphs[graph['week']] = {**graph, 'calendar': {k: manifest['metadata'][k] for k in ['asset', 'start_utc', 'end_utc', 'available_at']},
        'declared_array_members': manifest['arrays'],
        'array_members_read': False, 'manifest_pin': pin(graph['manifest']), 'verification_pin': pin(graph['verification'])}
dictionary_cell = next(r for r in coverage['requirements'] if r['original_id'] == 'dictionary-2022-01-03')
cells = []
for record in inv['pending_requirements']:
    week, stage = record['date'], record['stage']
    graph = graphs[week]
    cells.append({'requirement_id': record['original_id'], 'original_record': record,
        'week': week, 'graph_week_ref': week, 'graph_manifest_pin': graph['manifest_pin'],
        'graph_hash': graph['graph_hash'], 'calendar': graph['calendar'],
        'original_scientific_population': populations[stage], 'prerequisite_ids': base_ids + stage_ids[stage],
        'prospective_execution_cell_id': None,
        'prospective_execution_cell_id_reason': 'No prospective run registration or population mapping has been adopted.',
        'prospective_source_sha256': None,
        'prospective_source_sha256_reason': 'Producer-to-terminal integration and independent source freeze remain pending.',
        'prospective_policy_sha256': None,
        'prospective_policy_sha256_reason': 'Capacity, dictionary reuse, physical storage and guard policy amendments remain unresolved.',
        'execution_admitted': False, 'coverage_credit_granted': 0})
mapping = {**common, 'scope': 'Exact pending original resource requirements; preservation mapping only, not successor registration.',
    'inputs_inventory_pin': pin(inventory_path), 'coverage_pin': pin(coverage_path),
    'original_phase_pin': pin(phase_path), 'original_config_pins': [pin(STUDY+'config/'+name) for name in ['dictionary.json','matching-stable.json','model.json']],
    'compact_input_pins': inv['inputs'], 'graphs': list(graphs.values()), 'cells': cells,
    'counts': {'original_requirements': 109, 'supported_unchanged': 77, 'pending': 32, 'pending_by_stage': dict(Counter(r['stage'] for r in inv['pending_requirements']))},
    'historical_dispositions_unchanged': coverage['historical_dispositions'],
    'original_dictionary_evidence': dictionary_cell,
    'prospective_dictionary_content_sha256': None,
    'prospective_dictionary_content_sha256_reason': 'Historical result evidence is preserved; exact executable dictionary content/reuse admission is not frozen.',
    'prerequisites': prerequisites,
    'neural_population_does_not_depend_on_numerical_mcm': True,
    'financial_fit_count_unchanged': 1420,
    'no_credit_for': ['financial_fit_grid', 'chronological_multiweek_capacity', 'cold_historical_mapped_feature_admission', 'BTC_ETH_fund_comparisons', 'positive_returns']}
write('resource-cells.draft.json', mapping)

components = []
def component(name, logical, formula, reason):
    components.append({'name': name, 'conditional_logical_bytes': logical, 'logical_formula': formula,
        'physical_local_retained_bytes': None, 'physical_remote_retained_bytes': None,
        'peak_local_scratch_bytes': None, 'checkpoint_allowance_bytes': None,
        'transfer_allowance_bytes': None, 'cumulative_growth_allowance_bytes': None,
        'unknown_reason': reason, 'retention_policy_sha256': None,
        'retention_policy_sha256_reason': 'No prospective placement/lifetime/disposition policy adopted.'})
component('saved_graph_five_arrays', inv['totals']['saved_array_file_bytes'], 'sum(saved_array_file_bytes for nine pinned graphs)', 'Manifest-declared file-byte sum; current physical allocation, saved-edge duplication and staging overlap unmeasured.')
component('minimum_pair_events', lower['totals']['minimum_pair_log_payload_bytes'], '577498112 * 2 * 168', 'Logical begin+completion payload; header/metadata/checkpoint events, retries and archive allocation excluded; placement unresolved.')
component('score_tails', scores['totals']['retained_tail_record_bytes'], '577498112 * 80', 'Tail lifetime/placement not adopted; moving pair events alone does not remove these bytes.')
component('float64_score_batches', scores['totals']['batch_payload_bytes'], '577498112 * 8', 'Batch lifetime, local/remote staging, headers and failure copies unresolved.')
component('two_saved_float32_mcm_copies', lower['totals']['two_saved_float32_mcm_payloads_bytes'], '577498112 * 4 * 2', 'Saved output plus graph feature copy; dtype arithmetic only, physical allocation and lifetime unresolved.')
component('score_metadata_prior_logical_allowance', scores['totals']['metadata_allowance_bytes'], '(8816 + 9) * 32768', 'Prior static allowance, not measured overhead or an adopted admission cap.')
for name in ['dictionary_samples_matrices_events', 'matching_workspaces_and_snapshots', 'checkpoint_progress_event_growth',
             'model_optimizer_checkpoint_files', 'graph_saved_edge_artifacts', 'guard_logs_partial_writes_prior_attempts',
             'archive_upload_download_replay_staging', 'filesystem_allocation_headers_metadata']:
    component(name, None, None, 'Exact population-dependent lifetime, physical bytes and retained/peak/cumulative allowance remain unknown and must be measured or conservatively bounded before admission.')
worksheet = {**common, 'scope': 'Conditional logical arithmetic and explicit physical-accounting gaps; no final budget or measured peak claim.',
    'assumption': lower['assumptions'], 'input_pins': [pin(inventory_path), pin(lower_path), pin(score_path)],
    'rows_by_week': lower['rows'], 'selected_payload_totals': lower['totals'],
    'components': components,
    'selected_payload_lower_bound_bytes': 249479184384,
    'score_plus_matrix_payload_after_pair_event_offload_bytes': 55439818752,
    'score_plus_matrix_formula': '50819833856 + 4619984896',
    'not_in_selected_total': lower['excludes'],
    'source_pins_from_historical_arithmetic': lower['source_input_sha256'],
    'historical_source_pin_qualification': 'These identify the retained calculation, not current mutable integration source or a prospective run closure.',
    'prospective_source_closure_sha256': None,
    'prospective_source_closure_sha256_reason': 'Shared producer-to-terminal implementation is being edited; no frozen admitted source closure exists.',
    'free_space_observation': {'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'filesystem_path': str(ROOT),
        'free_bytes': shutil.disk_usage(ROOT).free, 'qualification': 'Point-in-time free space only; no reservation, capacity guarantee or launch authorization.'},
    'user_minimum_local_free_bytes': 10 * 2**30,
    'current_sampler_minimum_free_before_reservation_bytes': 20 * 2**30,
    'sampler_requirement_formula': 'free_bytes >= 20GiB + reserved_workspace_bytes',
    'floor_resolution': unknown('Coordinator must reconcile prospectively; maintain10GiB user floor and do not bypass current stricter sampler.'),
    'sampler_observed_source_pin': pin('tradingagents/research/onchain_replication/sampling_weights.py'),
    'allowances': {k: unknown('No reviewed physical/lifetime/aggregate reservation yet; null is not zero.') for k in
        ['local_retained_bytes','remote_retained_bytes','peak_local_scratch_bytes','peak_local_total_growth_bytes',
         'cumulative_checkpoint_bytes','retained_score_bytes','cumulative_transfer_bytes','remote_peak_staging_bytes',
         'rss_per_worker_bytes','host_reserve_bytes','cpu_limit','wall_seconds','verification_read_bytes']},
    'admission_equations': [
        'local_free_at_admission - max_t(incremental_local_retained(t) + local_scratch(t) + local_transfer_staging(t) + concurrent_reservations(t)) >= effective_floor_bytes',
        'remote_free_at_admission >= remote_retained_growth_peak + remote_partial_staging_peak + other_remote_reservations',
        'local_peak = max_t(sum(coexisting objects at t)); never sum all sequential maxima as though observed peak',
        'transfer_total = upload_bytes + verification_download_bytes + terminal_replay_bytes + retry_bytes; count each physical transfer',
        'aggregate_RSS_reservations + host_reserve <= currently_available_RAM'],
    'default_resource_heavy_concurrency': 1,
    'concurrency_reason': 'Historical8.4GiB available is below two3GiB workers plus3GiB host reserve; fresh aggregate measurements/reservations still required.',
    'physical_measurement_status': 'NOT_MEASURED', 'execution_route_decision': 'UNRESOLVED'}
write('physical-accounting.draft.json', worksheet)
reconciliation = {**common, 'existing_draft_pin': pin(budget_path), 'existing_draft_preserved': budget,
    'previous_ceiling': 60, 'spent_preserved': 33, 'remaining_missing_body_batches': 12,
    'remaining_financial_batches': 15, 'proposed_new_resource_slots': 1, 'proposed_cumulative_ceiling': 61,
    'formula': '33 + 12 + 15 + 1 = 61', 'old_formula': '33 + 12 + 15 = 60',
    'refunds': 0, 'new_financial_fits': 0, 'maximum_unique_fits_unchanged': 1420,
    'original_family_preserved': budget['original_family'],
    'prospective_identity_from_existing_draft': budget['prospective_identity'],
    'identity_status': 'proposal only; not reserved, launched or adopted by this preparation',
    'graph09_disposition': 'Reserved launch identity cannot be reused; rebound allowance consumed by graph10.',
    'graph09_allocation_pin': pin(FULL+'graph-successor-09-2026-09-30/budget-allocation.proposed.json'),
    'graph10_allocation_pin': pin(FULL+'graph-successor-10-2026-09-30/budget-allocation.proposed.json'),
    'historical_identities': 'All admitted historical study identities remain terminal; no old identity rerun.',
    'adopted_amendment_sha256': None, 'adopted_amendment_sha256_reason': 'Cumulative61 amendment has not been independently reviewed and adopted with exact executable contract.',
    'required_before_adoption': list(prerequisites),
    'attempt_count_qualification': '33spent is preserved from the pinned cumulative draft; this metadata preparation does not recount or reinterpret historical attempts.'}
write('budget-reconciliation.draft.json', reconciliation)
print(json.dumps({'status':'prepared_nonexecutable_drafts','compact_pins_checked':len(inv['inputs']), 'graph_count':len(graphs), 'cells':len(cells), 'pending_by_stage':mapping['counts']['pending_by_stage'], 'selected_logical_lower_bound_bytes':249479184384}, sort_keys=True))
