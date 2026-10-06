"""Bounded D6 failure review; adapted from accepted D2 checks, no empirical imports."""
from pathlib import Path
import hashlib,json,stat
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
H=F/'real-data-pilot-sixth-resource-failed-review01-2026-10-06';D=F/'real-data-pilot-final06-2026-10-06'
N='eth-paper-real-data-end-to-end-resource-20261006-06';SOURCE='375dc8bc6745b2718fbdcebbeb22ed2e29560c30'
C=Path('research_runs')/N;P=Path('research_artifacts/onchain-paper-replication-2026-09-24');A=P/'runs'/N;L=P/'pilot-parent'/N
cache={}
def raw(p):
 p=Path(p)
 if p not in cache:
  q=R/p;s=q.lstat();assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
  b=q.read_bytes();z=q.lstat();assert len(b)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
  cache[p]=b
 return cache[p]
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):
 assert Path(p).name!='resource-population.json'
 return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':sha(p)}
def write(n,v):
 p=H/n
 with p.open('x') as f:f.write(json.dumps(v,sort_keys=True,indent=2)+'\n')
 return p
files=[];directories=[]
for base in (C,A,L):
 for p in sorted([base,*base.rglob('*')]):
  s=p.lstat();assert (R/p).resolve(strict=True)==R/p and not stat.S_ISLNK(s.st_mode)
  if stat.S_ISDIR(s.st_mode):directories.append({'path':str(p),'kind':'directory','mode':stat.S_IMODE(s.st_mode)})
  else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;files.append(p)
