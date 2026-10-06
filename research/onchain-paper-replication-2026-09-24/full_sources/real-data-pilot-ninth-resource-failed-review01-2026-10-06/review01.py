"""Bounded D9 failure review; adapted from accepted D2 checks, no empirical imports."""
from pathlib import Path
import hashlib,json,stat
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
H=F/'real-data-pilot-ninth-resource-failed-review01-2026-10-06';D=F/'real-data-pilot-final09-2026-10-06'
N='eth-paper-real-data-end-to-end-resource-20261006-09';SOURCE='c8854e5315bb2a8b8d1cfde8121ead4e49e78808'
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
IDENTITY='885258df6934f62af3d655c37d8a00cb8092973819232dc17e4b03735c5ace6f'
J=Path('research_artifacts/onchain_representations')/IDENTITY/N
X=Path('research_artifacts/archive-dispatch-ethpilot-20261006-09')
files=[];directories=[]
for base in (C,A,L,J,X):
 for p in sorted([base,*base.rglob('*')]):
  s=p.lstat();assert (R/p).resolve(strict=True)==R/p and not stat.S_ISLNK(s.st_mode)
  if stat.S_ISDIR(s.st_mode):directories.append({'path':str(p),'kind':'directory','mode':stat.S_IMODE(s.st_mode)})
  else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;files.append(p)
