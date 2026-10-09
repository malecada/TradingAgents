"""Deterministic metadata-envelope accounting; all exemplar strings are length variables, not receipts."""
from pathlib import Path
import hashlib,json,os,resource,sys
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);os.nice(10)
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication'
graph_file=F/'mcm-batched-pilot-input-templates01-2026-10-09/draft01/GRAPH_BOUNDS.json'
graphs=json.loads(graph_file.read_text())['value']
old_file=F/'mcm-batched-whole-capacity02-2026-10-09/CAPACITY01.json';old=json.loads(old_file.read_text())
# Explicit future-entry restrictions, NOT inferred existing guarantees. Safe ASCII alphabet
# means one encoded JSON byte per path character. No emitted exemplar is an authority object.
H='h'*64;PATH='p'*512;N=2**63-1
raw=lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode()
size=lambda x:len(raw(x));round4=lambda n:((n+4095)//4096)*4096
history={'directory':PATH,'intent':'typed-'+H+'.json','intent_sha256':H,'complete':'typed-complete-'+H+'.json','complete_sha256':H}
receipt=dict(schema_version=1,format='archive-chunk-v1',transport_identity=H,remote='r'*127,member='m'*255,scope=H,source_sha256=H,bytes=N)
counter=dict(operations=N,preserved=N,recovered=N,chunks=N)
def envelopes(k):
 binding=dict(format='mcm-batched-group-v1',first_batch=N,batches=k,root=PATH,root_pin=[N,N],source_tokens='a'*(336*k),manifest_sha256=H)
 assert size(binding)<=8192
 member=dict(source_path=PATH,resolved_path=PATH,bytes=N,mtime_ns=N,expected_sha256=H,member='files/99999999')
 manifest=dict(members=[member]*(3*k),files=3*k,raw_bytes=N,archive_bytes=N,archive_sha256=H)
 semantic=dict(schema_version=1,format='group-semantic-recovery-v1',binding=binding,archive_sha256=H,start=N,stop=N,files=3*k,root_pin=[N,N])
 offload=dict(schema_version=1,format='registered-grouped-offload-v1',start=N,stop=N,cells=N,first_batch=N,batches=k,binding=binding,manifest=manifest,history=history,receipt=receipt,retired_files=3*k,resume_supported=False)
 fresh=dict(schema_version=1,format='registered-grouped-fresh-recovery-v1',original_history=history,history=history,source_binding=binding,start=N,stop=N,first_batch=N,batches=k)
 consume=[dict(schema_version=1,format='archive-consume-v1',receipt_sha256=H,receipt=receipt),dict(schema_version=1,intent_sha256=H,bytes=N,payload_sha256=H),dict(schema_version=1,verified_sha256=H,owned_cache_disposed=True)]
 work=[manifest,offload,receipt,receipt,dict(schema_version=1,receipt_sha256=H,owned_transfer_payloads_disposed=True),*consume,semantic,*consume,semantic,fresh]
 claim=dict(schema_version=1,format='typed-payload-operation-v1',owner=H,stage='mcm-'+H,stage_intent_sha256=H,stage_reference=H,kind='mcm-batched-bundle-v3',binding=binding,input='i'*128,input_sha256=H,ledger_identity=H,parent_claim_sha256=H,ordinal=N,reserved_payload_bytes=N,reserved_chunks=N,reserved=counter,batched_parent='actual-active-mcm-stage-v1')
 complete=dict(schema_version=1,operation_sha256=H,parts=N,parts_sha256=H,preserved_bytes=N,recovered_bytes=N,assumption='a'*512)
 part=dict(schema_version=1,operation_sha256=H,index=N,source=PATH,receipt=receipt,receipt_sha256=H,fresh_full_recovery=True)
 read=dict(receipt_sha256=H,bytes=N,reserved=counter)
 intent=dict(schema_version=1,kind='grouped-retirement-intent-v1',operation_sha256=H,binding=binding,receipt_sha256=H,recovery_attempt=PATH,semantic_root=PATH,failure_disposition='any subset may be retired; full group archive recovery required; no resume')
 retired=dict(schema_version=1,operation_sha256=H,binding=binding,files=3*k,receipt_sha256=H)
 typed=[claim,part,read,intent,retired,complete,claim,read,complete]
 assert len(work)==14 and len(typed)==9 and max(map(size,work+typed))<=131072
 return dict(work_body_bytes=sum(map(size,work)),work_alloc4096=sum(round4(size(x)) for x in work),typed_body_bytes=sum(map(size,typed)),typed_alloc4096=sum(round4(size(x)) for x in typed),largest_work_body=max(map(size,work)),manifest_body=size(manifest),offload_body=size(offload),largest_typed_body=max(map(size,typed)))
envelope_cache={k:envelopes(k) for k in range(1,17)}
rows={};totals={}
for graph,v in graphs.items():
 B=v['batches'];C=v['cells'];G=(B+15)//16;assert B==(C+4095)//4096
 env=[envelope_cache[min(16,B-16*i)] for i in range(G)]
 # Exact ceiling USTAR at 1024B each pending/complete, full original record/header size.
 tar=journal_live=0
 for first in range(0,B,16):
  lengths=[]
  for batch in range(first,min(first+16,B)):
   cells=min(4096,C-4096*batch);lengths.extend([1024,92+53*cells,1024])
  J=sum(lengths);A=((sum(512+((n+511)//512)*512 for n in lengths)+1024+10239)//10240)*10240
  assert A<=4*1024**2;tar+=A;journal_live=max(journal_live,J)
 r=dict(rows=v['rows'],cells=C,batches=B,groups=G,typed_operations=2*G,typed_chunks=3*G,actual_transport_commands=5*G,policy_commands=12*G,typed_controls=9*G,work_files=14*G+1,work_dirs=7*G+3,work_inventory_entries=21*G+4,max_preserved_bytes=tar,max_recovered_bytes=2*tar,logical_transport_bytes=4*tar,group_anchor_bytes=32*G,closure_tokens_bytes=168*B,numeric_origins_bytes=9*C,numeric_summary_bytes=8192*B,spool_and_output_bytes=8*C,live_original_journal_payload_upper=journal_live)
 for key in ('work_body_bytes','work_alloc4096','typed_body_bytes','typed_alloc4096'):r[key]=sum(e[key] for e in env)
 r['work_body_bytes']+=8192;r['work_alloc4096']+=8192 # one final fullcoverage body, conservative cap
 r['selected_persistent_alloc4096']=sum(round4(x) for x in (9*C,168*B,4*C,4*C))+8192*B+r['work_alloc4096']+r['typed_alloc4096']
 rows[graph]=r
 for key,value in r.items():totals[key]=totals.get(key,0)+value
out=dict(status='SOURCE_BOUND_CONDITIONAL_NOT_WHOLE_CAPACITY',entry_constraints={'all_record_paths_ascii_safe_bytes_max':512,'typed_input_name_ascii_safe_max':128,'receipt_member_bytes_max':255,'integers_nonnegative_max':N,'mtime_ns_nonnegative_max':N,'journal_body_cap':1024,'canonical_block_size':4096,'group_batches':16,'these_constraints_require_actual_entry_check':True},full_group_body_envelope=envelopes(16),graphs=rows,totals=totals,checkpoint_reservation_retained=43058298880,checkpoint_per_save_charge=269114368,maximum_saved_checkpoints_under_old_total=160,group_scratch_source_bound={'live_journal_payload_upper':max(r['live_original_journal_payload_upper'] for r in rows.values()),'archives_copies_upper':3*4*1024**2,'additional_RAM_archive_copies_unmeasured':True},prior_observation_only={'available_bytes':old['original_payload_evidence']['current_filesystem_available_bytes'],'floor_bytes':10737418240,'observation_is_not_current':True},unjoined=['original retained graph/index/tail/feature/model files and all legacy operation budgets','checkpoint actual allocation/file roster and shared global schedule cap','dispatch control_history actual compact selection or legacy caps; 2G typed context claim bodies duplicate claims','typed ledger _expected raw bodies, _typed_expected digests, dict/key overhead and repeated full history audits','directory allocation/inode availability and source path/metadata restrictions must be checked','failure receipts/staging/transport output caps and other writers actual reservations','remote physical quota/metadata and genuine reservation','full numerical/neural/runtime memory including cache and archives'],source_pins={})
files=[graph_file,old_file,F/'mcm-batched-grouped-driver01-2026-10-09/MANIFEST01.json']+[F/'mcm-batched-grouped-offload01-2026-10-09'/n for n in ('grouped_offload.py','grouped_offload_semantics.py','typed_payload_operations.py','MANIFEST01.json')]+[S/n for n in ('preservation.py','archive_chunks.py','archive_consume.py','typed_payload_policy.py','archive_dispatch.py','archive_control_history.py','archive_owner_operations.py')]
out['dispatch_unjoined_legacy_envelope']={'max_control_bytes_min':131072*(8+4*totals['policy_commands']),'max_diagnostic_bytes_min_excluding_payload':131072*totals['policy_commands'],'compact_control_history_selection_required_to_replace_legacy_envelope':True}
out['typed_success_expected_body_memory_envelope_bytes']=totals['typed_body_bytes']
out['typed_min_control_bytes_success_envelope']=totals['typed_body_bytes']
out['typed_failure_headroom_not_in_success_minimum']=True
out['execution']={'affinity':sorted(os.sched_getaffinity(0)),'python':sys.version,'limits':{'AS':256*1024**2,'FSIZE':4*1024**2,'CPU_seconds':30}}
out['source_pins']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(P/'CAPACITY01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'totals':totals,'full_group_body_envelope':out['full_group_body_envelope']}))
