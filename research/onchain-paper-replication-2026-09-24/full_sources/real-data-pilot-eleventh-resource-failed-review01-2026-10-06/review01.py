"""Bounded D11 failure review; adapted from accepted D2 checks, no empirical imports."""
from pathlib import Path
import hashlib,json,stat
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
H=F/'real-data-pilot-eleventh-resource-failed-review01-2026-10-06';D=F/'real-data-pilot-final11-2026-10-06'
N='eth-paper-real-data-end-to-end-resource-20261006-11';SOURCE='2860e953bf454074f3a94c25f8819c90066d4170'
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
IDENTITY='17cc8f89a6f49bd6e236bdb7976fc85628c9f6db37ec7297226481736a261a0f'
J=Path('research_artifacts/onchain_representations')/IDENTITY/N
X=Path('research_artifacts/archive-dispatch-ethpilot-20261006-11')
files=[];directories=[]
for base in (C,A,L,J,X):
 for p in sorted([base,*base.rglob('*')]):
  s=p.lstat();assert (R/p).resolve(strict=True)==R/p and not stat.S_ISLNK(s.st_mode)
  if stat.S_ISDIR(s.st_mode):directories.append({'path':str(p),'kind':'directory','mode':stat.S_IMODE(s.st_mode)})
  else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;files.append(p)
