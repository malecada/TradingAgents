"""Independent bounded pilot15 outcome and public increment review; no numerical imports.

Selection/stat checks follow the accepted failed14 incremental review. Every outcome
assertion below is joined to actual15 records, not copied from the prior verdict.
"""
from pathlib import Path
import hashlib,json,stat,struct,subprocess
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
H=F/'real-data-pilot-fifteenth-resource-failed-review01-2026-10-07';D=F/'real-data-pilot-final15-2026-10-07'
N='eth-paper-real-data-end-to-end-resource-20261007-15';SOURCE='1f0894a2c15a1d544ba3ac6c35893dfe53068b6a'
C=Path('research_runs')/N;P=Path('research_artifacts/onchain-paper-replication-2026-09-24');A=P/'runs'/N;L=P/'pilot-parent'/N
IDENTITY='25448ca4ffc3a83aa4286ddd95a438b4af170c7b194c357e80ff98f09639a16d'
J=Path('research_artifacts/onchain_representations')/IDENTITY/N;X=Path('research_artifacts/archive-dispatch-ethpilot-20261007-15')
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
for base in (C,A,L,J,X):
 for p in sorted([base,*base.rglob('*')]):
  s=p.lstat();assert (R/p).resolve(strict=True)==R/p and not stat.S_ISLNK(s.st_mode)
  if stat.S_ISDIR(s.st_mode):directories.append({'path':str(p),'kind':'directory','mode':stat.S_IMODE(s.st_mode)})
  else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;files.append(p)
