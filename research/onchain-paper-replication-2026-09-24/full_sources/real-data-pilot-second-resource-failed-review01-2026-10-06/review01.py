"""Bounded second failed-pilot outcome and exact incremental metadata selection."""
from pathlib import Path
import hashlib,json,stat
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
H=F/'real-data-pilot-second-resource-failed-review01-2026-10-06'
D=F/'real-data-pilot-final02-2026-10-06'
N='eth-paper-real-data-end-to-end-resource-20261006-02'
SOURCE='b0b3a922e11eb3ce400fb7b59f41b596e7dac469'
C=Path('research_runs')/N;P=Path('research_artifacts/onchain-paper-replication-2026-09-24')
A=P/'runs'/N;L=P/'pilot-parent'/N;X=Path('research_artifacts/archive-dispatch-ethpilot-20261006-02')
IDENTITY='c76446199cc2e9147323c71d90af0af2cb61f38a97f304bf26f152edfb7b7e9d'
J=Path('research_artifacts/onchain_representations')/IDENTITY/N
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
for root in (C,A,L,X,J):
 for p in sorted([root,*root.rglob('*')]):
  s=p.lstat();assert (R/p).resolve(strict=True)==R/p and not stat.S_ISLNK(s.st_mode)
  if stat.S_ISDIR(s.st_mode):directories.append({'path':str(p),'kind':'directory','mode':stat.S_IMODE(s.st_mode)})
  else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;files.append(p)