dynamic=('launch-attempt01.json','ROOT_ACTIVE01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ROOT_TERMINAL01.json','REMOTE_CONFIRMATION01.json')
files.extend(D/n for n in dynamic)
assert len(files)==len(set(files))==43 and len(directories)==13
rows=[]
for p in sorted(files):
 b=raw(p);s=p.lstat();rows.append({'path':str(p),'kind':'regular','bytes':len(b),'sha256':sha(p),'mode':stat.S_IMODE(s.st_mode),'nlink':s.st_nlink,'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]})
claim=read(C/'claim.json');failed=read(C/'failed.json');summary=read(C/'outputs/pilot-summary.json');root=read(D/'ROOT_TERMINAL01.json')
assert claim['experiment_id']==failed['experiment_id']==root['experiment']==N
assert claim['source']==SOURCE and claim['effective_attempt_budget']==82
assert claim['bindings'] is None and claim['bindings_sha256'] is None
assert sha(C/'claim.json')==failed['claim_sha256']=='49b2340a1bd776d06d05aca9898c019245649039ebfff3cb0e3556c8e0d18024'
reason='ValueError: imported numerical source closure differs'
assert failed['status']=='failed' and failed['reason']==root['failure_reason']==reason
assert not (C/'complete.json').exists() and not (C/'artifacts').exists() and not (P/'sources'/N).exists()
assert set(claim['experiment']['outputs'])==set(failed['output_sha256']) and len(failed['output_sha256'])==8
for n,pin in failed['output_sha256'].items():assert sha(C/'outputs'/n)==pin
ledger=read(C/'outputs/cell-ledger.json');assert ledger==[summary['cell']] and ledger[0]['status']=='failed' and ledger[0]['reason']==reason
t=summary['throughput'];assert t['graph_denominator']==len(t['graphs'])==t['unavailable_graphs']==7
assert all(t[k]==0 for k in ('complete_graphs','failed_graphs','verified_completed_motif_cells','verified_completed_nodes','attempted_mcm_seconds','paper_financial_fits'))
assert all(g['status']=='unavailable' and g['reason']=='not_attempted_after_failure' and g['completed_motif_cells'] is None and g['completed_nodes'] is None and g['elapsed_seconds'] is None for g in t['graphs'])
assert sum(g['expected_motif_cells'] for g in t['graphs'])==415968128
assert summary['training'] is None and summary['events']==[{'elapsed_seconds':181.09793729000012,'phase':'original_import'}] and summary['retained_target_count']==0 and summary['financial_fit_complete'] is False
assert read(C/'outputs/resource-binding.json')==read(C/'outputs/resource-journal.json')=={'kind':'real-data-import-training-pilot-v1','reason':reason,'resource_only':True,'schema_version':1,'status':'failed'}
assert list(Path('research_artifacts/onchain_representations').glob('*/'+N))==[J] and read(A/'unsealed-journals.json')==[]
jc,jf,jo,js=(read(J/n) for n in ('claim.json','failed.json','owner.json','start.json'))
assert jc['owner']==jf['owner']==js['owner']==jo and jo['experiment']==N and jo['source_commit']==SOURCE and jo['workflow_identity']==IDENTITY
assert jc['resource_only'] and jf['status']=='failed' and jf['events']==[] and jf['reason']==reason
assert jf['workflow_identity'] is None and js['workflow_identity'] is None
assert set(jf['required_graphs'])=={g['graph_hash'] for g in t['graphs']}
imp=read(J/'compact/dictionary-import/import-complete.json');ii=read(J/'compact/dictionary-import/intent.json')
assert imp['intent_sha256']==sha(J/'compact/dictionary-import/intent.json') and imp['owner']==ii['owner']
assert imp['current_matching_pairs']==0 and imp['historical_work_recomputed'] is False and imp['numeric']['mcm_execution_admitted'] is False and imp['numeric']['owner_stage_completed'] is False
assert imp['execution']['current_source']==SOURCE and len(imp['numeric']['ordered_motifs'])==32
intent=read(X/'intent.json');xt=read(X/'terminal.json');receipt=read(C/'outputs/archive-receipt.json')
assert read(C/'outputs/archive-terminal.json')==xt and xt['status']=='failed' and intent['execution_admitted'] is False
assert intent['claim_sha256']==sha(C/'claim.json') and intent['source_commit']==SOURCE and intent['experiment']==N
assert receipt['context']==str(X) and receipt['intent_sha256']==xt['intent_sha256']==sha(X/'intent.json')
assert xt['spent']=={'commands':0,'logical_bytes':0,'rounded_bytes':0}
assert all(v['acknowledged_records']==v['acknowledged_encoded_bytes']==v['shards']==0 for v in xt['control_history'].values())
assert all(not any((X/n).iterdir()) for n in ('controls','diagnostic-controls','diagnostics'))
assert read(X/'close-failed.json')['intent_sha256']==sha(X/'intent.json')
guard=read(A/'guard/final.json');owner=read(A/'owner.json');launch=read(A/'launch.json');io=read(D/'ROOT_IO_CLOSED01.json');storage=read(D/'FINAL_STORAGE01.json');obs=read(A/'observer.json')
assert sha(A/'guard/final.json')=='e90964c9c51742bec231d77a763749006197122d4e0ced166d3cbcf6199aaf8a'
assert root['root_session']==92163
assert root['actual_root_exit']==root['actual_parent_exit']==io['actual_parent_exit_code']==root['native_child_exit']==guard['child_exit_code']==1
assert guard['elapsed_seconds']==root['elapsed_seconds']==1106.3349451599997
assert guard['cleanup_verified'] is True and root['cleanup_verified'] is True and guard['cleanup_stop_returncode']==0
assert all(guard['memory_events'][k]==0 for k in ('max','oom','oom_kill','oom_group_kill'))
assert io['outer_log_handles_closed'] is True and io['supervisor_reaped'] is True
assert io['supervisor_pid']==launch['supervisor_pid']==owner['supervisor_pid']==185004 and launch['nonce']==owner['nonce']
assert launch['source_commit']==owner['source_commit']==storage['source']==SOURCE and owner['monitor_pid']==guard['monitor_pid']==185318
for k,n in (('guard','guard/final.json'),('launch','launch.json'),('owner','owner.json')):assert storage['original_metadata_sha256'][k]==sha(A/n)
assert storage['actual_current_cgroup_absent'] and storage['original_monitor_process_absent'] and storage['actual_current_unit_properties']['MainPID']=='0' and storage['actual_current_unit_properties']['ControlGroup']==''
assert not Path(guard['cgroup']).exists()
assert obs['terminal_sha256']==sha(C/'failed.json') and obs['owner_sha256']==sha(A/'owner.json')
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
pids.update(int(k) for k in root['all_recorded_pids_absent']);assert len(pids)==7
assert all(not Path('/proc',str(pid)).exists() for pid in pids)
trace=raw(A/'guard/child.log').decode();assert 'imported_mcm_identity.py\", line 114, in sources' in trace and reason in trace
assert 'history audit stale' in trace and 'history audit poisoned' in trace
caller=Path('tradingagents/research/onchain_replication/real_pilot_import_caller.py');dispatch=Path('tradingagents/research/onchain_replication/imported_mcm_identity.py')
cs=raw(caller).decode();ds=raw(dispatch).decode()
assert cs.index("checked = [Target(execution,g,k) for k,g in graphs.items()]")<cs.index("for target in checked:")<cs.index("compact_mcm._prepare(target,target.key")
assert 'real_pilot_import_caller.py\", line 450, in execute' in trace and 'compact_mcm.py\", line 109, in _prepare' in trace
assert "job.required_sources()|{KERNEL,HELPER}" in ds and "expected is not None and file_hash(run.admission.root/name)==expected" in ds
mismatches=[]
for name in ('research/onchain-paper-replication-2026-09-24/full_sources/original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py','research/onchain-paper-replication-2026-09-24/full_sources/pair-workload-2026-09-30/workload.py'):
 assert name not in claim['experiment']['source_files']
 mismatches.append({'path':name,'registered':None,'actual_sha256':sha(Path(name))})
assert mismatches==root['source_closure_mismatches'] and root['all_seven_target_constructors_returned'] is True
policy_path=Path(claim['inputs']['imported_authority_lease']['path']);assert sha(policy_path)==claim['inputs']['imported_authority_lease']['sha256']
assert read(policy_path)['max_stale_ms']==30000
remote=read(D/'REMOTE_CONFIRMATION01.json');assert remote['actual_remote_HEAD']==remote['source']==SOURCE and remote['actual_ls_remote_exit_code']==remote['push_exit_code']==0
selection={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'files':rows,'directories':directories,'regular_count':len(rows),'directory_count':len(directories),'original_regular_bytes':sum(r['bytes'] for r in rows),'absent_source_namespace':str(P/'sources'/N),'dynamic_entry_records':[str(D/n) for n in dynamic],'scope':'Exact actual11 failed-pilot increment: all five owned roots and six D11 entry/closure records; typed directory names/modes included.','exclusions':['Scientific arrays/raw ledgers/runtime/private connection bodies','Earlier committed source/gate/preparation/input records','Earlier closed archive namespaces and workflow journals','Shared parent directories outside five owned roots'],'qualification':'Original bodies retained; selection permits exact archive construction, not deletion, transport or scientific relaunch. Actual external recovery still required.'}
bp=write('INCREMENT_SELECTION01.json',selection)
outcome={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'claim_sha256':sha(C/'claim.json'),'increment_selection':ref(bp),'evidence':{str(p):sha(p) for p in sorted(files)},'reviewed_source':[ref(caller),ref(dispatch)],'source_closure_mismatches':mismatches,'all_seven_target_constructors_returned':True,'retained_target_count_qualification':'Original summary retains0; controlflow at caller450 independently proves the seven-element constructor list returned. Neither means any MCM stage completed.','root_actual_exit':{'exit_code':1,'session':92163,'terminal_chunk':'fea8c2'},'native':{'elapsed_seconds':guard['elapsed_seconds'],'child_exit_code':1,'cleanup_verified':True,'cleanup_stop_returncode':0,'memory_events':guard['memory_events'],'last_unit_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes']},'failure':{'reason':reason,'source_location':'tradingagents/research/onchain_replication/imported_mcm_identity.py:114','caller_location':'tradingagents/research/onchain_replication/real_pilot_import_caller.py:450','impact':'All seven Target constructors returned before compact_mcm._prepare reached Target.sources: required KERNEL source lacks a source_files registration pin. HELPER is also absent from the same required closure, independently checked but not necessarily reached before the first raise. Genuine11 attempt82 is spent; no MCM, update or fit completed.','action':'Verify the exact existing helper provenance and include the complete required closure in a separately reviewed fresh registration; preserve11 and all earlier identities. Do not bypass source validation.'},'denominator':{'registered_cells':1,'declared_outputs':8,'retained_outputs':8,'unavailable_outputs':[],'worker_failed_cell_ledger':ledger,'supervisor_postmortem_cells':read(A/'postmortem-cells.json'),'graphs':7,'MCM_completed':0,'MCM_failed':0,'MCM_unavailable_not_attempted':7,'verified_completed_motif_cells':0,'training':None,'financial_fits':0},'binding_distinction':{'claim_bindings':None,'claim_bindings_sha256':None,'output_resource_journal':'Failure placeholder distinct from retained genuine workflow journal.','actual11_journal_matches':[str(J)],'unsealed_journals':[]},'current_cleanup':{'selected_pid_exists':{str(pid):False for pid in sorted(pids)},'recorded_cgroup_absent':True,'lifetime_process_history':None,'native_unit_properties':'Original final-storage/guard readbacks reused; no native/systemctl call.'},'archive_context':{'spent':xt['spent'],'control_history':xt['control_history'],'secondary_cleanup_diagnostics':['history audit stale','history audit poisoned'],'close_failed_retained':True},'timing':{'native_seconds':1106.3349451599997,'scope_seconds':summary['throughput']['scope_elapsed_seconds'],'original_import_events':summary['events'],'max_stale_ms':30000,'policy':ref(policy_path),'exact_failure_call_seconds':None,'callback_duration_breakdown':None,'failure_boundary':'Target.sources:114 refused missing required registration pins after all seven Target constructors returned. No global freshness or callback-saving claim follows.'},'dictionary_import':{'current_matching_pairs':0,'historical_work_recomputed':False,'mcm_execution_admitted':False,'owner_stage_completed':False},'disposition':'Permanent FAILED/spent11; no refund, transfer, relaunch or scientific credit.','null_preservation':'Original claim/training/graph nulls and separate unavailable supervisor postmortem retained.','not_tested':['Numerical arrays/raw/price/labels/runtime/private connection bodies; population output hash only.','No experiment, transport, network, native or claim invocation.','Return/cashflow, leakage, fees/funding, predictive performance and full-pilot capacity.','External recovery and POSIX reconstruction not yet accepted.']}
op=write('OUTCOME_REVIEW01.json',outcome)
mp=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','experiment':N,'files':[ref(H/'review01.py'),ref(bp),ref(op)]})
print(json.dumps({'outcome':ref(op),'selection':ref(bp),'manifest':ref(mp),'regulars':len(rows),'directories':len(directories),'bytes':selection['original_regular_bytes'],'selected_absent_pids':len(pids),'decision':'accepted'},sort_keys=True))