dynamic=('launch-attempt01.json','ROOT_ACTIVE01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ROOT_TERMINAL01.json','REMOTE_CONFIRMATION01.json','ELIGIBILITY_READY01.json')
files.extend(D/n for n in dynamic)
assert len(files)==len(set(files))
rows=[]
for p in sorted(files):
 b=raw(p);s=p.lstat();rows.append({'path':str(p),'kind':'regular','bytes':len(b),'sha256':sha(p),'mode':stat.S_IMODE(s.st_mode),'nlink':s.st_nlink,'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]})
claim=read(C/'claim.json');failed=read(C/'failed.json');summary=read(C/'outputs/pilot-summary.json');root=read(D/'ROOT_TERMINAL01.json')
assert claim['experiment_id']==failed['experiment_id']==root['experiment']==N
assert claim['source']==root['source_commit']==SOURCE and claim['effective_attempt_budget']==86
assert claim['bindings'] is None and claim['bindings_sha256'] is None
assert sha(C/'claim.json')==failed['claim_sha256']=='ae9bdf0533defc72bef7ca2ab37395573b695b2782e5cbc212a2709adcc24aca'
reason='ValueError: neighborhood index buffer allowance exceeded'
assert failed['status']=='failed' and failed['reason']==root['failure_reason']==reason
assert not (C/'complete.json').exists() and not (C/'artifacts').exists() and not (P/'sources'/N).exists()
assert set(claim['experiment']['outputs'])==set(failed['output_sha256']) and len(failed['output_sha256'])==8
for n,pin in failed['output_sha256'].items():assert sha(C/'outputs'/n)==pin
ledger=read(C/'outputs/cell-ledger.json');assert ledger==[summary['cell']] and ledger[0]['status']=='failed' and ledger[0]['reason']==reason
t=summary['throughput'];assert t['graph_denominator']==len(t['graphs'])==7 and t['unavailable_graphs']==6 and t['failed_graphs']==1 and t['attempted_mcm_seconds']==505.13878678599986
assert all(t[k]==0 for k in ('complete_graphs','verified_completed_motif_cells','verified_completed_nodes','paper_financial_fits'))
assert all(g['status']=='unavailable' and g['reason']=='not_attempted_after_failure' and g['completed_motif_cells'] is None and g['completed_nodes'] is None and g['elapsed_seconds'] is None for g in t['graphs'][1:])
assert t['graphs'][0]['status']=='failed' and t['graphs'][0]['reason']==reason and t['graphs'][0]['elapsed_seconds']==t['attempted_mcm_seconds'] and t['graphs'][0]['completed_motif_cells'] is None
assert sum(g['expected_motif_cells'] for g in t['graphs'])==415968128
assert all(g['expected_motif_cells']==32*g['expected_nodes'] for g in t['graphs'])
assert summary['training'] is None and summary['events']==[{'elapsed_seconds':216.81333152000002,'phase':'original_import'}] and summary['retained_target_count']==0 and summary['financial_fit_complete'] is False
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
assert xt['spent']=={'commands':0,'logical_bytes':73075435776,'rounded_bytes':0} and xt['wire_bytes_measured'] is False
controls=xt['control_history']['controls'];assert (controls['acknowledged_records'],controls['acknowledged_encoded_bytes'],controls['shards'],controls['journal_failed'])==(1,728,1,False)
frame=raw(X/'controls/control-00000000.bin');nl,rl=struct.unpack('<II',frame[:8]);assert len(frame)==8+nl+rl+32==728
assert hashlib.sha256(bytes(32)+frame[:-32]).digest()==frame[-32:] and frame[-32:].hex()==controls['head_sha256']
control_name=frame[8:8+nl].decode();control=json.loads(frame[8+nl:-32])
assert all(xt['control_history']['diagnostic-controls'][k]==0 for k in ('acknowledged_records','acknowledged_encoded_bytes','shards'))
assert all(not any((X/n).iterdir()) for n in ('diagnostic-controls','diagnostics'))
assert read(X/'close-failed.json')['intent_sha256']==sha(X/'intent.json')
guard=read(A/'guard/final.json');owner=read(A/'owner.json');launch=read(A/'launch.json');io=read(D/'ROOT_IO_CLOSED01.json');storage=read(D/'FINAL_STORAGE01.json');obs=read(A/'observer.json')
assert sha(A/'guard/final.json')=='7a3d229410dadc12437b7e498ee1898d83d28721da1945471838fa4cade835de'
for p,pin in root['original_receipts_sha256'].items():assert sha(p)==pin
assert root['actual_root_session']==39936 and root['root_terminal_tool_chunk']=='cc0a30'
assert root['actual_root_exit_code']==root['actual_parent_exit_code']==io['actual_parent_exit_code']==root['native_child_exit_code']==guard['child_exit_code']==1
assert guard['elapsed_seconds']==root['native_elapsed_seconds']==2592.604633627
assert guard['cleanup_verified'] is True and guard['cleanup_stop_returncode']==0 and guard['elapsed_time_kill'] is False
assert all(guard['memory_events'][k]==0 for k in ('max','oom','oom_kill','oom_group_kill'))
assert io['outer_log_handles_closed'] is True and io['supervisor_reaped'] is True
assert io['supervisor_pid']==launch['supervisor_pid']==owner['supervisor_pid']==18169 and launch['nonce']==owner['nonce']
assert launch['source_commit']==owner['source_commit']==storage['source']==SOURCE and owner['monitor_pid']==guard['monitor_pid']==18501
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
pids.update(int(k) for k in root['current_recorded_pids_absent']);assert len(pids)==4
assert all(not Path('/proc',str(pid)).exists() for pid in pids)
unit=subprocess.run(['systemctl','--user','show',guard['unit'],'--property=MainPID,ControlGroup,ActiveState,SubState'],capture_output=True,text=True,check=True)
unit_props=dict(line.split('=',1) for line in unit.stdout.splitlines() if '=' in line)
assert unit_props=={'MainPID':'0','ControlGroup':'','ActiveState':'failed','SubState':'failed'}
trace=raw(A/'guard/child.log').decode();assert reason in trace and 'history audit stale' not in trace and 'history audit poisoned' not in trace
assert 'array_neighborhoods.py", line 30, in __init__' in trace and 'archive_owner_writer.py", line 82, in _run_locked' in trace
progress=[json.loads(line) for line in trace.splitlines() if line.startswith('{')]
assert len(progress)==summary['partial_mcm_progress']['records']==3 and progress[-1]==summary['partial_mcm_progress']['last_observation']
assert [p['sequence'] for p in progress]==[0,1,2]
assert all(p['claim_sha256']==sha(C/'claim.json') and p['source']==SOURCE and p['graph_hash']==t['graphs'][0]['graph_hash'] for p in progress)
assert all(p[k]==0 for p in progress for k in ('started_matching_pairs','acknowledged_computed_matching_pairs','durable_score_batches','durable_score_batch_cells','paper_financial_fits','representation_credit'))
assert all(p['full_mcm_completion_verified_here'] is False and p['joint_update_verified_here'] is False for p in progress)
source_paths=[Path('tradingagents/research/onchain_replication')/n for n in ('array_neighborhoods.py','archive_dispatch.py','real_pilot_import_caller.py')]+[F/'original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py']
source_records=[];source_text={}
for p in source_paths:
 b=subprocess.run(['git','show',SOURCE+':'+str(p)],check=True,capture_output=True).stdout
 source_records.append({'path':str(p),'source_commit':SOURCE,'sha256':hashlib.sha256(b).hexdigest()});source_text[p.name]=b.decode()
s=source_text['array_neighborhoods.py'];assert s.index('if self.buffer_allowance>max_buffer_bytes:')<s.index('self.orders=[]; self.offsets=[]') and "raise ValueError('neighborhood index buffer allowance exceeded')" in s
k=source_text['imported_kernel.py'];assert k.index('with ArrayNeighborhoodIndex(')<k.index('result=np.empty(')<k.index('value=workload.score(')
ds=source_text['archive_dispatch.py'];assert "logical=claim.record['reserved_decoded_transfer_bytes']" in ds and "c._spent['logical_bytes']+=logical" in ds
stage=J/'compact'/('mcm-'+t['graphs'][0]['graph_hash']);op=J/'archive-operations'/('writer-mcm-'+t['graphs'][0]['graph_hash']+'-0000')
assert (stage/'intent.json').is_file() and (stage/'matching/start.json').is_file() and not (stage/'complete.json').exists()
assert read(op/'failed.json')=={'error_type':'ValueError','reservations_retained':True,'schema_version':1,'status':'failed'} and not (op/'complete.json').exists()
assert not any((stage/'matching/copies').iterdir()) and not any((stage/'matching/reads').iterdir())
assert not any((stage/'checkpoints/events').iterdir()) and not any((stage/'checkpoints/stores').iterdir()) and not any((stage/'stream/tails').iterdir())
assert [p.name for p in (stage/'stream/batches').iterdir()]==['start.json']
remote=read(D/'REMOTE_CONFIRMATION01.json');assert remote['actual_remote_head']==remote['source']==SOURCE and remote['remote_readback']['exit_code']==remote['push']['exit_code']==0
allocation_path=F/'real-data-pilot-retry15-registration01-2026-10-07/CUMULATIVE_ALLOCATION_PROPOSED86_01.json';prior_review_path=F/'real-data-pilot-retry15-review01-2026-10-07/EXTENSION_REVIEW01.json'
allocation=read(allocation_path);prior_review=read(prior_review_path)
assert prior_review['decision']=='accepted' and allocation['consumed_before']==55 and allocation['proposed_cumulative_ceiling']==86 and allocation['identities']==[N]
assert len(allocation['closed_claims'])==38 and allocation['base_family']['prior_attempts']==17
assert sum(c['terminal_status']=='failed' for c in allocation['closed_claims'])==18 and sum(c['terminal_status']=='complete' for c in allocation['closed_claims'])==20
assert sum(allocation['unchanged_pending_allocation'].values())==28 and len(allocation['preserved_reserved_preclaim_allowances'])==2
assert N not in [c['experiment'] for c in allocation['closed_claims']] and allocation['refunds']==allocation['category_transfers']==0
selection={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'files':rows,'directories':directories,'regular_count':len(rows),'directory_count':len(directories),'original_regular_bytes':sum(r['bytes'] for r in rows),'absent_source_namespace':str(P/'sources'/N),'dynamic_entry_records':[str(D/n) for n in dynamic],'scope':'Exact actual15 failed-pilot increment: all five owned roots and seven dynamic D15 entry/closure records. Typed directory names/modes include partial checkpoint/matching/stream and original control shard.','exclusions':['Referenced immutable source/gate/preparation/input records and historical stores','Scientific arrays/raw ledgers/runtime/private transport binding bodies','Shared parent directories outside five owned roots'],'qualification':'Original bodies retained; exact archive construction only. No deletion, transport or scientific relaunch authority. Actual external recovery still required.'}
bp=write('INCREMENT_SELECTION01.json',selection)
outcome={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'claim_sha256':sha(C/'claim.json'),'increment_selection':ref(bp),'evidence':{str(p):sha(p) for p in sorted(files)},'reviewed_source':source_records,'root_actual_exit':{'exit_code':1,'session':39936,'terminal_chunk':'cc0a30'},'native':{'elapsed_seconds':guard['elapsed_seconds'],'child_exit_code':1,'cleanup_verified':True,'cleanup_stop_returncode':0,'memory_events':guard['memory_events'],'peak_sampled_memory_current_bytes':guard['peak_sampled_memory_current_bytes'],'last_unit_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes'],'peak_qualification':'Includes charged file cache. Optional last kernel readback need not equal final lifetime peak.','minimum_sampled_disk_free_bytes':guard['minimum_sampled_disk_free_bytes'],'elapsed_time_kill':False},'failure':{'reason':reason,'source_location':'tradingagents/research/onchain_replication/array_neighborhoods.py:28','raise_location':'tradingagents/research/onchain_replication/array_neighborhoods.py:30','caller_location':'research/onchain-paper-replication-2026-09-24/full_sources/original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py:48','impact':'Additive whole-graph index/scratch admission refused before index arrays, MCM result allocation and first matcher call. Genuine15 attempt86 is spent.','action':'Preserve failed15. Diagnose registered allowance versus exact seven-graph dimensions from existing metadata and add early capacity checks before any separately registered successor. No truncation, subsampling, silent cap increase or spent identity restart.','required_bytes':None,'allowed_bytes':None,'byte_diagnostic_qualification':'Original exception does not record values; exact demand reconstruction delegated separately and not claimed by this outcome review.'},'denominator':{'registered_cells':1,'declared_outputs':8,'retained_outputs':8,'unavailable_outputs':[],'worker_failed_cell_ledger':ledger,'supervisor_postmortem_cells':read(A/'postmortem-cells.json'),'graphs':7,'MCM_completed':0,'MCM_failed':1,'MCM_unavailable_not_attempted':6,'expected_motif_cells':415968128,'verified_completed_motif_cells':0,'partial_progress_records':3,'training':None,'financial_fits':0},'partial_progress':{'records':progress,'scope':'Actual retained stdout records; not final lifetime counts or restart authority. Source ordering independently supports pre-matcher failure. No useful matching throughput inferred.'},'binding_distinction':{'claim_bindings':None,'claim_bindings_sha256':None,'output_resource_journal':'Failure placeholder distinct from retained genuine workflow journal.','actual15_journal_matches':[str(J)],'unsealed_journals':[]},'current_cleanup':{'selected_pid_exists':{str(pid):False for pid in sorted(pids)},'recorded_cgroup_absent':True,'native_unit_properties':unit_props,'read_only_systemctl_exit_code':unit.returncode,'lifetime_process_history':None},'archive_context':{'spent':xt['spent'],'wire_bytes_measured':False,'control_history':xt['control_history'],'independently_decoded_control':{'name':control_name,'record':control,'hash_chain_verified':True},'logical_bytes_qualification':'73,075,435,776 is the retained decoded-transfer reservation from archive_dispatch.binding, not bytes transferred or allocated. Zero command/rounded counters do not erase that reservation.','secondary_cleanup_diagnostics':[],'close_failed_retained':True,'writer_failed_reservations_retained':True},'accounting':{'basis':'Accepted prior55 plus independently joined genuine15 failed claim, without rereading historical bodies. Prior17 base-family claims and current38 remain correlated spent history.','prior_allocation':ref(allocation_path),'prior_accepted_review':ref(prior_review_path),'closed':56,'complete':33,'failed':23,'highest_actually_claimed':86,'unchanged_pending':28,'closed_preclaim_reserves':2,'equation':'86 = 56 closed + 28 unchanged pending + 2 closed preclaim reserves','refunds':0,'category_transfers':0,'new_allowance':False,'status_split_qualification':'33COMPLETE/22FAILED prior55 split is carried from accepted current checkpoint; inspected allocation explicitly lists current38 as20COMPLETE/18FAILED plus17base, whose13COMPLETE/4FAILED split was not reread in this bounded review.'},'timing':{'native_seconds':guard['elapsed_seconds'],'scope_seconds':t['scope_elapsed_seconds'],'original_import_events':summary['events'],'first_MCM_attempt_seconds':t['attempted_mcm_seconds'],'whole_future_boundary_or_capacity_proof':False},'dictionary_import':{'current_matching_pairs':0,'historical_work_recomputed':False,'mcm_execution_admitted':False,'owner_stage_completed':False},'disposition':'Permanent FAILED/spent15; no refund, transfer, relaunch or scientific credit.','null_preservation':'Original claim/training/graph nulls, retained_target_count0 and separate unavailable supervisor postmortem retained.','not_tested':['No financial/empirical experiment, claim, transport or numerical imports invoked.','Return/cashflow convention, leakage, fees/funding, predictive performance and full-pilot capacity.','Population output hashed only; numerical arrays, raw/price/labels/runtime/private connection bodies not interpreted.','Global historical accounting bodies reused through accepted prior allocation; no unchanged historical matrix repeated.','Exact required/allowed index bytes, full runtime attribution, continuous resource/process history.','External recovery and POSIX reconstruction not yet accepted.']}
op=write('OUTCOME_REVIEW01.json',outcome)
mp=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','experiment':N,'files':[ref(H/'review01.py'),ref(bp),ref(op)]})
print(json.dumps({'outcome':ref(op),'selection':ref(bp),'manifest':ref(mp),'regulars':len(rows),'directories':len(directories),'bytes':selection['original_regular_bytes'],'selected_absent_pids':len(pids),'decision':'accepted'},sort_keys=True))
