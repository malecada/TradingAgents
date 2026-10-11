"""Finite source-only arithmetic. No project imports, arrays, claims or transport."""
import hashlib,json,resource
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(128*1024**2,128*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(20,20))
P=Path(__file__).resolve().parent; F=P.parent; R=P.parents[3]
paths=[]
def load(path):
 p=F/path;paths.append(p);return json.loads(p.read_text())
a=load('real-data-pilot-full36-entry-preparation01-2026-10-11/CAPACITY_DECLARATION_ROOT01.json')
base=load('real-data-pilot-full36-entry-preparation01-2026-10-11/BASELINE_STORAGE_OBSERVATION01.json')
join=load('real-data-pilot-full36-entry-preparation01-2026-10-11/PREPARATION_ONLY_CAPACITY_JOIN01.json')
old=load('mcm-batched-grouped-capacity01-2026-10-09/CAPACITY01.json')
old2=load('mcm-batched-grouped-capacity02-2026-10-09/CAPACITY01.json')
t=load('real-data-pilot-full36-binding-preparation01-2026-10-11/inputs01/typed_payload.json')
p=load('real-data-pilot-full36-binding-preparation01-2026-10-11/inputs01/mcm_policy.json')
transport=load('real-data-pilot-full36-binding-preparation01-2026-10-11/public01/archive_transport.json')
b=p['batched']; assert b['batch_cells']==4096 and b['group_batches']==16 and b['max_body_bytes']==4096
assert b['continuation']['manifest_input'] is None and not b['continuation']['graph_manifest_inputs']
assert transport['control_history']['success_control_bytes']==16384 and transport['control_history']['success_diagnostic_bytes']==2048
round4=lambda n:(n+4095)//4096*4096
rows=[]
for graph,v in t['graphs'].items():
 C=v['kinds']['mcm-output-f32']['max_preserved_bytes']//4;B=(C+4095)//4096;G=(B+15)//16
 assert old['graphs'][graph]['cells']==C and old['graphs'][graph]['batches']==B
 tar={1024:0,4096:0}; peak={1024:0,4096:0}; alloc={1024:0,4096:0}
 for cap in tar:
  for start in range(0,B,16):
   lengths=[]
   for batch in range(start,min(start+16,B)):
    lengths += [cap,92+53*min(4096,C-4096*batch),cap]
   extent=(sum(512+(n+511)//512*512 for n in lengths)+1024+10239)//10240*10240
   assert extent<=v['kinds']['mcm-batched-bundle-v3']['chunk_bytes']<=4*1024**2
   tar[cap]+=extent;peak[cap]=max(peak[cap],sum(lengths));alloc[cap]=max(alloc[cap],sum(map(round4,lengths)))
 assert tar[4096]<=v['kinds']['mcm-batched-bundle-v3']['max_preserved_bytes']
 assert B*4096<=b['continuation']['max_commit_bytes']
 rows.append(dict(graph=graph,cells=C,batches=B,groups=G,prefix_logical_cap=B*4096,prefix_alloc4096_cap=B*4096,additional_persistent_entries=B,old_tar_cap=tar[1024],new_tar_cap=tar[4096],cumulative_transport_delta=4*(tar[4096]-tar[1024]),old_live_journal_cap=peak[1024],new_live_journal_cap=peak[4096],old_live_journal_alloc4096=alloc[1024],new_live_journal_alloc4096=alloc[4096]))
B=sum(x['batches'] for x in rows);marker=B*4096;live=max(x['new_live_journal_cap'] for x in rows)-max(x['old_live_journal_cap'] for x in rows)
assert sum(x['cells'] for x in rows)==415968128
# Conservative equal logical/allocated addition retains old rounding surplus intact.
add=dict(logical_file_bytes=marker+live,allocated_bytes=marker+live,entries=B)
proj={k:join['projection'][k]+v for k,v in add.items()}
limits={'logical_file_bytes':join['fixed_limits']['max_logical_bytes'],'allocated_bytes':join['fixed_limits']['max_allocated_bytes'],'entries':join['fixed_limits']['max_entries']}
out=dict(status='SOURCE_ONLY_CONDITIONAL_WHOLE37_PROJECTION_NOT_ADMISSION',graphs=rows,total_cells=sum(x['cells'] for x in rows),total_batches=B,total_groups=sum(x['groups'] for x in rows),persistent_prefix_bytes=marker,live_journal_logical_delta=live,exact_live_journal_alloc4096_delta=0,conservative_additions_over36=add,inherited36_projection=join['projection'],whole37_projection_with_unchanged_declared_directory_other_writer_allowances=proj,fixed_caps=limits,remaining_margin={k:limits[k]-proj[k] for k in proj},cap_deficit={k:max(0,proj[k]-limits[k]) for k in proj},directory_headroom_inherited=a['directory_allocated_bound_bytes'],other_writer_headroom_inherited=a['other_writer_reserved_bytes'],additional_directory_bytes_not_measured=True,additional_directory_bytes_affordable_before_allocated_cap=limits['allocated_bytes']-proj['allocated_bytes'],control_delta=dict(new_per_batch_summary_files=0,new_summary_cap_bytes=0,new_typed_operations=0,new_transport_commands=0,new_group_controls=0,source_envelope_delta=0),cumulative_transport_addition_not_retained=sum(x['cumulative_transport_delta'] for x in rows),pilot36_new_writer_additions_at_mandatory_stop=dict(logical_file_bytes=0,allocated_bytes=0,entries=0),limitations=['Current36 declaration explicitly refuses full37 admission.','Projection reuses dated36 baseline; fresh actual37 baseline and disk free/inode observations required.','Directory allowance is prospective declared aggregate, not filesystem guarantee; expanded marker directory scope requires Root acceptance.','Retained controls use prior source envelopes and ASCII/path/integer restrictions, not full cumulative policy maxima.','No historical34 import; no new recovery copy/manifest is selected by current null manifest policy.','No actual measurement, claims, arrays, transport, reservations, registration or release.'])
for name in ('batched_continuation.py','batched_journal.py','batched_numeric_execution.py','compact_mcm_batched.py','grouped_offload.py','grouped_offload_semantics.py','typed_payload_operations.py','archive_control_history.py','phase_timing.py','real_pilot_import_caller.py'):
 paths.append(R/'tradingagents/research/onchain_replication'/name)
out['source_pins']={str(q.relative_to(R)):{'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'bytes':q.stat().st_size} for q in paths}
(P/'CAPACITY01.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ('total_cells','total_batches','total_groups','persistent_prefix_bytes','conservative_additions_over36','whole37_projection_with_unchanged_declared_directory_other_writer_allowances','remaining_margin','cap_deficit','cumulative_transport_addition_not_retained')},indent=2))
