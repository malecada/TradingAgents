"""Finite metadata-only reservation draft. No authority, payloads or runtime imports.

Inputs are declarations, not proofs: source evidence and filesystem assumptions
remain subject to independent review and Root's genuine admission. Never selects
or increases an execution cap. Unknown residual writer domains are errors.
"""
import argparse
import hashlib
import json
from pathlib import Path

META=8192
DMETA=131072
ARCHIVE=8*1024**2
WEEKS=tuple('2022-'+x+'T00:00:00Z' for x in ('05-02','05-09','05-16','05-23','05-30','06-06','06-13'))
EXPERIMENT='eth-paper-real-data-end-to-end-resource-20261006-10'
ALLOCATION='../../real-data-pilot-resource-buffer-allocation01-2026-10-06/allocation01.py'
ALLOCATION_SHA='3912e68c232553f1fab5e39a92c0741c2c0ddab49316321c1189781d19611dfd'
# These are disjoint from the derived domains below. None may be omitted/zeroed
# by default. Evidence must cover success, failure, temporary and ancestor paths.
REQUIRED={
 'checkpoint_retention': 'stage_retention/restart_retention: all retained states, input copies, generations, bridges, replay evidence and failure controls for eight stages',
 'import_owner_stage_journal': 'original import, compact_owner stage intent/complete, feature_journal metadata, imported sample/dictionary reference controls; opaque numeric sources stay inputs',
 'training_and_lifecycle': 'real_pilot_training checkpoint/phases/complete/failed plus ResearchRun outputs, progress, guard/sampler/stdout and run/shared-lock writers',
 'runtime_temp_cache': 'real_pilot_storage forwarded native temp/cache and all additional selected writer paths not in the other named domains',
}

def need(ok,message):
    if not ok:raise ValueError(message)
def integer(n,zero=False):
    need(type(n) is int and (0 if zero else 1)<=n<2**63,'finite integer declaration required')
    return n
def sha(s):
    need(type(s) is str and len(s)==64 and all(c in '0123456789abcdef' for c in s),'exact SHA256 reference required')
def exact(v,keys,label):need(type(v) is dict and set(v)==set(keys),label+' fields differ')
def allocation():
    raw=(Path(__file__).parent/ALLOCATION).read_bytes()
    need(hashlib.sha256(raw).hexdigest()==ALLOCATION_SHA,'accepted allocation source changed')
    ns={};exec(compile(raw,ALLOCATION,'exec'),ns);return ns