files.extend(D/n for n in ('launch-attempt01.json','ROOT_ACTIVE01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ROOT_TERMINAL01.json'))
assert len(files)==len(set(files))==38 and len(directories)==10
rows=[]
for p in sorted(files):
 b=raw(p);s=p.lstat();rows.append({'path':str(p),'kind':'regular','bytes':len(b),'sha256':sha(p),'mode':stat.S_IMODE(s.st_mode),'nlink':s.st_nlink,'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]})
claim=read(C/'claim.json');failed=read(C/'failed.json');summary=read(C/'outputs/pilot-summary.json');root=read(D/'ROOT_TERMINAL01.json')
assert claim['experiment_id']==failed['experiment_id']==root['experiment']==N
assert claim['source']==root['source']==SOURCE and claim['effective_attempt_budget']==73
assert claim['bindings'] is None and claim['bindings_sha256'] is None
assert sha(C/'claim.json')==failed['claim_sha256']=='d44bad59ecf2b4f1420ae5072e71afa816fef013de12619c8f98e93a804aaea7'
reason='ValueError: finite imported owner reservation required'
assert failed['status']=='failed' and failed['reason']==root['failure']==reason
assert not (C/'complete.json').exists() and not (C/'artifacts').exists() and not (P/'sources'/N).exists()
assert set(failed['output_sha256'])==set(claim['experiment']['outputs']) and len(failed['output_sha256'])==8
for n,pin in failed['output_sha256'].items():assert sha(C/'outputs'/n)==pin
ledger=read(C/'outputs/cell-ledger.json');assert ledger==[summary['cell']] and ledger[0]['status']=='failed' and ledger[0]['reason']==reason
t=summary['throughput'];assert t['graph_denominator']==len(t['graphs'])==t['unavailable_graphs']==7
assert all(t[k]==0 for k in ('complete_graphs','failed_graphs','verified_completed_motif_cells','verified_completed_nodes','attempted_mcm_seconds','paper_financial_fits'))
assert all(g['status']=='unavailable' and g['reason']=='not_attempted_after_failure' and g['completed_motif_cells'] is None and g['completed_nodes'] is None and g['elapsed_seconds'] is None for g in t['graphs'])
assert summary['training'] is None and summary['events']==[] and summary['retained_target_count']==0 and summary['financial_fit_complete'] is False
assert read(C/'outputs/resource-binding.json')==read(C/'outputs/resource-journal.json') and read(C/'outputs/resource-journal.json')['status']=='failed'
jc,jf,jo,js=(read(J/n) for n in ('claim.json','failed.json','owner.json','start.json'))
assert jc['owner']==jf['owner']==js['owner']==jo and jo['experiment']==N and jo['source_commit']==SOURCE and jo['workflow_identity']==IDENTITY
assert jc['resource_only'] is True and jf['status']=='failed' and jf['events']==[] and jf['reason']==reason
assert jf['workflow_identity'] is None and js['workflow_identity'] is None
assert set(p.name for p in J.iterdir())=={'claim.json','start.json','failed.json','owner.json'}
assert set(jf['required_graphs'])=={g['graph_hash'] for g in t['graphs']}
intent=read(X/'intent.json');xt=read(X/'terminal.json');receipt=read(C/'outputs/archive-receipt.json')
assert read(C/'outputs/archive-terminal.json')==xt and xt['status']=='failed' and intent['execution_admitted'] is False
assert intent['claim_sha256']==sha(C/'claim.json') and intent['source_commit']==SOURCE and intent['experiment']==N
assert receipt['context']==str(X) and receipt['intent_sha256']==xt['intent_sha256']==sha(X/'intent.json')
assert xt['spent']=={'commands':0,'logical_bytes':0,'rounded_bytes':0}
assert all(v['acknowledged_records']==v['acknowledged_encoded_bytes']==v['shards']==0 for v in xt['control_history'].values())
assert all(not any((X/n).iterdir()) for n in ('controls','diagnostic-controls','diagnostics'))
guard=read(A/'guard/final.json');owner=read(A/'owner.json');launch=read(A/'launch.json');io=read(D/'ROOT_IO_CLOSED01.json');storage=read(D/'FINAL_STORAGE01.json');obs=read(A/'observer.json')
assert sha(A/'guard/final.json')==root['original_guard_sha256']=='41b4d082343d2392124c4abe5e2da55dcf91f7c4a6c093daa20e436d5ba36b44'
assert root['root_session']==13845 and root['actual_root_terminal_chunk']=='a13f4d'
assert root['actual_root_exit_code']==io['actual_parent_exit_code']==root['native_child_exit_code']==guard['child_exit_code']==1
assert guard['elapsed_seconds']==root['native_elapsed_seconds']==438.3183279300001
assert guard['cleanup_verified'] is True and root['cleanup_verified'] is True and guard['cleanup_stop_returncode']==0
assert io['outer_log_handles_closed'] is True and io['supervisor_reaped'] is True
assert io['supervisor_pid']==launch['supervisor_pid']==owner['supervisor_pid'] and launch['nonce']==owner['nonce']
assert launch['source_commit']==owner['source_commit']==storage['source']==SOURCE
assert owner['monitor_pid']==guard['monitor_pid']
for k,n in (('guard','guard/final.json'),('launch','launch.json'),('owner','owner.json')):assert storage['original_metadata_sha256'][k]==sha(A/n)
assert storage['actual_current_cgroup_absent'] is True and storage['original_monitor_process_absent'] is True
assert storage['actual_current_unit_properties']['MainPID']=='0' and storage['actual_current_unit_properties']['ControlGroup']==''
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
assert all(not Path('/proc',str(pid)).exists() for pid in pids)
cp=Path(claim['inputs']['compact_policy']['path']);sp=Path(claim['inputs']['original_import_stage']['path'])
assert sha(cp)==claim['inputs']['compact_policy']['sha256'] and sha(sp)==claim['inputs']['original_import_stage']['sha256']
assert read(cp)['max_workflow_retained_logical_bytes'] is None and read(sp)['max_stage_bytes']==262144
trace=raw(A/'guard/child.log').decode();assert 'original_import_stage.py", line 127, in attach' in trace and reason in trace

selection={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'files':rows,'directories':directories,
 'regular_count':38,'directory_count':10,'original_regular_bytes':sum(r['bytes'] for r in rows),
 'absent_source_namespace':str(P/'sources'/N),'dynamic_entry_records':[str(D/n) for n in ('launch-attempt01.json','ROOT_ACTIVE01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ROOT_TERMINAL01.json')],
 'scope':'Exact actual02 failed-pilot metadata/log increment only. Include all38 regular bodies and10typed directory names/modes; separate four-body resource journal is mandatory.',
 'exclusions':['All scientific arrays/raw ledgers/runtime/private connection bodies','Earlier committed source, gate, preparation and input records','All original01 failed-pilot/recovery stores','Shared parent directories outside the five owned roots'],
 'qualification':'Original bodies retained; selection permits constructing an exact archive, not deletion, transport or scientific relaunch. Byte hashes and current stat identities verified. No archive or external recovery yet.'}
bp=write('INCREMENT_SELECTION01.json',selection)
evidence={str(p):sha(p) for p in files}
evidence[str(cp)]=sha(cp);evidence[str(sp)]=sha(sp)
outcome={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'claim_sha256':sha(C/'claim.json'),
 'scope':'Independent authentication of permanent02 failed outcome and exact retained increment; no scientific or capacity acceptance.',
 'evidence':dict(sorted(evidence.items())),'increment_selection':ref(bp),
 'root_actual_exit':{'exit_code':1,'session':13845,'terminal_chunk':'a13f4d'},
 'native':{'elapsed_seconds':guard['elapsed_seconds'],'child_exit_code':1,'cleanup_verified':True,'cleanup_stop_returncode':guard['cleanup_stop_returncode'],'memory_events':guard['memory_events'],'last_unit_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes']},
 'failure':{'reason':reason,'source_location':'tradingagents/research/onchain_replication/original_import_stage.py:127','compact_policy_reference':ref(cp),'actual_max_workflow_retained_logical_bytes':None,'stage_max_bytes':262144,
 'impact':'Null reservation fails the finite integer/minimum-owner-plus-stage check before Owner attachment, MCM and training;02 is spent.',
 'action':'Any separately authorized successor must freeze a finite complete reservation and precheck the exact admitted policy before native work. Preserve02; do not patch or relaunch it.'},
 'denominator':{'registered_cells':1,'worker_failed_cell_ledger':ledger,'supervisor_postmortem_cells':read(A/'postmortem-cells.json'),'graphs':7,'MCM_completed':0,'MCM_failed':0,'MCM_unavailable_not_attempted':7,'verified_completed_motif_cells':0,'training':None,'financial_fits':0},
 'binding_distinction':{'claim_bindings':None,'claim_bindings_sha256':None,'output_binding_journal':'Failed placeholders, not actual resource journal.','actual_resource_journal':str(J),'actual_resource_journal_bodies':4,'journal_top_level_workflow_identity':None,'journal_owner_workflow_identity':IDENTITY},
 'archive_context':{'created':True,'execution_admitted':False,'spent':xt['spent'],'control_history':xt['control_history']},
 'current_cleanup':{'selected_pid_exists':{str(pid):False for pid in sorted(pids)},'recorded_cgroup_absent':True,'lifetime_process_history':None,'native_unit_properties':'Original final-storage/guard closure readbacks reused; no native/systemctl call.'},
 'disposition':'Permanent FAILED/spent; no refund, transfer, relaunch, numerical completion or financial credit.',
 'null_preservation':'All original claim/journal/training/graph-count nulls are retained; no values are filled from other attempts.',
 'not_tested':['No numerical arrays/runtime/price/label/graph/raw bodies inspected or decoded; resource-population output hash only.','No experiment, network/native/transport/claim invocation.','No return/cashflow, timing leakage, fees/funding, predictive performance or full-pilot capacity claim tested.','No archive capture or external recovery yet; later actual archive and returned-byte checks remain required.']}
op=write('OUTCOME_REVIEW01.json',outcome)
mp=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','experiment':N,'files':[ref(H/'review01.py'),ref(bp),ref(op)]})
print(json.dumps({'outcome':ref(op),'selection':ref(bp),'manifest':ref(mp),'regulars':38,'directories':10,'bytes':selection['original_regular_bytes'],'selected_absent_pids':len(pids),'decision':'accepted'},sort_keys=True))