dynamic=('launch-attempt01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ROOT_TERMINAL01.json','REMOTE_CONFIRMATION01.json')
files.extend(D/n for n in dynamic)
assert len(files)==len(set(files))==23 and len(directories)==5
rows=[]
for p in sorted(files):
 b=raw(p);s=p.lstat();rows.append({'path':str(p),'kind':'regular','bytes':len(b),'sha256':sha(p),'mode':stat.S_IMODE(s.st_mode),'nlink':s.st_nlink,'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]})
claim=read(C/'claim.json');failed=read(C/'failed.json');root=read(D/'ROOT_TERMINAL01.json')
assert claim['experiment_id']==failed['experiment_id']==root['identity']==N
assert claim['source']==root['source']==SOURCE and claim['effective_attempt_budget']==77
assert claim['bindings'] is None and claim['bindings_sha256'] is None
assert sha(C/'claim.json')==failed['claim_sha256']=='b358943fbcd2e24fe10b4c10875516dca14f1d0da6babd88c58482869a89b3f6'
reason='SystemExit: owned execution interrupted; never relaunch this identity'
scan_reason='ValueError: experiment born during scan; complete new observation required'
assert failed['status']=='failed' and failed['reason']==reason and failed['output_sha256']=={}
assert len(claim['experiment']['outputs'])==8 and claim['experiment']['cells']==['real-eth-one-update']
assert not (C/'complete.json').exists() and not (C/'artifacts').exists() and not (P/'sources'/N).exists()
assert (C/'outputs').is_dir() and list((C/'outputs').iterdir())==[]
assert list(Path('research_artifacts/onchain_representations').glob('*/'+N))==[] and read(A/'unsealed-journals.json')==[]
assert not Path('research_artifacts/archive-dispatch-ethpilot-20261006-06').exists() and not (D/'ROOT_ACTIVE01.json').exists()
guard=read(A/'guard/final.json');owner=read(A/'owner.json');launch=read(A/'launch.json');io=read(D/'ROOT_IO_CLOSED01.json');storage=read(D/'FINAL_STORAGE01.json');obs=read(A/'observer.json')
assert sha(A/'guard/final.json')==root['guard_sha256']=='6883b5756f33cb8f3c4e8e36564d95c8a81d2ac3d51918b764e730906fcb6058'
assert root['root_session']==62519 and root['root_terminal_chunk']=='2b8b45'
assert root['actual_root_exit']==root['actual_parent_exit']==io['actual_parent_exit_code']==1
assert guard['child_exit_code'] is None
assert read(A/'guard/child_exit.json')['exit_code']==125 and read(A/'guard/child_exit.json')['reason']=='signal'
assert guard['limit_reason']==scan_reason
assert guard['elapsed_seconds']==6.66460862599979
assert guard['cleanup_verified'] is True and root['cleanup_verified'] is True and guard['cleanup_stop_returncode']==0
assert all(guard['memory_events'][k]==0 for k in ('max','oom','oom_kill','oom_group_kill'))
assert io['outer_log_handles_closed'] is True and io['supervisor_reaped'] is True
assert io['supervisor_pid']==launch['supervisor_pid']==owner['supervisor_pid']==124575 and launch['nonce']==owner['nonce']
assert launch['source_commit']==owner['source_commit']==storage['source']==SOURCE and owner['monitor_pid']==guard['monitor_pid']==124866
for k,n in (('guard','guard/final.json'),('launch','launch.json'),('owner','owner.json')):assert storage['original_metadata_sha256'][k]==sha(A/n)
assert storage['actual_current_cgroup_absent'] and storage['original_monitor_process_absent'] and storage['actual_current_unit_properties']['MainPID']=='0' and storage['actual_current_unit_properties']['ControlGroup']==''
assert not Path(guard['cgroup']).exists()
assert obs['terminal_sha256']==sha(C/'failed.json')==root['research_failed_sha256'] and obs['owner_sha256']==sha(A/'owner.json')
for p,pin in obs['evidence_sha256'].items():assert sha(A/p)==pin
pids=set()
def collect(v):
 if isinstance(v,dict):
  for k,x in v.items():
   if (k=='pid' or k.endswith('_pid')) and type(x) is int and x>0:pids.add(x)
   else:collect(x)
 elif isinstance(v,list):
  for x in v:collect(x)
for v in (guard,owner,launch,read(A/'guard/child_exit.json'),read(A/'guard/cpu_ready.json')):collect(v)
assert all(not Path('/proc',str(pid)).exists() for pid in pids)
assert raw(A/'guard/child.log').decode().strip()=='owned execution interrupted; never relaunch this identity'
source=Path('tradingagents/research/onchain_replication/real_pilot_storage.py')
assert "if born is None and after is not None:raise ValueError('experiment born during scan; complete new observation required')" in raw(source).decode()
remote=read(D/'REMOTE_CONFIRMATION01.json');assert remote['actual_remote_head']==remote['actual_local_head']==SOURCE and remote['push_exit']==remote['readback_exit']==0
selection={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'files':rows,'directories':directories,'regular_count':len(rows),'directory_count':len(directories),'original_regular_bytes':sum(r['bytes'] for r in rows),'absent_source_namespace':str(P/'sources'/N),'dynamic_entry_records':[str(D/n) for n in dynamic],'scope':'Exact actual06 failed-pilot increment: all three owned roots and five D6 entry/closure records; typed directory names/modes included.','exclusions':['Scientific arrays/raw ledgers/runtime/private connection bodies','Earlier committed source/gate/preparation/input records','All earlier closed archive namespaces; no06 workflow/archive namespace exists','Shared parent directories outside three owned roots'],'qualification':'Original bodies retained; selection permits exact archive construction, not deletion, transport or scientific relaunch. Actual external recovery still required.'}
bp=write('INCREMENT_SELECTION01.json',selection)
outcome={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'claim_sha256':sha(C/'claim.json'),'increment_selection':ref(bp),'evidence':{str(p):sha(p) for p in sorted(files)},'reviewed_source':[ref(source)],'root_actual_exit':{'exit_code':1,'session':62519,'terminal_chunk':'2b8b45'},'native':{'elapsed_seconds':guard['elapsed_seconds'],'original_guard_child_exit_code':None,'separate_child_exit_record':read(A/'guard/child_exit.json'),'cleanup_verified':True,'cleanup_stop_returncode':0,'memory_events':guard['memory_events'],'last_guard_unit_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes']},'failure':{'guard_reason':scan_reason,'worker_reason':reason,'source_location':'tradingagents/research/onchain_replication/real_pilot_storage.py:172','impact':'Experiment namespace birth between the pre-scan and post-scan checks raises a fatal ValueError; guard interrupts genuine claimed77 before any durable scientific output.','action':'A separately registered successor needs a bounded complete re-observation for this exact birth transition while retaining original aggregate budgets and rejecting replacement or repeated instability. Preserve06; no relaunch or cap change.'},'denominator':{'registered_cells':1,'declared_outputs':claim['experiment']['outputs'],'retained_outputs':[],'supervisor_postmortem_cells':read(A/'postmortem-cells.json'),'registered_graph_inputs':[k for k in claim['inputs'] if k.startswith('graph_')],'graph_completion_records':None,'MCM_completed':0,'training_updates':0,'financial_fits':0,'qualification':'All eight scientific outputs absent; no per-graph counts or timing are fabricated. One registered cell is retained as unavailable in supervisor postmortem.'},'absence':{'ROOT_ACTIVE01':True,'source_namespace':True,'workflow_journal':True,'archive_namespace':True,'scientific_outputs':True},'binding_distinction':{'claim_bindings':None,'claim_bindings_sha256':None},'current_cleanup':{'selected_pid_exists':{str(pid):False for pid in sorted(pids)},'recorded_cgroup_absent':True,'lifetime_process_history':None,'native_unit_properties':'Original final-storage/guard readbacks reused; no native/systemctl call.'},'disposition':'Permanent FAILED/spent06; no refund, transfer, relaunch or scientific credit.','null_preservation':'Original guard child exit remains null; separate child signal125 and actual parent/Root1 preserved without substitution. No missing scientific output fabricated.','not_tested':['No numerical/raw/graph/runtime/private bodies inspected.','No experiment, transport, network, native or claim invocation.','Return/cashflow, leakage, fees/funding, predictive performance, numerical graph-loading completeness and full-pilot capacity.','Actual external recovery and POSIX reconstruction not yet accepted.']}
op=write('OUTCOME_REVIEW01.json',outcome)
mp=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','experiment':N,'files':[ref(H/'review01.py'),ref(bp),ref(op)]})
print(json.dumps({'outcome':ref(op),'selection':ref(bp),'manifest':ref(mp),'regulars':len(rows),'directories':len(directories),'bytes':selection['original_regular_bytes'],'selected_absent_pids':len(pids),'decision':'accepted'},sort_keys=True))
