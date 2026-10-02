"""Qualify draft sampler accounting; no production import or execution."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
OLD = OUT.parent/'revision01-original'
ROOT = OUT.parents[4]

def unknown(reason):
    return {'value':None,'reason':reason}

def load(name):
    return json.loads((OLD/name).read_bytes())

def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')

def pin(name):
    raw=(ROOT/name).read_bytes()
    return {'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

mapping=load('resource-cells.draft.json')
physical=load('physical-accounting.draft.json')
budget=load('budget-reconciliation.draft.json')
reason=('Selected compact resident-leased-v1 requires16bytes per training center for weights/probability and separately bounded retained samples/index/NumPychoice/Python/RSS; no MappedWeights20GiB floor applies to that route. Optional neighborhoods.sample_neighborhoods with nonnull weight_workspace invokes MappedWeights and requires20GiB+reservedworkspace. Preserve user10GiB floor for all routes; freeze exact route and complete physical/RAM limits prospectively.')
old_key='floor_reconciliation'
new_key='sampler_route_resource_admission'
mapping['prerequisites'][new_key]=reason
del mapping['prerequisites'][old_key]
for cell in mapping['cells']:
    cell['prerequisite_ids']=[new_key if v==old_key else v for v in cell['prerequisite_ids']]
budget['required_before_adoption']=[new_key if v==old_key else v for v in budget['required_before_adoption']]
paths={
    'compact_sampler':'tradingagents/research/onchain_replication/compact_sampler.py',
    'leased_core':'research/onchain-paper-replication-2026-09-24/full_sources/sampler-leased-core-2026-10-01/core.py',
    'neighborhoods':'tradingagents/research/onchain_replication/neighborhoods.py',
    'mapped_weights':'tradingagents/research/onchain_replication/sampling_weights.py',
}
(OUT/'observed-source').mkdir()
pins={}
for label,path in paths.items():
    pins[label]=pin(path)
    (OUT/'observed-source'/f'{label}.py').write_bytes((ROOT/path).read_bytes())
route={
    'selected_compact_route':{
        'selector':'compact_sampler._prepare requires policy.kernel == resident-leased-v1',
        'kernel':'resident-leased-v1','storage':'resident NumPy arrays',
        'mapped_weights_instantiated':False,'mapped_20gib_floor_applies':False,
        'direct_array_requirement_formula':'16 * total_centers_in_admitted_training_graph_union',
        'direct_array_bytes_per_center':16,
        'direct_array_limit_formula':'16 * total_centers <= policy.limits.max_direct_weight_bytes',
        'center_limit_formula':'sample_count <= total_centers <= policy.limits.max_centers',
        'retained_sample_limit_formula':'sum(sample_array_bytes(selected_neighborhoods)) <= neighborhood.max_sample_array_bytes',
        'retains_sample_graphs_in_memory':True,
        'not_covered_by_direct_weight_bound':['NumPychoice scratch','parentgraphs','retainedsample arrays','active neighborhood index','selected-index and offset arrays','Python objects','model/autograd','other working buffers'],
        'sample_metadata_disk_formula':'(sample_count + 3) * max_metadata_bytes <= max_attempt_bytes',
        'direct_weight_allowance_bytes':unknown('Prospective training graph union and sampler policy remain unadopted.'),
        'retained_sample_ram_allowance_bytes':unknown('Selected512neighborhood arrays and lifetime require complete prospective bound; no measured retained RAM.'),
        'active_index_ram_allowance_bytes':unknown('Active graph index footprint depends on prospective bounded neighborhood policy.'),
        'numpy_choice_scratch_bytes':unknown('16bytes per center accounts only weights/probability, not NumPychoice scratch/RSS.'),
        'whole_sampler_peak_rss_bytes':unknown('Must include all coexisting parentgraphs, retained samples, index, arrays, Python and guard overhead.'),
        'whole_sampler_disk_allowance_bytes':unknown('Metadata/sample publication/archive/checkpoint/transfer allowances remain unresolved; absence of mapped floor is not disk feasibility.'),
    },
    'optional_mapped_route':{
        'entrypoint':'neighborhoods.sample_neighborhoods',
        'activation_condition':'weight_workspace is not None',
        'mapped_weights_instantiated_when_condition_true':True,
        'selected_by_current_compact_sampler':False,
        'mapped_20gib_floor_applies_only_when_activated':True,
        'floor_bytes':20*2**30,
        'free_space_requirement_formula':'free_bytes >= 20GiB + reserved_workspace_bytes',
        'workspace_formula':'3 * ceil(count * 8 / filesystem_block_bytes) * filesystem_block_bytes + metadata_bytes',
        'workspace_arrays':['weights','probability','cdf'],
        'reserved_workspace_bytes':unknown('Mapped route not selected; center count, filesystem allocation and metadata allowance not adopted.'),
        'policy_decision_if_selected':'Preserve existing20GiB+workspace guard or prospectively review an explicit amendment;10GiB user floor is never relaxed.',
    },
    'user_minimum_local_free_bytes_all_routes':10*2**30,
    'route_choice_for_future_admission':unknown('Current code selects resident kernel; future exact executable registration and complete route policy remain unadopted.'),
    'source_observation_pins':pins,
    'qualification':'Read-only source-route observation, not executable source admission, an empirical measurement or a gate change.',
    'direct_array_arithmetic_by_single_graph':[{'week':g['week'],'centers':g['nodes'],'weights_plus_probability_bytes':16*g['nodes']} for g in mapping['graphs']],
    'conditional_nine_graph_union_direct_array_bytes':16*sum(g['nodes'] for g in mapping['graphs']),
    'union_qualification':'Arithmetic only; nine-graph union is not selected here and per-week original resource population is unchanged.'
}
for key in ['current_sampler_minimum_free_before_reservation_bytes','sampler_requirement_formula','floor_resolution']:
    del physical[key]
physical['sampler_routes']=route
physical['sampler_observed_source_pin_qualification']='This retained pin identifies only optional MappedWeights implementation, not the selected compact resident kernel.'
physical['allowances']['retained_sampler_sample_ram_bytes']=unknown('Resident sampler retains neighborhood arrays; prospective bound and coexistence lifetime unresolved.')
physical['allowances']['sampler_numpy_choice_scratch_bytes']=unknown('Resident16bytes-per-center direct-array bound does not bound NumPychoice scratch or peak RSS.')
for draft in [mapping,physical,budget]:
    draft['draft_revision']=2
    draft['supersedes_revision01_only_for']='Sampler route applicability and associated RAM/disk prerequisites; historical populations, counts, arithmetic, budgets and all execution refusals unchanged.'
    draft['revision01_manifest_sha256']=hashlib.sha256((OLD/'SHA256SUMS').read_bytes()).hexdigest()
write('resource-cells.draft.json',mapping)
write('physical-accounting.draft.json',physical)
write('budget-reconciliation.draft.json',budget)
print(json.dumps({'status':'NONEXECUTABLE_REVISION02_PREPARED','selected_route':'resident-leased-v1','mapped_floor_applies_to_selected_route':False,'mapped_floor_activation':'weight_workspace is not None','original_cells_unchanged':32,'conditional_all_nine_graph_direct_bytes':route['conditional_nine_graph_union_direct_array_bytes']},sort_keys=True))
