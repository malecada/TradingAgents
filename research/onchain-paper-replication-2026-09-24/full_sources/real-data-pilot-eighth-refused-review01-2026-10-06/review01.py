"""One bounded public08 preclaim-refusal review; no empirical imports or writes."""
from pathlib import Path
import hashlib,json,stat
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
H=F/'real-data-pilot-eighth-refused-review01-2026-10-06';D=F/'real-data-pilot-final08-2026-10-06'
N='eth-paper-real-data-end-to-end-resource-20261006-08';SOURCE='ab1f5907f68e723e8a311cab5f9484d9d9c43e82'
P=Path('research_artifacts/onchain-paper-replication-2026-09-24');A=P/'runs'/N;L=P/'pilot-parent'/N;C=Path('research_runs')/N
cache={};stats={}
def ident(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def raw(p):
 p=Path(p)
 if p not in cache:
  q=R/p;s=q.lstat();assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
  b=q.read_bytes();z=q.lstat();assert len(b)==s.st_size and ident(s)==ident(z) and s.st_mode==z.st_mode and s.st_nlink==z.st_nlink
  cache[p]=b;stats[p]=s
 return cache[p]
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':sha(p)}
def write(n,v):
 p=H/n
 with p.open('x') as f:f.write(json.dumps(v,sort_keys=True,indent=2)+'\n')
 return p
files=[];directories=[]
for base in (A,L):
 for p in sorted([base,*base.rglob('*')]):
  s=p.lstat();assert (R/p).resolve(strict=True)==R/p and not stat.S_ISLNK(s.st_mode)
  if stat.S_ISDIR(s.st_mode):directories.append({'path':str(p),'kind':'directory','mode':stat.S_IMODE(s.st_mode)})
  else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;files.append(p)
dynamic=('launch-attempt01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ROOT_TERMINAL01.json','REMOTE_CONFIRMATION01.json')
files.extend(D/n for n in dynamic)
assert len(files)==len(set(files))==16 and len(directories)==3
rows=[]
for p in sorted(files):
 b=raw(p);s=stats[p];rows.append({'path':str(p),'kind':'regular','bytes':len(b),'sha256':sha(p),'mode':stat.S_IMODE(s.st_mode),'nlink':s.st_nlink,'stat_identity':ident(s)})
root=read(D/'ROOT_TERMINAL01.json');guard=read(A/'guard/final.json');child=read(A/'guard/child_exit.json');ready=read(A/'guard/cpu_ready.json');owner=read(A/'owner.json');launch=read(A/'launch.json');observer=read(A/'observer.json');io=read(D/'ROOT_IO_CLOSED01.json');storage=read(D/'FINAL_STORAGE01.json');attempt=read(D/'launch-attempt01.json');remote=read(D/'REMOTE_CONFIRMATION01.json')
assert root['identity']==owner['experiment']==launch['experiment']==attempt['experiment']==storage['experiment']==N
assert root['source']==owner['source_commit']==launch['source_commit']==attempt['source']==storage['source']==remote['source']==remote['actual_remote_head']==SOURCE
assert root['root_exit']==root['actual_parent_exit']==io['actual_parent_exit_code']==1 and root['root_session']==53034 and root['root_terminal_chunk']=='91d189'
assert root['original_guard_child_exit'] is None and guard['child_exit_code'] is None
assert child['exit_code']==125 and child['reason']=='signal before release' and child['workload_pid'] is None
assert not (A/'guard/release.json').exists() and not C.exists() and not (P/'sources'/N).exists()
assert not list(Path('research_artifacts/onchain_representations').glob('*/'+N)) and not Path('research_artifacts/archive-dispatch-ethpilot-20261006-08').exists()
assert root['scientific_claim'] is None and root['scientific_outputs']==root['mcm_completed']==root['training_updates']==root['financial_fits']==0
assert attempt['effective_attempt_budget']==root['reserved_allowance_ceiling']==79
assert sha(A/'guard/final.json')==sha(A/'guard/live.json')==root['guard_sha256']=='7680a1add1809613841613cad047c20a953c284f2e351dabdbd370a16ebed8b1'
assert guard['elapsed_seconds']==root['native_elapsed_seconds']==27.419141170999865
assert guard['phase']=='failed' and guard['limit_reason']==root['reason']=='RuntimeError: host reserve fell during cgroup setup'
assert guard['host_mem_available_bytes']==9649569792 and guard['start_reserve_bytes']==9663676416 and guard['start_reserve_bytes']-guard['host_mem_available_bytes']==14106624
assert guard['cleanup_verified'] is True and guard['cleanup_stop_returncode']==0 and root['cleanup_verified'] is True
assert all(guard['memory_events'][k]==0 for k in ('max','oom','oom_kill','oom_group_kill'))
assert all(child['terminal_memory_snapshot']['memory_events'][k]==0 for k in ('max','oom','oom_kill','oom_group_kill'))
assert observer['status']=='not_admitted' and observer['owner_sha256']==sha(A/'owner.json')
for p,pin in observer['evidence_sha256'].items():assert sha(A/p)==pin
assert json.loads(raw(L/'stdout.log'))==observer and raw(L/'stderr.log')==raw(A/'guard/child.log')==b''
assert io['supervisor_reaped'] and io['outer_log_handles_closed'] and io['supervisor_pid']==launch['supervisor_pid']==owner['supervisor_pid']==221651
assert owner['monitor_pid']==guard['monitor_pid']==221952 and ready['pid']==222469 and launch['nonce']==owner['nonce']
assert guard['owner_identity']==owner
for k,n in (('guard','guard/final.json'),('launch','launch.json'),('owner','owner.json')):assert storage['original_metadata_sha256'][k]==sha(A/n)
assert storage['actual_current_cgroup_absent'] and storage['original_monitor_process_absent'] and storage['actual_current_unit_properties']['MainPID']=='0' and storage['actual_current_unit_properties']['ControlGroup']==''
assert storage['actual_current_unit_properties']['ExecMainStatus']=='125' and storage['actual_current_unit_properties']['Result']=='exit-code'
assert not Path(guard['cgroup']).exists()
pids={221651,221952,222469};assert all(not Path('/proc',str(pid)).exists() for pid in pids)
assert remote['push_exit_code']==remote['readback_exit_code']==remote['actual_preflight_exit_code']==0
source=Path('tradingagents/research/onchain_replication/resources.py');body=raw(source).decode()
assert body.index("raise RuntimeError('host reserve fell during cgroup setup')")<body.index("_native_atomic(receipt/'release.json'")
selection={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'files':rows,'directories':directories,'regular_count':len(rows),'directory_count':len(directories),'original_regular_bytes':sum(v['bytes'] for v in rows),'absent_source_namespace':str(P/'sources'/N),'absent_scientific_namespace':str(C),'dynamic_entry_records':[str(D/n) for n in dynamic],'scope':'Exact actual08 refused preclaim increment: complete owned monitor and outer-log roots plus five entry/closure records. All three typed directory names and modes included.','exclusions':['Private connection bodies, scientific arrays, runtime and historical raw stores','Previously committed preparation, gate, registration and source bodies','Shared parent directories outside the two owned roots'],'qualification':'Original bodies retained. Selection authorizes exact capture only, not deletion or relaunch; actual external recovery remains required.'}
sp=write('INCREMENT_SELECTION01.json',selection)
outcome={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'increment_selection':ref(sp),'evidence':{str(p):sha(p) for p in sorted(files)},'reviewed_source':[ref(source)],'root_actual_exit':{'exit_code':1,'session':53034,'terminal_chunk':'91d189'},'native':{'elapsed_seconds':guard['elapsed_seconds'],'original_guard_child_exit_code':None,'separate_child_exit':child['exit_code'],'separate_child_reason':child['reason'],'workload_pid':None,'cleanup_verified':True,'memory_events':guard['memory_events']},'failure':{'reason':root['reason'],'source_location':'tradingagents/research/onchain_replication/resources.py:607','impact':'Final setup recheck found host availability 14106624 bytes below fixed startup requirement; numerical release and scientific claim never occurred.','action':'Keep08 permanently closed/reserved at79. A successor requires fresh identity, preserved reservation, reviewed cumulative accounting and original resource eligibility; no lower threshold or relaunch of08.'},'denominator':{'registered_pilot_cells':1,'scientific_claim':None,'scientific_outputs':0,'graphs_required':7,'MCM_completed':0,'MCM_unavailable_before_release':7,'training_updates':0,'financial_fits':0,'scientific_worker_cell_ledger':None},'accounting_scope':{'reserved_preclaim_allowance':79,'genuine_claim_added':False,'qualification':'No accounting ledger was written or full historical claim census repeated. Actual preclaim refusal leaves previously accepted49 closed=33COMPLETE16FAILED unchanged; existing03 preclaim reserve also remains.'},'current_cleanup':{'selected_pid_exists':{str(pid):False for pid in sorted(pids)},'recorded_cgroup_absent':True,'unit_properties':storage['actual_current_unit_properties'],'lifetime_process_history':None},'resource_observation':{'available_at_guard_setup':guard['host_mem_available_bytes'],'required_startup_available':guard['start_reserve_bytes'],'shortfall_bytes':14106624,'kernel_peak_last_observed':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes'],'qualification':'Setup-only resource observations; no whole-pilot capacity, feature-generation throughput or training-time evidence.'},'disposition':'Permanent CLOSED_NATIVE_SETUP_REFUSAL_PRECLAIM/reserved79; no refund, transfer, relaunch or scientific credit.','null_preservation':'Guard child null remains unknown; separately recorded child125 and Root/Parent1 retained without synthetic substitution. Monitor owner does not constitute scientific Owner.','not_tested':['No financial experiment, registry or ledger mutation, native invocation or network operation.','No numerical arrays, runtime or private-body read; no return/cashflow/leakage/fees/funding/model correctness or full capacity claim.','Historical root terminal exit is corroborated by preserved parent exit receipt; tool transcript itself is not reconstructed.','External BYTE recovery and POSIX reconstruction not yet accepted.']}
op=write('OUTCOME_REVIEW01.json',outcome)
mp=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','experiment':N,'files':[ref(H/'review01.py'),ref(sp),ref(op)]})
print(json.dumps({'outcome':ref(op),'selection':ref(sp),'manifest':ref(mp),'regulars':len(rows),'directories':len(directories),'bytes':selection['original_regular_bytes'],'decision':'accepted'},sort_keys=True))
