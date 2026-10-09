import os,json,hashlib,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
OUT=Path(__file__).resolve().parent
F=OUT.parent
pins={}
def read(p):
 p=ROOT/p if not Path(p).is_absolute() else Path(p)
 b=p.read_bytes();pins[str(p.relative_to(ROOT))]=hashlib.sha256(b).hexdigest();return json.loads(b)
refs=read(F/'real-data-pilot-full27-transport-binding01-2026-10-09/ALL_INPUT_REFS01.json')
selected={}
for k,r in refs.items():
 if '/real-data-pilot-full27-transport-binding01-' in r['path']:
  selected[k]=read(r['path']);assert pins[r['path']]==r['sha256']
# Private archive_transport and scientific data bodies are deliberately never opened.
job=selected['execution_job'];budget=job['resources']['storage_budget'];exp=budget['experiment']
from tradingagents.research.onchain_replication.real_pilot_storage import WritableUnion
for name in ('real_pilot_storage.py','workflow_storage.py','compact_mcm_batched.py','grouped_offload.py','grouped_offload_semantics.py'):
 p=ROOT/'tradingagents/research/onchain_replication'/name;pins[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
start=time.time();watch=WritableUnion(budget,ROOT,experiment=exp)
samples=[]
for i in range(2):
 try:samples.append({'status':'PASS','observation':watch.check()})
 except Exception as e:samples.append({'status':'REFUSAL','error':repr(e),'observation':getattr(e,'observation',None)})
fs=os.statvfs(ROOT);mem={}
for line in Path('/proc/meminfo').read_text().splitlines():
 k,v=line.split(':',1)
 if k in ('MemTotal','MemAvailable','SwapTotal','SwapFree'):mem[k+'_bytes']=int(v.split()[0])*1024
cap=read(F/'mcm-batched-grouped-capacity02-2026-10-09/CAPACITY01.json')
pol=selected['mcm_policy'];typed=selected['typed_payload'];graphs=typed['graphs'];rows=sum(x['rows'] for x in graphs.values());cells=32*rows
batches=sum((32*x['rows']+4095)//4096 for x in graphs.values());groups=sum(((32*x['rows']+4095)//4096+15)//16 for x in graphs.values())
assert (rows,cells,batches,groups)==(12999004,415968128,101559,6352)
assert pol['schema_version']==6 and pol['batched']['group_batches']==16 and pol['batched']['max_body_bytes']==1024
paths=[r['path'] for k,r in refs.items() if k!='archive_transport']
assert all(p.isascii() and len(p.encode())<=512 for p in paths)
assert all(k.isascii() and len(k)<=128 for k in refs)
ints=[]
def ints_walk(x):
 if type(x) is int:ints.append(x)
 elif type(x) is dict:
  for v in x.values():ints_walk(v)
 elif type(x) is list:
  for v in x:ints_walk(v)
for k in ('typed_payload','archive_policy','mcm_policy','pair_policy','execution_job'):ints_walk(selected[k])
assert all(0<=i<2**63 for i in ints)
# Actual source path templates: owner.identity and graph hashes are fixed 64 hex bytes.
group_base=ROOT/'research_artifacts/onchain_batched_offload'/('f'*64)/('mcm-'+'f'*64)
future=[group_base/'preserve/00006351/recover',group_base/'preserve/00006351/semantic/tree/00101558.complete.json',group_base/'final/00006351/recover',group_base/'final/accepted-coverage.json']
assert all(str(p).isascii() and len(str(p).encode())<=512 for p in future)
# Retained grouped control namespace from source capacity; deliberately count full original journal as well as grouped controls.
projected={'original_journal_files_conservative':3*batches,'numeric_summary_files':batches,'group_control_files':23*groups+7,'group_work_directories':7*groups+21,'other_files_directories_allowance':20000}
projected_total=sum(projected.values())
latest=samples[-1].get('observation') or {};baseentries=latest.get('entries');assert baseentries is None or baseentries+projected_total<1000000
claims=[]
for p in sorted((ROOT/'research_runs').glob('eth-paper-*/claim.json')):
 terms=[n for n in ('failed.json','complete.json','completed.json') if (p.parent/n).is_file()]
 claims.append({'experiment':p.parent.name,'terminal_names':terms})
# Process comm only: no environment, credentials or unbounded command-line dump.
procs=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  comm=(p/'comm').read_text().strip()
  if any(t in comm.lower() for t in ('python','native','pilot')):
   procs.append({'pid':int(p.name),'comm':comm,'self':int(p.name)==os.getpid()})
 except (OSError,ProcessLookupError):pass
namespace={str(ROOT/'research_runs'/exp):os.path.lexists(ROOT/'research_runs'/exp),str(ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/exp):os.path.lexists(ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/exp)}
result={'status':'READ_ONLY_CONDITIONAL_ENTRY_EVIDENCE','sample_epoch':start,'experiment':exp,'selected_public_bound_inputs':len(selected),'private_role_body_opened':False,'metadata_refs_count':len(refs),'public_ref_max_path_bytes':max(map(len,paths)),'input_name_max_bytes':max(map(len,refs)),'control_integer_count':len(ints),'control_integer_max':max(ints),'rows':rows,'cells':cells,'batches':batches,'groups':groups,'group_batches':16,'journal_body_limit':1024,'derived_future_path_examples':[str(p) for p in future],'derived_future_max_bytes':max(len(str(p)) for p in future),'samples':samples,'filesystem':{'available_bytes':fs.f_bavail*fs.f_frsize,'free_inodes':fs.f_favail,'fragment_bytes':fs.f_frsize},'memory':mem,'projected_entries_conservative':projected,'projected_entries_total':projected_total,'baseline_plus_projected_entries':None if baseentries is None else baseentries+projected_total,'capacity_join':{'accepted_increment_allocated':cap['physical_join']['increment_allocated'],'accepted_increment_logical':cap['physical_join']['increment_logical'],'current_available_after_increment_and_floor':fs.f_bavail*fs.f_frsize-cap['physical_join']['increment_allocated']-job['resources']['disk_floor_bytes'],'current_union_allocated_plus_increment':latest.get('allocated_bytes',0)+cap['physical_join']['increment_allocated'],'current_union_logical_plus_increment':latest.get('logical_file_bytes',0)+cap['physical_join']['increment_logical']},'namespaces_exist':namespace,'scoped_claim_terminal_names':claims,'process_comm_candidates':procs,'limits':job['resources'],'qualifications':['Source/model conditional projection; extra 20000 entries is explicit allowance, not a proven exhaustive failure-path namespace bound.','Actual descriptor-dependent complete/pending bodies remain runtime enforced <=1024; source limit is not advance proof of every body.','Derived group route examples are not a complete generated pathname inventory; actual future semantic and transport paths remain runtime constrained.','Process names cannot establish absence of active native work or competing writers; classification and Root current launch state must join.','Claim terminal filename presence is metadata evidence only; no body/status validation or claim mutation.','No private transport inspection, remote reservation or quota proof; no atomic filesystem snapshot or writer exclusion.','Sampling guard retains exact configured limits; allocations and memory can change after observation.']}
(OUT/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'SOURCE_PINS01.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','selected_public_bound_inputs','capacity_join','baseline_plus_projected_entries','namespaces_exist','memory','process_comm_candidates')}))