def calculate(s):
    exact(s,{'schema_version','graphs','chunk_cells','typed_control_bytes','archive','stage','transport','residual_domains','filesystem','baseline','storage_budget'},'input')
    need(type(s['schema_version']) is int and s['schema_version']==1,'schema version')
    need(type(s['graphs']) is dict and set(s['graphs'])==set(WEEKS),'exact seven original weekly counts required')
    calc=allocation();integer(s['chunk_cells']);integer(s['typed_control_bytes'])
    st=s['stage'];exact(st,{'max_events','chunk_events','max_total_checkpoints'},'stage')
    for x in st.values():integer(x)
    pair_chunk=st['chunk_events']*168
    need(pair_chunk<=ARCHIVE,'original pair chunk exceeds codec cap')
    by={};attempts=ops=batches=0
    for week in WEEKS:
        g=s['graphs'][week];exact(g,{'rows','tail_part_bytes','output_part_bytes','allowances','count_evidence_sha256'},'graph')
        sha(g['count_evidence_sha256'])
        x=calc['graph'](g['rows'],s['chunk_cells'],g['tail_part_bytes'],g['output_part_bytes'],pair_chunk)
        calc['check_typed_allowances'](x,g['allowances'])
        for kind,required in x['required_typed_allowances'].items():
            exact(g['allowances'][kind],required,'typed kind')
            for v in g['allowances'][kind].values():integer(v,True)
            attempts+=g['allowances'][kind]['max_chunks'];ops+=g['allowances'][kind]['max_operations']
        need(set(g['allowances'])==set(x['required_typed_allowances']),'typed kinds differ')
        batches+=x['batch_count'];by[week]=x
    a=s['archive'];exact(a,{'max_stage_verifications','max_writer_metadata_bytes','max_read_metadata_bytes','max_stage_bytes','max_workflow_metadata_bytes'}|({'read_controls'} if 'read_controls' in a else set()),'archive')
    for key,x in a.items():
        if key!='read_controls':integer(x)
    R=a['max_stage_verifications'];need(R<=1024,'archive read bound')
    Q=(st['max_events']+st['chunk_events']-1)//st['chunk_events'];T=st['max_total_checkpoints']
    ordinary_ops=8*(1+R)
    writer_files=7*Q+8;read_files=3*Q+8
    read_bound=read_files*META;read_dirs=Q;archive_max_file=max(META,40*T)
    if 'read_controls' in a:
        from tradingagents.research.onchain_replication.archive_read_control_capacity import capacity as read_capacity
        packed=read_capacity(Q,a['read_controls']);read_bound=packed['logical_bytes'];read_files=packed['files'];read_dirs=packed['directories'];archive_max_file=max(archive_max_file,a['read_controls']['shard_bytes'])
    need(a['max_writer_metadata_bytes']>=writer_files*META and a['max_read_metadata_bytes']>=read_bound,'archive per-stage controls underfunded')
    need(a['max_stage_bytes']>=a['max_read_metadata_bytes']+40*T+8*META,'archive reference controls underfunded')
    archive_min=(4+3*ordinary_ops+8)*META+8*(a['max_writer_metadata_bytes']+8*META+R*a['max_stage_bytes'])
    need(a['max_workflow_metadata_bytes']>=archive_min,'archive workflow controls underfunded')
    tr=s['transport'];exact(tr,{'max_commands','max_payload_bytes','max_diagnostic_bytes','max_control_bytes'}|({'control_history'} if 'control_history' in tr else set()),'transport')
    for k,x in tr.items():
        if k!='control_history':integer(x)
    N=tr['max_commands']
    # Unchanged cumulative transport guards. This is NOT a complete transport
    # capacity calculator; builder03 still checks every pair/typed traversal.
    history_bounds=None
    if 'control_history' in tr:
        from tradingagents.research.onchain_replication.archive_control_history import capacity
        history_bounds=capacity(tr['control_history'],N)
        need(tr['max_diagnostic_bytes']>=history_bounds['diagnostic_bytes'] and tr['max_control_bytes']>=history_bounds['control_bytes'],'bounded transport caps underfunded')
    else:
        need(tr['max_diagnostic_bytes']>=tr['max_payload_bytes']+DMETA*N and tr['max_control_bytes']>=DMETA*(8+4*N),'original transport caps underfunded')
    typed_files=3*ops+attempts # intent/complete/failure plus preserved/read parts
    need(s['typed_control_bytes']>=typed_files*META,'typed ledger controls underfunded')
    dispatch_files=8+3*N+ordinary_ops+ops # command/result/reservation + claims
    if history_bounds is None:need(tr['max_control_bytes']>=dispatch_files*DMETA,'dispatch claims and command controls underfunded')
    else:dispatch_files=history_bounds['control_files']
    def item(n,files,dirs,max_file,basis):
        for value in (n,files,dirs,max_file):integer(value,True)
        return dict(logical_bytes=n,regular_files=files,directories=dirs,max_file_bytes=max_file,basis=basis)
    streams=5*batches+35
    # Archive file slots conservatively include reference binaries and failure
    # headroom. Directory count includes operation roots and nested event/copy/
    # read attempts; no checkpoint-retention files are included here.
    archive_files=4+3*ordinary_ops+8+8*(writer_files+8+R*(read_files+9))
    archive_dirs=1+ordinary_ops+8*(5+2*Q+R*(5+read_dirs))
    categories={
      'stream_tail_batch_headers':item(streams*META,streams,21+2*batches,META,'per graph 5B+5 JSON; stream/batches/tails plus 2B tail/typed directories'),
      'producer_output_controls':item(7*6*META,7*6,7*4,META,'per graph producer start/complete/failure; output manifest/storage/receipt; producer + attempt/artifact/transport'),
      'typed_attempts':item(attempts*4*META,attempts*4,attempts,META,'four metadata slots per selected chunk credit; includes failure headroom'),
      'typed_ledger':item(s['typed_control_bytes'],typed_files,0,META,'typed claims/complete/failure and part/read records; directory counted by archive'),
      'archive_ledger_writer_reads':item(a['max_workflow_metadata_bytes'],archive_files,archive_dirs,archive_max_file,'eight reserved original stages; writer/read metadata and 40-byte checkpoint references'),
      'dispatch':item(tr['max_control_bytes'],dispatch_files,1 if history_bounds is None else 2,DMETA if history_bounds is None else tr['control_history']['shard_bytes'],'Context controls; lease checks create no per-call disk file'),
      'transport_diagnostics':item(DMETA*N+ARCHIVE if history_bounds is None else history_bounds['diagnostic_bytes'],2*N if history_bounds is None else history_bounds['diagnostic_files'],1 if history_bounds is None else 2,ARCHIVE,'one JSON and at most one bin per call; one failed/inflight bin body; successful get staging moves into caller'),
      'retained_original_matrices':item(sum(x['retained_matrix_logical_bytes'] for x in by.values()),7,0,max(x['retained_matrix_logical_bytes'] for x in by.values()),'all seven original row-major f32 matrices; no RAM replacement'),
      'selected_payload_scratch':item(max(3*ARCHIVE,max(x['selected_payload_overlap_upper_bytes'] for x in by.values())),6,0,ARCHIVE,'accepted serial pair/tail/batch/output overlap; six simultaneous regular bodies upper bound; diagnostics counted separately'),
    }
    declarations=s['residual_domains'];need(type(declarations) is dict and set(declarations)==set(REQUIRED),'complete residual writer domain declarations required')
    extra_scratch=0
    for name,description in REQUIRED.items():
        d=declarations[name]
        exact(d,{'logical_bytes','regular_files','directories','max_file_bytes','additional_scratch_bytes','scratch_files','scratch_max_file_bytes','evidence_sha256','bound_basis'},name)
        for k in set(d)-{'evidence_sha256','bound_basis'}:integer(d[k],True)
        sha(d['evidence_sha256']);need(type(d['bound_basis']) is str and 0<len(d['bound_basis'])<=4096,'source-specific residual bound explanation required')
        need(d['regular_files']>0 and d['logical_bytes']>0 and d['max_file_bytes']>0,'unknown/zero residual domain refused')
        need(d['logical_bytes']<=d['regular_files']*d['max_file_bytes'],'residual per-file declaration inconsistent')
        need((d['additional_scratch_bytes']==0)==(d['scratch_files']==0)==(d['scratch_max_file_bytes']==0),'residual scratch declaration inconsistent')
        need(d['additional_scratch_bytes']<=d['scratch_files']*d['scratch_max_file_bytes'],'residual scratch extent inconsistent')
        if name=='training_and_lifecycle':need(d['logical_bytes']>=4*1024**2+2*65536+4096 and d['regular_files']>=4 and d['max_file_bytes']>=4*1024**2,'one-update checkpoint/receipt/phase minimum absent')
        categories[name]=item(d['logical_bytes']+d['additional_scratch_bytes'],d['regular_files']+d['scratch_files'],d['directories'],max(d['max_file_bytes'],d['scratch_max_file_bytes']),description)
        extra_scratch+=d['additional_scratch_bytes']
    fs=s['filesystem'];exact(fs,{'allocation_unit_bytes','per_regular_inode_overhead_bytes','per_directory_allocated_bytes','extra_allocated_bytes','extra_entries','max_native_file_bytes','evidence_sha256'},'filesystem')
    sha(fs['evidence_sha256'])
    for k in set(fs)-{'evidence_sha256'}:integer(fs[k],k in {'extra_allocated_bytes','extra_entries'})
    files=sum(c['regular_files'] for c in categories.values());dirs=sum(c['directories'] for c in categories.values())
    logical=sum(c['logical_bytes'] for c in categories.values())
    # This is an explicit filesystem model, NOT inferred stat blocks. Directory
    # allocation and inode metadata depend on filesystem/features/entry density.
    overhead=files*(fs['allocation_unit_bytes']-1+fs['per_regular_inode_overhead_bytes'])+dirs*fs['per_directory_allocated_bytes']+fs['extra_allocated_bytes']
    need(max(c['max_file_bytes'] for c in categories.values())<=fs['max_native_file_bytes'],'selected native file cap underfunded')
    baseline=s['baseline'];exact(baseline,{'logical_bytes','allocated_bytes','entries','evidence_sha256'},'baseline');sha(baseline['evidence_sha256'])
    for k in ('logical_bytes','allocated_bytes','entries'):integer(baseline[k],True)
    budget=s['storage_budget'];exact(budget,{'schema_version','kind','authority_root','experiment','roots','shared_files','limits'},'storage')
    root=budget['authority_root'];need(type(root) is str and root.startswith('/') and str(Path(root))==root and '..' not in Path(root).parts,'canonical root spelling required')
    need(type(budget['schema_version']) is int and budget['schema_version']==2 and budget['kind']=='real-pilot-writable-union' and budget['experiment']==EXPERIMENT and budget['roots']==[root+'/research_artifacts',root+'/research_runs/'+EXPERIMENT] and budget['shared_files']==[root+'/research_runs/.lock'],'exact original/shared writable scope required')
    lim=budget['limits'];exact(lim,{'max_logical_bytes','max_allocated_bytes','max_entries','max_depth','max_scan_seconds'},'storage limits')
    for v in lim.values():integer(v)
    need(lim['max_depth']<=64 and lim['max_scan_seconds']<=5,'original watcher limits differ')
    totals={'logical_bytes':logical+baseline['logical_bytes'],'allocated_bytes':logical+overhead+baseline['allocated_bytes'],'entries':files+dirs+fs['extra_entries']+baseline['entries']}
    for k,v in totals.items():need(v<=lim['max_'+k],'aggregate writable scope underfunded: '+k)
    # Builder03 lower-bound fields, not a complete builder spec or admission.
    other=sum(categories[k]['logical_bytes'] for k in REQUIRED)-extra_scratch
    fragment={'reserved_growth_bytes':categories['retained_original_matrices']['logical_bytes'],
      'reserved_control_bytes':s['typed_control_bytes']+a['max_workflow_metadata_bytes']+tr['max_control_bytes'],
      'retained_diagnostic_bytes':categories['transport_diagnostics']['logical_bytes'],
      'caller_scratch_bytes':categories['selected_payload_scratch']['logical_bytes']+extra_scratch,
      'allocation_overhead_bytes':overhead,'typed_attempt_metadata_bytes':categories['typed_attempts']['logical_bytes'],
      'remaining_control_inventory':{'stream_tail_batch_headers_bytes':streams*META,'producer_output_controls_bytes':42*META,'other_selected_controls_bytes':other},'additional_scratch_bytes':extra_scratch}
    need(sum(fragment[k] for k in ('reserved_growth_bytes','reserved_control_bytes','retained_diagnostic_bytes','caller_scratch_bytes','typed_attempt_metadata_bytes'))+sum(fragment['remaining_control_inventory'].values())==logical,'builder physical domains do not reconcile')
    for v in (logical,overhead,files,dirs,*totals.values()):integer(v,True)
    return {'status':'DRAFT_DECLARATIONS_NOT_ADMITTED','schema_version':1,'categories':categories,'by_week':by,'regular_file_slots':files,'directory_slots':dirs,'new_logical_bytes':logical,'allocation_overhead_bytes':overhead,'total_with_declared_baseline':totals,'builder03_physical_fragment':fragment,'storage_budget_unchanged':budget,'local_free_floor_bytes':10*1024**3,'transport_caps_unchanged':tr,'residual_declarations':declarations,'filesystem_assumption':fs,'qualification':'Finite reservation arithmetic conditional on reviewed declarations. Not an authenticated inventory, hard filesystem quota, scan-time/depth proof, available-capacity observation, RAM bound, current remote availability or permission to run. Builder03 must still validate exact metadata, 512/32/16x28 membership, transport and caller policy joins; Root must admit actual budgets and sources.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');a=p.parse_args()
    with Path(a.input).open('rb') as stream:raw=stream.read(4*1024**2+1)
    need(len(raw)<=4*1024**2,'metadata input too large')
    print(json.dumps(calculate(json.loads(raw)),sort_keys=True,indent=2,allow_nan=False))