dynamic=('launch-attempt01.json','ROOT_ACTIVE01.json','ROOT_PROGRESS01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ROOT_TERMINAL01.json','REMOTE_CONFIRMATION01.json')
files.extend(D/n for n in dynamic)
assert len(files)==len(set(files))==44 and len(directories)==13
rows=[]
for p in sorted(files):
 b=raw(p);s=p.lstat();rows.append({'path':str(p),'kind':'regular','bytes':len(b),'sha256':sha(p),'mode':stat.S_IMODE(s.st_mode),'nlink':s.st_nlink,'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]})
claim=read(C/'claim.json');failed=read(C/'failed.json');summary=read(C/'outputs/pilot-summary.json');root=read(D/'ROOT_TERMINAL01.json')
assert claim['experiment_id']==failed['experiment_id']==root['identity']==N
assert claim['source']==root['source']==SOURCE and claim['effective_attempt_budget']==80
assert claim['bindings'] is None and claim['bindings_sha256'] is None
assert sha(C/'claim.json')==failed['claim_sha256']=='a06dd660e4c138fbfdafec0b85e73eb747854e4aac4ca83f5f7e313c46f8da8b'
reason='ValueError: import lease: stale interval cannot refresh'
assert failed['status']=='failed' and failed['reason']==root['reason']==reason
assert not (C/'complete.json').exists() and not (C/'artifacts').exists() and not (P/'sources'/N).exists()
assert set(claim['experiment']['outputs'])==set(failed['output_sha256']) and len(failed['output_sha256'])==8
for n,pin in failed['output_sha256'].items():assert sha(C/'outputs'/n)==pin
ledger=read(C/'outputs/cell-ledger.json');assert ledger==[summary['cell']] and ledger[0]['status']=='failed' and ledger[0]['reason']==reason
t=summary['throughput'];assert t['graph_denominator']==len(t['graphs'])==t['unavailable_graphs']==7
assert all(t[k]==0 for k in ('complete_graphs','failed_graphs','verified_completed_motif_cells','verified_completed_nodes','attempted_mcm_seconds','paper_financial_fits'))
assert all(g['status']=='unavailable' and g['reason']=='not_attempted_after_failure' and g['completed_motif_cells'] is None and g['completed_nodes'] is None and g['elapsed_seconds'] is None for g in t['graphs'])
assert sum(g['expected_motif_cells'] for g in t['graphs'])==415968128
assert summary['training'] is None and summary['events']==[{'elapsed_seconds':199.94338109499995,'phase':'original_import'}] and summary['retained_target_count']==0 and summary['financial_fit_complete'] is False
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
assert sha(A/'guard/final.json')==root['guard']['sha256']=='9ed9d5d6224131534b3a429b18d0b00d1cdd5912fa52f62fef93284f0a1fa62e'
assert root['root_exec_session']==90306 and root['root_output_chunk']=='4c0a60'
assert root['actual_root_exit_code']==root['actual_parent_exit_code']==io['actual_parent_exit_code']==root['original_guard_child_exit_code']==guard['child_exit_code']==1
assert guard['elapsed_seconds']==root['native_elapsed_seconds']==644.7821131579999
assert guard['cleanup_verified'] is True and root['cleanup_verified'] is True and guard['cleanup_stop_returncode']==0
assert all(guard['memory_events'][k]==0 for k in ('max','oom','oom_kill','oom_group_kill'))
assert io['outer_log_handles_closed'] is True and io['supervisor_reaped'] is True
assert io['supervisor_pid']==launch['supervisor_pid']==owner['supervisor_pid']==29089 and launch['nonce']==owner['nonce']
assert launch['source_commit']==owner['source_commit']==storage['source']==SOURCE and owner['monitor_pid']==guard['monitor_pid']==29375
for k,n in (('guard','guard/final.json'),('launch','launch.json'),('owner','owner.json')):assert storage['original_metadata_sha256'][k]==sha(A/n)
assert storage['actual_current_cgroup_absent'] and storage['original_monitor_process_absent'] and storage['actual_current_unit_properties']['MainPID']=='0' and storage['actual_current_unit_properties']['ControlGroup']==''
assert not Path(guard['cgroup']).exists()
assert obs['terminal_sha256']==sha(C/'failed.json')==root['failed']['sha256'] and obs['owner_sha256']==sha(A/'owner.json')
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
pids.update(int(k) for k in root['recorded_pids_absent']);assert len(pids)==7
assert all(not Path('/proc',str(pid)).exists() for pid in pids)
trace=raw(A/'guard/child.log').decode();assert 'imported_authority_interval.py\", line 34, in freshness' in trace and reason in trace
assert 'history audit stale' in trace and 'history audit poisoned' in trace
caller=Path('tradingagents/research/onchain_replication/real_pilot_import_caller.py');dispatch=Path('tradingagents/research/onchain_replication/imported_authority_interval.py')
cs=raw(caller).decode();assert cs.index("activate(execution,p['imported_authority_lease_input'])")<cs.index("mark('original_import')")
assert "'stale interval cannot refresh'" in raw(dispatch).decode()
assert 'imported_mcm_identity.py\", line 53, in __init__' in trace and 'imported_authority_interval.py\", line 43, in validate' in trace
policy_path=Path(claim['inputs']['imported_authority_lease']['path']);assert sha(policy_path)==claim['inputs']['imported_authority_lease']['sha256']
assert read(policy_path)['max_stale_ms']==30000
remote=read(D/'REMOTE_CONFIRMATION01.json');assert remote['actual_remote_head']==remote.get('source',remote.get('actual_local_head'))==SOURCE and remote['actual_exit_code']==0
selection={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'files':rows,'directories':directories,'regular_count':len(rows),'directory_count':len(directories),'original_regular_bytes':sum(r['bytes'] for r in rows),'absent_source_namespace':str(P/'sources'/N),'dynamic_entry_records':[str(D/n) for n in dynamic],'scope':'Exact actual09 failed-pilot increment: all five owned roots and seven D9 entry/closure records; typed directory names/modes included.','exclusions':['Scientific arrays/raw ledgers/runtime/private connection bodies','Earlier committed source/gate/preparation/input records','Earlier closed archive namespaces and workflow journals','Shared parent directories outside five owned roots'],'qualification':'Original bodies retained; selection permits exact archive construction, not deletion, transport or scientific relaunch. Actual external recovery still required.'}
bp=write('INCREMENT_SELECTION01.json',selection)
outcome={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'claim_sha256':sha(C/'claim.json'),'increment_selection':ref(bp),'evidence':{str(p):sha(p) for p in sorted(files)},'reviewed_source':[ref(caller),ref(dispatch)],'root_actual_exit':{'exit_code':1,'session':90306,'terminal_chunk':'4c0a60'},'native':{'elapsed_seconds':guard['elapsed_seconds'],'child_exit_code':1,'cleanup_verified':True,'cleanup_stop_returncode':0,'memory_events':guard['memory_events'],'last_unit_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes']},'failure':{'reason':reason,'source_location':'tradingagents/research/onchain_replication/imported_authority_interval.py:43','caller_location':'tradingagents/research/onchain_replication/real_pilot_import_caller.py:448','impact':'Target constructor passes entry and manifest read/parse, then full-authority checkpoint fails freshness(full_done) before MCM; genuine09 attempt80 is spent. Original import event confirms activation returned; exact full-callback duration and prior interval age are unknown.','action':'Measure the full-authority validation path and prior age before choosing a changed seam; any successor must be separately reviewed and registered. Preserve09 and all earlier namespaces.'},'denominator':{'registered_cells':1,'declared_outputs':8,'retained_outputs':8,'unavailable_outputs':[],'worker_failed_cell_ledger':ledger,'supervisor_postmortem_cells':read(A/'postmortem-cells.json'),'graphs':7,'MCM_completed':0,'MCM_failed':0,'MCM_unavailable_not_attempted':7,'verified_completed_motif_cells':0,'training':None,'financial_fits':0},'binding_distinction':{'claim_bindings':None,'claim_bindings_sha256':None,'output_resource_journal':'Failure placeholder distinct from retained genuine workflow journal.','actual09_journal_matches':[str(J)],'unsealed_journals':[]},'current_cleanup':{'selected_pid_exists':{str(pid):False for pid in sorted(pids)},'recorded_cgroup_absent':True,'lifetime_process_history':None,'native_unit_properties':'Original final-storage/guard readbacks reused; no native/systemctl call.'},'archive_context':{'spent':xt['spent'],'control_history':xt['control_history'],'secondary_cleanup_diagnostics':['history audit stale','history audit poisoned'],'close_failed_retained':True},'timing':{'native_seconds':644.7821131579999,'scope_seconds':summary['throughput']['scope_elapsed_seconds'],'original_import_events':summary['events'],'max_stale_ms':30000,'policy':ref(policy_path),'exact_failure_call_seconds':None,'callback_duration_breakdown':None,'failure_boundary':'Target.__init__:53; full_check returned then freshness(full_done) refused. Existing age plus full callback can exceed threshold; callback alone >30s is not proved.'},'dictionary_import':{'current_matching_pairs':0,'historical_work_recomputed':False,'mcm_execution_admitted':False,'owner_stage_completed':False},'disposition':'Permanent FAILED/spent09; no refund, transfer, relaunch or scientific credit.','null_preservation':'Original claim/training/graph nulls and separate unavailable supervisor postmortem retained.','not_tested':['Numerical arrays/raw/price/labels/runtime/private connection bodies; population output hash only.','No experiment, transport, network, native or claim invocation.','Return/cashflow, leakage, fees/funding, predictive performance and full-pilot capacity.','External recovery and POSIX reconstruction not yet accepted.']}
op=write('OUTCOME_REVIEW01.json',outcome)
mp=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','experiment':N,'files':[ref(H/'review01.py'),ref(bp),ref(op)]})
print(json.dumps({'outcome':ref(op),'selection':ref(bp),'manifest':ref(mp),'regulars':len(rows),'directories':len(directories),'bytes':selection['original_regular_bytes'],'selected_absent_pids':len(pids),'decision':'accepted'},sort_keys=True))
