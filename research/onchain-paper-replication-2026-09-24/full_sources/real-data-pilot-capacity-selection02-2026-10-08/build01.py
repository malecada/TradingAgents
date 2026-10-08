"""Deterministic metadata capacities. No arrays, empirical claims or admission."""
import copy
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
F=HERE.parent
META=8192
CONTROL=16384
SHARDED_CONTROL=65536
CHUNK_ENTRIES=262144
PINS={
 'actual_job':('real-data-pilot-final19-2026-10-08/ACTUAL_JOB_READONLY_ADMISSION01.json','77521f2a1313626a05dec9b9d98a2efdbb52bdb28bc0b2d649810d252b0b84a8'),
 'inputs':('real-data-pilot-capacity-application01-2026-10-08/INPUTS01.json','cd0d0122596c13e35c20a2dcf862a26fa11bf02d9b1baaa9884fcf9a6a6274a6'),
 'capacity':('real-data-pilot-capacity-application01-2026-10-08/CAPACITY01.json','86ff2ac343b6c6dab82b3e886f525fbb04e4ec3030faf9035386653ad6eeacd9'),
 'preparation':('real-data-pilot-final19-2026-10-08/PREPARATION_RESULT01.json','5fae455feef385b5248f0f0556ac1519b00ffab42d2418db3ab6b1f8e9cb79b0'),
 'kernel':('real-data-pilot-complete-neighborhood-capacity-preparation01-2026-10-08/imported_kernel.py','dc0a244b7cce4261093a95ce686a01bae0f26c8797a8616463c7d5078a2b2604'),
 'compact':('real-data-pilot-finite-reservation-correction01-2026-10-06/metadata01/compact_policy.json','c2843df0f6ce1c67b01b525f0c971caadc634b6f39afdb61f9467c77d9c48c3a'),
 'import_stage':('real-data-pilot-selected-feature-protocol01-2026-10-06/draft07/templates/original_import_stage.json','a00d61c743c6f2a9a5534ab772dc5ef383bde94bfcd5b1ed7c5003f89b5cde9b'),
 'mcm':('real-data-pilot-index-capacity01-2026-10-07/mcm_policy01.json','7a77c3818104a085e713333ce5d428ec696ff0be574cd3a8cc7d6e137ae06ed3'),
}

def read(name):
    relative,expected=PINS[name];raw=(F/relative).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('pinned input differs: '+name)
    return json.loads(raw)

def ceildiv(n,d):return (n+d-1)//d

