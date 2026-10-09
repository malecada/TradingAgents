"""Explicit schema5 accounting for the complete imported batched pilot only.

Logical event/score envelopes are not simultaneous physical-store reservations.
The existing writable-union and archive/typed transport guards remain separate.
"""
import re
from . import compact_policy, resource_binding, typed_payload_policy
from . import compact_mcm_batched, compact_owner
from .archive_read_control_capacity import capacity as read_capacity

def require(ok,message):
    if not ok:raise ValueError(message)

def validate(envelope,import_stage,mcm,output,archive,typed,pair,graph_keys):
    typed_payload_policy.validate(typed)
    require(typed['schema_version']==2 and typed['batched_parent']=='actual-active-mcm-stage-v1','batched typed active-stage grant required')
    require(set(typed['graphs'])==set(graph_keys) and len(graph_keys)==7,'exact seven reservation graph joins required')
    imported=resource_binding.import_policy(import_stage)
    require(type(envelope) is dict and set(envelope)=={'schema_version','backend','stage_policy','max_workflow_retained_logical_bytes'} and type(envelope['schema_version']) is int and envelope['schema_version']==1 and envelope['backend']==compact_policy.BACKEND,'compact reservation envelope differs')
    compact_policy.positive((envelope['max_workflow_retained_logical_bytes'],))
    stage=envelope['stage_policy'];require(stage['pair']==pair['limits'],'reservation pair policy differs')
    counts={k:v['rows']*32 for k,v in typed['graphs'].items()}
    capacities={k:compact_policy.validate(stage,kind='mcm',pairs=n) for k,n in counts.items()}
    owner=2*65536+imported['max_stage_bytes']+sum(c['logical_reservation_bytes']+2*8192 for c in capacities.values())
    require(owner<=envelope['max_workflow_retained_logical_bytes']<2**63,'complete imported owner reservation insufficient')
    require(compact_mcm_batched.selected(mcm),'explicit schema5 MCM reservation required')
    batched={key:compact_mcm_batched.validate(mcm,n) for key,n in counts.items()}
    compact_policy.positive((mcm['max_entries'],mcm['max_workflow_metadata_bytes']))
    require(mcm['max_entries']>=max(counts.values()) and mcm['max_workflow_metadata_bytes']>=3*8192*7,'MCM population/metadata reservation insufficient')
    numeric=mcm['numeric'];fields={'schema_version','max_buffer_bytes','edge_chunk','max_output_bytes','max_numeric_bytes'}
    require(type(numeric) is dict and set(numeric) in (fields,fields|{'extraction_limit'}) and type(numeric['schema_version']) is int and numeric['schema_version']==1,'MCM numeric schema')
    compact_policy.positive(numeric[k] for k in fields-{'schema_version'})
    if 'extraction_limit' in numeric:compact_policy.positive((numeric['extraction_limit'],))
    require(numeric['max_output_bytes']>=4*max(counts.values()) and numeric['max_numeric_bytes']>=4*max(counts.values())+numeric['max_buffer_bytes'],'MCM numeric reservation insufficient')
    require(type(output) is dict and set(output)=={'schema_version','backend','max_artifact_bytes','max_workflow_output_bytes'} and type(output['schema_version']) is int and output['schema_version']==1 and output['backend']==compact_policy.BACKEND,'batched local output reservation schema')
    compact_policy.positive((output['max_artifact_bytes'],output['max_workflow_output_bytes']))
    require(output['max_artifact_bytes']>=4*max(counts.values())+2*8192 and output['max_workflow_output_bytes']>=7*(output['max_artifact_bytes']+8192),'MCM output reservation insufficient')
    fields={'schema_version','backend','transport_identity','remote_namespace','local_free_floor_bytes','max_stage_verifications','max_writer_metadata_bytes','max_read_metadata_bytes','max_stage_bytes','max_workflow_metadata_bytes','max_remote_payload_bytes','max_decoded_transfer_bytes'}
    require(type(archive) is dict and set(archive)-{'read_controls'}==fields and type(archive['schema_version']) is int and archive['schema_version']==1 and archive['backend']=='compact-archive-events-v1','archive reservation schema')
    compact_policy.positive(archive[k] for k in fields-{'schema_version','backend','transport_identity','remote_namespace'})
    require(type(archive['transport_identity']) is str and re.fullmatch('[0-9a-f]{64}',archive['transport_identity']) and type(archive['remote_namespace']) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,19}',archive['remote_namespace']),'archive reservation endpoint/namespace')
    require(archive['local_free_floor_bytes']==typed['local_free_floor_bytes']==10*1024**3 and archive['max_stage_verifications']<=1024,'archive floor/verification bound differs')
    log=stage['log'];chunks=(log['max_events']+log['chunk_events']-1)//log['chunk_events'];reads=archive['max_stage_verifications'];count=8
    # Exact archive_pair_writer._policy and archive_owner_policy._record formulas.
    require(archive['max_writer_metadata_bytes']>=(7*chunks+8)*8192,'archive writer reservation insufficient')
    read=read_capacity(chunks,archive.get('read_controls'))['logical_bytes']
    refs=40*stage['schedule']['max_total_checkpoints']
    require(archive['max_read_metadata_bytes']>=read and archive['max_stage_bytes']>=archive['max_read_metadata_bytes']+refs+8*8192,'archive read/reference reservation insufficient')
    payload=count*log['max_events']*168
    controls=(4+3*count*(1+reads))*8192
    metadata=controls+8*8192+count*(archive['max_writer_metadata_bytes']+8*8192+reads*archive['max_stage_bytes'])
    require(archive['max_remote_payload_bytes']>=payload and archive['max_decoded_transfer_bytes']>=payload*(3+reads) and archive['max_workflow_metadata_bytes']>=metadata,'archive workflow reservation insufficient')
    for key,g in typed['graphs'].items():
        n=counts[key];require(g['chunk_cells']==stage['score_chunk_cells'],'typed/compact score chunk differs')
        full,last=divmod(n,g['chunk_cells']);batches=full+bool(last)
        for kind,width in typed_payload_policy.LEGACY_KINDS.items():
            v=g['kinds'][kind];part=v['chunk_bytes']
            if kind=='score-tail-f64':
                chunks=2*(full*((g['chunk_cells']*80+part-1)//part)+(0 if not last else (last*80+part-1)//part));operations=batches;recovered=n*80
            elif kind=='score-batch-f64':chunks=2*batches;operations=batches+1;recovered=n*8
            else:chunks=(n*4+part-1)//part;operations=1;recovered=0
            require(v['max_chunks']>=chunks and v['max_operations']>=operations and v['max_recovered_bytes']>=recovered,'typed traversal reservation insufficient')
        b=batched[key];batch_cells=b['batch_cells'];full,last=divmod(n,batch_cells);batch_count=full+bool(last)
        budget=g['kinds'][typed_payload_policy.BATCHED_KIND]
        grouped=mcm['schema_version']==6
        group_batches=b['group_batches'] if grouped else 1
        require(group_batches==(16 if grouped else 1),'explicit fixed journal group size required')
        def archive_extent(cells):
            # Original three journal bodies per batch, one complete tar per group.
            whole,remainder=divmod(cells,batch_cells)
            sizes=[]
            for actual in [batch_cells]*whole+([remainder] if remainder else []):
                sizes.extend((92+53*actual,b['max_body_bytes'],b['max_body_bytes']))
            return ((sum(512+((size+511)//512)*512 for size in sizes)+1024+10239)//10240)*10240
        full_groups,last_group_cells=divmod(n,batch_cells*group_batches)
        full_extent=archive_extent(batch_cells*group_batches)
        last_extent=archive_extent(last_group_cells) if last_group_cells else 0
        preserved=full_groups*full_extent+last_extent
        operations=full_groups+bool(last_group_cells)
        require(b['retention']==('typed-grouped-recover-before-retire-v1' if grouped else 'typed-recover-before-retire-v2'),'full selected pilot requires explicit offloaded journal retention')
        require(budget['chunk_bytes']>=max(full_extent,last_extent) and budget['max_operations']>=2*operations and budget['max_chunks']>=3*operations and budget['max_preserved_bytes']>=preserved and budget['max_recovered_bytes']>=2*preserved,'full batched preservation and two actual recoveries not reserved')
        require(b['execution']['max_summary_bytes']>=8192*batch_count,'full numeric summary reservation insufficient')
        selected=b['max_journal_bytes']+b['max_closure_token_bytes']+b['max_checkpoint_bytes']+b['max_spool_bytes']+b['max_offload_metadata_bytes']+b['execution']['max_origin_bytes']+b['execution']['max_summary_bytes']+4*8192
        require(selected<=capacities[key]['logical_reservation_bytes']+compact_owner.STAGE_BYTES,'batched genuine stage logical reservation insufficient')
    return {'batched_schema':mcm['schema_version'],'physical_capacity_admitted':False,'pair_occurrences':counts,'owner_logical_reservation_bytes':owner,'stage_capacities':capacities,'archive_metadata_bytes':metadata,'archive_remote_payload_bytes':payload,'qualification':'Original logical occurrence envelopes plus explicit batched bounds; not physical storage, capacity, or admission.'}
