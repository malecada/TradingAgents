"""Bounded D12 failure review; adapted from accepted D2 checks, no empirical imports."""
from pathlib import Path
import hashlib,json,stat
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
H=F/'real-data-pilot-twelfth-resource-failed-review01-2026-10-06';D=F/'real-data-pilot-final12-2026-10-06'
N='eth-paper-real-data-end-to-end-resource-20261006-12';SOURCE='4be0806f40f46a80866ffbd77252c56c5a708e14'
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
IDENTITY='ed80da61b74eef519c95e45b1832e260c7e28bef3679ce12b4e9b22df80b6b45'
J=Path('research_artifacts/onchain_representations')/IDENTITY/N
X=Path('research_artifacts/archive-dispatch-ethpilot-20261006-12')
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
assert claim['experiment_id']==failed['experiment_id']==root['identity']==N
assert claim['source']==SOURCE and claim['effective_attempt_budget']==83
assert claim['bindings'] is None and claim['bindings_sha256'] is None
assert sha(C/'claim.json')==failed['claim_sha256']=='4bac493bfaa8a1937945128564e97c9cb1ecbc84fcb94b3cbd95d3fd8d9ccf3f'
reason='ValueError: import lease: stale interval cannot refresh'
assert failed['status']=='failed' and failed['reason']==root['failed_reason']==reason
assert not (C/'complete.json').exists() and not (C/'artifacts').exists() and not (P/'sources'/N).exists()
assert set(claim['experiment']['outputs'])==set(failed['output_sha256']) and len(failed['output_sha256'])==8
for n,pin in failed['output_sha256'].items():assert sha(C/'outputs'/n)==pin
ledger=read(C/'outputs/cell-ledger.json');assert ledger==[summary['cell']] and ledger[0]['status']=='failed' and ledger[0]['reason']==reason
t=summary['throughput'];assert t['graph_denominator']==len(t['graphs'])==t['unavailable_graphs']==7
assert all(t[k]==0 for k in ('complete_graphs','failed_graphs','verified_completed_motif_cells','verified_completed_nodes','attempted_mcm_seconds','paper_financial_fits'))
assert all(g['status']=='unavailable' and g['reason']=='not_attempted_after_failure' and g['completed_motif_cells'] is None and g['completed_nodes'] is None and g['elapsed_seconds'] is None for g in t['graphs'])
assert sum(g['expected_motif_cells'] for g in t['graphs'])==415968128
assert summary['training'] is None and summary['events']==[{'elapsed_seconds':191.79207522400065,'phase':'original_import'}] and summary['retained_target_count']==0 and summary['financial_fit_complete'] is False
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
assert sha(A/'guard/final.json')=='92e16ce4fb8231366a012a28a5253e39d196a1135f815a26ae78a47a8490e005'
assert root['root_session_id']==90344
assert root['actual_root_exit_code']==root['actual_parent_exit_code']==io['actual_parent_exit_code']==root['actual_native_child_exit_code']==guard['child_exit_code']==1
assert guard['elapsed_seconds']==root['native_elapsed_seconds']==667.1718313639994
assert guard['cleanup_verified'] is True and root['cleanup_verified'] is True and guard['cleanup_stop_returncode']==0
assert all(guard['memory_events'][k]==0 for k in ('max','oom','oom_kill','oom_group_kill'))
assert io['outer_log_handles_closed'] is True and io['supervisor_reaped'] is True
assert io['supervisor_pid']==launch['supervisor_pid']==owner['supervisor_pid']==297397 and launch['nonce']==owner['nonce']
assert launch['source_commit']==owner['source_commit']==storage['source']==SOURCE and owner['monitor_pid']==guard['monitor_pid']==297699
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
pids.update(int(k) for k in root['recorded_pids_absent']);assert len(pids)==4
assert all(not Path('/proc',str(pid)).exists() for pid in pids)
trace=raw(A/'guard/child.log').decode();assert 'imported_authority_interval.py\", line 34, in freshness' in trace and reason in trace
assert 'history audit stale' in trace and 'history audit poisoned' in trace
caller=Path('tradingagents/research/onchain_replication/real_pilot_import_caller.py');dispatch=Path('tradingagents/research/onchain_replication/imported_authority_interval.py')
cs=raw(caller).decode();assert cs.index("activate(execution,p['imported_authority_lease_input'])")<cs.index("mark('original_import')")
assert "'stale interval cannot refresh'" in raw(dispatch).decode()
assert 'imported_mcm_identity.py\", line 37, in __init__' in trace and 'imported_authority_interval.py\", line 44, in validate' in trace
import re
match=re.search(r'import lease full boundary timing: full_callback_seconds=([0-9.]+); pre_callback_age_seconds=([0-9.]+); total_age_seconds=([0-9.]+)',trace);assert match
callback,age,total=map(float,match.groups());assert callback==root['full_callback_seconds']==5.279688018999877 and age==root['pre_callback_age_seconds']==24.771937047000392 and total==root['total_age_seconds']==30.05162506600027
assert abs(age+callback-total)<1e-12 and callback<30<total and root['max_stale_seconds']==30
policy_path=Path(claim['inputs']['imported_authority_lease']['path']);assert sha(policy_path)==claim['inputs']['imported_authority_lease']['sha256']
assert read(policy_path)['max_stale_ms']==30000
remote=read(D/'REMOTE_CONFIRMATION01.json');assert remote['actual_remote_head']==remote['source']==SOURCE and remote['actual_ls_remote']['exit_code']==remote['push']['exit_code']==0
selection={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'files':rows,'directories':directories,'regular_count':len(rows),'directory_count':len(directories),'original_regular_bytes':sum(r['bytes'] for r in rows),'absent_source_namespace':str(P/'sources'/N),'dynamic_entry_records':[str(D/n) for n in dynamic],'scope':'Exact actual12 failed-pilot increment: all five owned roots and six D12 entry/closure records; typed directory names/modes included.','exclusions':['Scientific arrays/raw ledgers/runtime/private connection bodies','Earlier committed source/gate/preparation/input records','Earlier closed archive namespaces and workflow journals','Shared parent directories outside five owned roots'],'qualification':'Original bodies retained; selection permits exact archive construction, not deletion, transport or scientific relaunch. Actual external recovery still required.'}
bp=write('INCREMENT_SELECTION01.json',selection)
outcome={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'claim_sha256':sha(C/'claim.json'),'increment_selection':ref(bp),'evidence':{str(p):sha(p) for p in sorted(files)},'reviewed_source':[ref(caller),ref(dispatch)],'root_actual_exit':{'exit_code':1,'session':90344,'terminal_chunk':'acd15a'},'native':{'elapsed_seconds':guard['elapsed_seconds'],'child_exit_code':1,'cleanup_verified':True,'cleanup_stop_returncode':0,'memory_events':guard['memory_events'],'last_unit_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes']},'failure':{'reason':reason,'source_location':'tradingagents/research/onchain_replication/imported_authority_interval.py:44','caller_location':'tradingagents/research/onchain_replication/real_pilot_import_caller.py:457','impact':'Target constructor ENTRY checkpoint37 fails freshness(full_done) before MCM; genuine12 attempt83 is spent. Actual failure diagnostic gives prior age24.771937047s plus callback5.279688019s equals30.051625066s. Callback alone is below30s; the original Target entry cardinality is unrecorded.','action':'Preserve12 and original30s policy. User authorized a separately registered60s successor; do not reinterpret or reopen this spent failure.'},'denominator':{'registered_cells':1,'declared_outputs':8,'retained_outputs':8,'unavailable_outputs':[],'worker_failed_cell_ledger':ledger,'supervisor_postmortem_cells':read(A/'postmortem-cells.json'),'graphs':7,'MCM_completed':0,'MCM_failed':0,'MCM_unavailable_not_attempted':7,'verified_completed_motif_cells':0,'training':None,'financial_fits':0},'binding_distinction':{'claim_bindings':None,'claim_bindings_sha256':None,'output_resource_journal':'Failure placeholder distinct from retained genuine workflow journal.','actual12_journal_matches':[str(J)],'unsealed_journals':[]},'current_cleanup':{'selected_pid_exists':{str(pid):False for pid in sorted(pids)},'recorded_cgroup_absent':True,'lifetime_process_history':None,'native_unit_properties':'Original final-storage/guard readbacks reused; no native/systemctl call.'},'archive_context':{'spent':xt['spent'],'control_history':xt['control_history'],'secondary_cleanup_diagnostics':['history audit stale','history audit poisoned'],'close_failed_retained':True},'timing':{'native_seconds':667.1718313639994,'scope_seconds':summary['throughput']['scope_elapsed_seconds'],'original_import_events':summary['events'],'max_stale_ms':30000,'policy':ref(policy_path),'exact_failure_call_seconds':callback,'callback_duration_breakdown':{'prior_age_seconds':age,'full_callback_seconds':callback,'total_age_seconds':total,'prior_age_operation_attribution':None},'failure_boundary':'Target.__init__:37 ENTRY; full_check returned then freshness(full_done) refused. Diagnostic decomposes30.051625066s total into24.771937047s prior age and5.279688019s callback. No attribution of prior gap to a specific operation is established.'},'dictionary_import':{'current_matching_pairs':0,'historical_work_recomputed':False,'mcm_execution_admitted':False,'owner_stage_completed':False},'disposition':'Permanent FAILED/spent12; no refund, transfer, relaunch or scientific credit.','target_constructor_cardinality':None,'null_preservation':'Original claim/training/graph nulls and separate unavailable supervisor postmortem retained.','not_tested':['Numerical arrays/raw/price/labels/runtime/private connection bodies; population output hash only.','No experiment, transport, network, native or claim invocation.','Return/cashflow, leakage, fees/funding, predictive performance and full-pilot capacity.','External recovery and POSIX reconstruction not yet accepted.']}
op=write('OUTCOME_REVIEW01.json',outcome)
mp=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','experiment':N,'files':[ref(H/'review01.py'),ref(bp),ref(op)]})
print(json.dumps({'outcome':ref(op),'selection':ref(bp),'manifest':ref(mp),'regulars':len(rows),'directories':len(directories),'bytes':selection['original_regular_bytes'],'selected_absent_pids':len(pids),'decision':'accepted'},sort_keys=True))