def build():
    source_pins=json.loads((HERE/'SOURCE_PINS01.json').read_text())
    for name,expected in source_pins.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise ValueError('current validator/source changed: '+name)
    data=read('inputs');prior=read('capacity');graphs=data['topology']['graphs'];motifs=data['motifs']['representatives']
    if len(graphs)!=7 or len(motifs)!=32 or [m['motif_index'] for m in motifs]!=list(range(32)):raise ValueError('exact7/32 membership required')
    for g in graphs:
        if (g['node_features'],g['edge_features'],g['node_itemsize'],g['edge_itemsize'])!=(4,2,8,8):raise ValueError('target feature geometry differs')
    max_nodes=max(g['maximum_cardinality'] for g in graphs)
    pair_entries=max(g['maximum_cardinality']*m['nodes'] for g in graphs for m in motifs)
    axis=max(max(m['nodes'],g['maximum_cardinality'] if m['nodes']==1 else 2*g['maximum_cardinality']) for g in graphs for m in motifs)
    hard=max(17*g['maximum_cardinality']*m['nodes']+g['maximum_cardinality']+m['nodes']+16*min(g['maximum_cardinality'],m['nodes']) for g in graphs for m in motifs)
    if (max_nodes,pair_entries,axis,hard)!=(350110,8402640,700220,143195398):raise ValueError('authenticated geometry changed')
    io_scratch=3*(8*CHUNK_ENTRIES+128)+65536
    shards=ceildiv(pair_entries,CHUNK_ENTRIES)
    checkpoint=4*(8*pair_entries+128*shards)+3*65536
    compact=copy.deepcopy(read('compact'));stage=compact['stage_policy'];pair=stage['pair'];schedule=stage['schedule']
    pair.update(max_pair_entries_override=pair_entries,checkpoint_layout={'format':'sharded-npy-v1','chunk_entries':CHUNK_ENTRIES},
        max_state_bytes=32*pair_entries+io_scratch,normalization_chunk_entries=axis,hardening_buffer_bytes=hard,max_checkpoint_bytes=checkpoint)
    pair['max_score_buffer_bytes']=max(pair['max_score_buffer_bytes'],prior['universal_component_envelopes']['score_only_explicit_bytes']['required'])
    pair['total_checkpoint_bytes']=65536+schedule['max_checkpoints']*(checkpoint+65536)
    generations=schedule['max_total_checkpoints'];stores=generations;selections=2
    schedule['max_total_checkpoint_bytes']=generations*(checkpoint+2*META)
    # Exact stage-retention reservation calls, including their per-call16KiB
    # reserve record, subordinate64KiB controls and both selected input pairs.
    generation_control=8*SHARDED_CONTROL+3*65536
    controls=(8*CONTROL+selections*3*CONTROL+generations*(generation_control+4*CONTROL)
              +stores*(6*SHARDED_CONTROL+CONTROL)+(stores+selections)*3*CONTROL)
    input_pair_upper=prior['universal_component_envelopes']['retained_pair_input_upper_bytes']['required']
    input_upper=selections*input_pair_upper
    replay=selections*checkpoint
    live=controls+input_upper+replay+2*checkpoint
    cumulative=controls+input_upper+generations*checkpoint+replay
    retention=stage['restart_retention']
    retention.update(max_stores=stores,max_generations=generations,max_control_bytes=controls,max_input_bytes=input_upper,
        max_replay_bytes=replay,max_live_bytes=live,max_cumulative_bytes=cumulative,max_replays=selections)
    maxpairs=max(g['nodes']*32 for g in graphs);log=stage['log']
    log['max_pairs']=maxpairs;log['max_events']=2*maxpairs+generations
    log['max_logical_bytes']=log['max_events']*168+2*META
    def stage_bound(n):
        chunks=ceildiv(n,stage['score_chunk_cells']);scores=88*n+(4*chunks+4)*META
        return log['max_logical_bytes']+live+scores
    stage['max_retained_logical_bytes']=stage_bound(maxpairs)
    # Original imported stage reservation is reused; no dictionary recomputation.
    compact['max_workflow_retained_logical_bytes']=2*65536+read('import_stage')['max_stage_bytes']+sum(stage_bound(g['nodes']*32)+2*META for g in graphs)
    mcm=copy.deepcopy(read('mcm'));numeric=mcm['numeric'];rows=[]
    for g in graphs:
        n,e,c=g['nodes'],g['edges'],g['maximum_cardinality'];chunk=numeric['edge_chunk']
        index=16*(e+n+1)+16*e+40*(n+1)+4*n+chunk*(64+2*32+2*16)
        output_copies=2*(c*32+e*32)
        rows.append({'graph_sha256':g['graph_sha256'],'nodes':n,'edges_global_upper':e,'complete_neighborhood_max':c,
          'mcm_cells':n*32,'mcm_output_bytes':4*n*32,'index_and_extraction_bytes':index+output_copies,
          'stage_logical_reservation_bytes':stage_bound(n*32),'induced_edge_bound_is_global':True})
    numeric.update(extraction_limit=max_nodes,max_buffer_bytes=max(r['index_and_extraction_bytes'] for r in rows),max_output_bytes=4*maxpairs)
    numeric['max_numeric_bytes']=numeric['max_buffer_bytes']+numeric['max_output_bytes'];mcm['max_entries']=maxpairs
    if numeric['max_buffer_bytes']!=458003060:raise ValueError('index formula differs from authenticated capacity')
    domains=read('preparation')['residuals']['residual_domains']
    details={'schema_version':1,'execution_admitted':False,'complete_resource_envelope_proven':False,
      'frozen_native_memory_max_bytes':read('actual_job')['resource_policy']['memory_max_bytes'],
      'frozen_native_file_max_bytes':read('actual_job')['resource_policy']['native_unit_limits']['file_size_bytes'],
      'frozen_disk_floor_bytes':read('actual_job')['resource_policy']['disk_floor_bytes'],
      'validator_source_sha256':source_pins,
      'source_inputs':{k:{'path':v[0],'sha256':v[1]} for k,v in PINS.items()},'graphs':rows,
      'pair_entries':pair_entries,'retained_numeric_bytes':32*pair_entries,'checkpoint_io_scratch_bytes':io_scratch,
      'checkpoint':{'chunks_per_array':shards,'array_payload_bytes':8*pair_entries,'array_npy_headers_bytes':128*shards,
        'four_arrays_plus_three_64KiB_manifests_bytes':checkpoint,'max_chunk_file_bytes':8*CHUNK_ENTRIES+128,
        'generation_control_reservation_bytes':generation_control,'selected_control_record_cap':SHARDED_CONTROL},
      'retention_derivation':{'generations':generations,'stores':stores,'selected_pairs':selections,
        'selected_pair_input_conditional_upper':input_pair_upper,'stage_control_bytes':controls,'stage_live_bytes':live,'stage_cumulative_bytes':cumulative},
      'historical_declared_domains':domains,'candidate_retention_global_reservation_bytes':7*(controls+input_upper+replay)+2*checkpoint,
      'unresolved':['Selected-input bound includes16KiB metadata but original serializer enforces8KiB; complete node-ID JSON cardinality/encoded widths remain unproved.',
        'Selected inputs still serialize six full NPY bodies concurrently; ID Python objects and all encoded copies need whole-memory accounting.',
        'Largest conservative selected-input NPY exceeds historical16MiB checkpoint-domain declaration; actual native file cap1GiB is distinct.',
        'Sharded chunks2MiB+128 exceed historical256KiB checkpoint scratch-file declaration; exact physical-domain selection must be reconciled.',
        'GlobalE is conservative for local induced edges; no node/edge truncation admitted.',
        'Python/runtime/allocator, stable sort/SciPy scratch, source graph populations, retained outputs and filesystem cache remain outside component totals.',
        'Logical event/tail/output reservations require actual common physical-store reservation, bounded transport and verified offload/recovery.',
        'Existing160-checkpoint schedule is retained; capacity selection is not a completion or convergence guarantee.',
        'Root must join original/effective matching identities, source closure, current inputs and committed registration before any new trial.']}
    return {'compact_policy.json':compact,'mcm_policy.json':mcm,'pair_limits.json':pair,'CAPACITY_SELECTION01.json':details}

def main():
    outputs=build()
    for name,value in outputs.items():
        raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
        target=HERE/name
        if target.exists():
            if target.read_bytes()!=raw:raise ValueError('existing output differs: '+name)
        else:target.write_bytes(raw)
    print(json.dumps({'status':'metadata_built_not_admitted','files':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in outputs}},sort_keys=True))
if __name__=='__main__':main()
