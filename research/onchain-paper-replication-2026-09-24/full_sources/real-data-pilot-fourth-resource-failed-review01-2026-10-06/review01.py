"""Bounded D4 failure review; adapted from accepted D2 checks, no empirical imports."""
from pathlib import Path
import hashlib,json,stat
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
H=F/'real-data-pilot-fourth-resource-failed-review01-2026-10-06';D=F/'real-data-pilot-final04-2026-10-06'
N='eth-paper-real-data-end-to-end-resource-20261006-04';SOURCE='cb12e8237a2e87536e68a9d3e4a43ddb06191ea9'
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
dynamic=('launch-attempt01.json','ROOT_ACTIVE01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ROOT_TERMINAL01.json','REMOTE_CONFIRMATION01.json')
files.extend(D/n for n in dynamic)
assert len(files)==len(set(files))==30 and len(directories)==5
rows=[]
for p in sorted(files):
 b=raw(p);s=p.lstat();rows.append({'path':str(p),'kind':'regular','bytes':len(b),'sha256':sha(p),'mode':stat.S_IMODE(s.st_mode),'nlink':s.st_nlink,'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]})
claim=read(C/'claim.json');failed=read(C/'failed.json');summary=read(C/'outputs/pilot-summary.json');root=read(D/'ROOT_TERMINAL01.json')
assert claim['experiment_id']==failed['experiment_id']==root['identity']==N
assert claim['source']==root['source']==SOURCE and claim['effective_attempt_budget']==75
assert claim['bindings'] is None and claim['bindings_sha256'] is None
assert sha(C/'claim.json')==failed['claim_sha256']=='1cd093cc10b9e6c761fa70d813c11a798054cac55da699616bc669d2a94f4955'
reason='ValueError: archive transport namespace already reserved'
assert failed['status']=='failed' and failed['reason']==root['reason']==reason
assert not (C/'complete.json').exists() and not (C/'artifacts').exists() and not (P/'sources'/N).exists()
assert set(claim['experiment']['outputs'])-set(failed['output_sha256'])=={'archive-receipt.json','archive-terminal.json'} and len(failed['output_sha256'])==6
assert not (C/'outputs/archive-receipt.json').exists() and not (C/'outputs/archive-terminal.json').exists()
for n,pin in failed['output_sha256'].items():assert sha(C/'outputs'/n)==pin
ledger=read(C/'outputs/cell-ledger.json');assert ledger==[summary['cell']] and ledger[0]['status']=='failed' and ledger[0]['reason']==reason
t=summary['throughput'];assert t['graph_denominator']==len(t['graphs'])==t['unavailable_graphs']==7
assert all(t[k]==0 for k in ('complete_graphs','failed_graphs','verified_completed_motif_cells','verified_completed_nodes','attempted_mcm_seconds','paper_financial_fits'))
assert all(g['status']=='unavailable' and g['reason']=='not_attempted_after_failure' and g['completed_motif_cells'] is None and g['completed_nodes'] is None and g['elapsed_seconds'] is None for g in t['graphs'])
assert sum(g['expected_motif_cells'] for g in t['graphs'])==415968128
assert summary['training'] is None and summary['events']==[] and summary['retained_target_count']==0 and summary['financial_fit_complete'] is False
assert read(C/'outputs/resource-binding.json')==read(C/'outputs/resource-journal.json')=={'kind':'real-data-import-training-pilot-v1','reason':reason,'resource_only':True,'schema_version':1,'status':'failed'}
assert list(Path('research_artifacts/onchain_representations').glob('*/'+N))==[] and read(A/'unsealed-journals.json')==[]
guard=read(A/'guard/final.json');owner=read(A/'owner.json');launch=read(A/'launch.json');io=read(D/'ROOT_IO_CLOSED01.json');storage=read(D/'FINAL_STORAGE01.json');obs=read(A/'observer.json')
assert sha(A/'guard/final.json')==root['guard_sha256']=='2133248e4188a3caee2ad4241b40364957250c3de0406565df03ee752a680f91'
assert root['root_session']==61944 and root['root_terminal_chunk']=='231f5f'
assert root['actual_root_exit']==root['actual_parent_exit']==io['actual_parent_exit_code']==root['native_child_exit']==guard['child_exit_code']==1
assert guard['elapsed_seconds']==root['native_elapsed_seconds']==420.58513276299993
assert guard['cleanup_verified'] is True and root['cleanup_verified'] is True and guard['cleanup_stop_returncode']==0
assert all(guard['memory_events'][k]==0 for k in ('max','oom','oom_kill','oom_group_kill'))
assert io['outer_log_handles_closed'] is True and io['supervisor_reaped'] is True
assert io['supervisor_pid']==launch['supervisor_pid']==owner['supervisor_pid']==20669 and launch['nonce']==owner['nonce']
assert launch['source_commit']==owner['source_commit']==storage['source']==SOURCE and owner['monitor_pid']==guard['monitor_pid']==20950
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
trace=raw(A/'guard/child.log').decode();assert 'archive_dispatch.py", line 249, in __init__' in trace and reason in trace
caller=Path('tradingagents/research/onchain_replication/real_pilot_import_caller.py');dispatch=Path('tradingagents/research/onchain_replication/archive_dispatch.py')
cs=raw(caller).decode();assert cs.index('archive_context=archive_dispatch.Context(archive_plan)')<cs.index('journal,bound = resource_binding.open_first')
assert "require(not os.path.lexists(self.root),'archive transport namespace already reserved')" in raw(dispatch).decode()
assert Path('research_artifacts/archive-dispatch-ethpilot-20261006-02').is_dir()
remote=read(D/'REMOTE_CONFIRMATION01.json');assert remote['actual_remote_head']==remote['source']==SOURCE and remote['push_exit']==remote['readback_exit']==0
selection={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'files':rows,'directories':directories,'regular_count':len(rows),'directory_count':len(directories),'original_regular_bytes':sum(r['bytes'] for r in rows),'absent_source_namespace':str(P/'sources'/N),'dynamic_entry_records':[str(D/n) for n in dynamic],'scope':'Exact actual04 failed-pilot increment: all three owned roots and six D4 entry/closure records; typed directory names/modes included.','exclusions':['Scientific arrays/raw ledgers/runtime/private connection bodies','Earlier committed source/gate/preparation/input records','Existing closed02 archive namespace; no04 workflow journal exists','Shared parent directories outside three owned roots'],'qualification':'Original bodies retained; selection permits exact archive construction, not deletion, transport or scientific relaunch. Actual external recovery still required.'}
bp=write('INCREMENT_SELECTION01.json',selection)
outcome={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'claim_sha256':sha(C/'claim.json'),'increment_selection':ref(bp),'evidence':{str(p):sha(p) for p in sorted(files)},'reviewed_source':[ref(caller),ref(dispatch)],'root_actual_exit':{'exit_code':1,'session':61944,'terminal_chunk':'231f5f'},'native':{'elapsed_seconds':guard['elapsed_seconds'],'child_exit_code':1,'cleanup_verified':True,'cleanup_stop_returncode':0,'memory_events':guard['memory_events'],'last_unit_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes']},'failure':{'reason':reason,'source_location':'tradingagents/research/onchain_replication/archive_dispatch.py:249','caller_location':'tradingagents/research/onchain_replication/real_pilot_import_caller.py:415','impact':'Existing transport namespace rejected before resource_binding.open_first, Owner creation, MCM or training; genuine04 attempt75 is spent.','action':'Separately registered successor must bind/precheck exact unused local archive namespace and remote transport identity before native work. Preserve04 and existing02; never delete the old namespace to force reuse.'},'denominator':{'registered_cells':1,'declared_outputs':8,'retained_outputs':6,'unavailable_outputs':['archive-receipt.json','archive-terminal.json'],'unavailable_output_reason':'Archive Context rejected before construction; no receipt or terminal fabricated.','worker_failed_cell_ledger':ledger,'supervisor_postmortem_cells':read(A/'postmortem-cells.json'),'graphs':7,'MCM_completed':0,'MCM_failed':0,'MCM_unavailable_not_attempted':7,'verified_completed_motif_cells':0,'training':None,'financial_fits':0},'binding_distinction':{'claim_bindings':None,'claim_bindings_sha256':None,'output_resource_journal':'Failure placeholder; no actual workflow journal created.','actual04_journal_matches':[],'unsealed_journals':[]},'current_cleanup':{'selected_pid_exists':{str(pid):False for pid in sorted(pids)},'recorded_cgroup_absent':True,'lifetime_process_history':None,'native_unit_properties':'Original final-storage/guard readbacks reused; no native/systemctl call.'},'disposition':'Permanent FAILED/spent04; no refund, transfer, relaunch or scientific credit.','null_preservation':'Original claim/training/graph nulls and separate unavailable supervisor postmortem retained.','not_tested':['Numerical arrays/raw/price/labels/runtime/private connection bodies; population output hash only.','No experiment, transport, network, native or claim invocation.','Return/cashflow, leakage, fees/funding, predictive performance and full-pilot capacity.','External recovery and POSIX reconstruction not yet accepted.']}
op=write('OUTCOME_REVIEW01.json',outcome)
mp=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','experiment':N,'files':[ref(H/'review01.py'),ref(bp),ref(op)]})
print(json.dumps({'outcome':ref(op),'selection':ref(bp),'manifest':ref(mp),'regulars':len(rows),'directories':len(directories),'bytes':selection['original_regular_bytes'],'selected_absent_pids':len(pids),'decision':'accepted'},sort_keys=True))
