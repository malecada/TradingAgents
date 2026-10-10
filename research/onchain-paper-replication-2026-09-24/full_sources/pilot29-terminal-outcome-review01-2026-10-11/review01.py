import resource
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
from pathlib import Path
import json,hashlib,os,struct,datetime
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];E=P/'evidence';E.mkdir()
ID='eth-paper-real-data-end-to-end-resource-20261009-29';ENTRY=F/'real-data-pilot-full29-entry01-2026-10-09';RUN=R/'research_runs'/ID;N=R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID;REP=R/'research_artifacts/onchain_representations/5efca533e6c821207f9cdb0b69d090f6b6ae02ef4e32e89f4d7793c6cd9787b5'/ID;S=REP/'compact/mcm-0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba';nbytes=0;inventory={};checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def ck(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p,save=True):
 global nbytes
 p=Path(p);p=p if p.is_absolute() else R/p
 with p.open('rb') as h:
  st=os.fstat(h.fileno());b=h.read(4*1024**2+1);en=os.fstat(h.fileno())
 ck(len(b)<=4*1024**2 and (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(en.st_dev,en.st_ino,en.st_size,en.st_mtime_ns) and len(b)==st.st_size,'stable bounded '+p.name)
 nbytes+=len(b);ck(nbytes<=16*1024**2,'cumulative input bound')
 name=f'{len(inventory):03d}-'+p.name;key=str(p.relative_to(R));inventory[key]={'bytes':len(b),'sha256':sha(b)}
 if save:(E/name).write_bytes(b);inventory[key]['snapshot']='evidence/'+name
 return b
def js(p):return json.loads(read(p))
claimb=read(RUN/'claim.json');claim=json.loads(claimb);failedb=read(RUN/'failed.json');failed=json.loads(failedb)
ck(sha(claimb)=='5b81c3cb892f75a0b1505bb08049c5cc985b4dd43f01e38899c8f7abf54c2504' and sha(failedb)=='100e51b2408119975cac58abec88b09b17203736f3a8254011507da147f977e0' and failed['claim_sha256']==sha(claimb),'actual original claim terminal anchors')
ck(failed['status']=='failed' and not (RUN/'complete.json').exists(),'permanent failed original claim')
gateb=read(ENTRY/'gate04.json');gate=json.loads(gateb);ck(sha(gateb)==claim['registration_sha256']=='f6be8198d971451eea91647bf853de036b82405ffcb70e18db61ef204e76c898','original gate/claim join');exp=gate['experiments'][ID];ck(exp==claim['experiment'] and claim['effective_attempt_budget']==100,'same frozen experiment and effective budget')
for name,digest in failed['output_sha256'].items():ck(sha(read(RUN/'outputs'/name,False))==digest,'failed retained output '+name)
owner=js(N/'owner.json');launch=js(N/'launch.json');finalb=read(N/'guard/final.json');final=json.loads(finalb);liveb=read(N/'guard/live.json');death=js(N/'guard/observer-death.json');child=js(N/'guard/child_exit.json');observer=js(N/'observer.json');cells=js(N/'postmortem-cells.json');unsealed=js(N/'unsealed-journals.json');freeze=js(ENTRY/'SOURCE_FREEZE01.json');root=js(ENTRY/'ACTUAL_ROOT_EXIT01.json');processhistory=js(ENTRY/'LIVE_PROCESS_PHASE_OBSERVATION03.json')
for name,row in freeze['original_receipts'].items():ck(sha(read(row['path']))==row['sha256'],'original unchanged receipt '+name)
ck(owner==final['owner_identity'] and owner==freeze['original_live_sample']['owner_identity'] and owner['source_commit']==claim['source'],'same actual native Owner')
ck(liveb==finalb and final['phase']=='failed' and final['limit_reason']=='RuntimeError: registered wall-clock limit exceeded' and final['elapsed_seconds']>=final['wall_seconds']==28800,'terminal exact wall limit')
ck(final['cleanup_verified'] is True and final['cleanup_stop_returncode']==0 and final['cleanup_unit_properties']['ControlGroup']=='' and final['cleanup_unit_properties']['Result']=='timeout','recorded native cleanup and timeout')
ck(final['child_exit_code'] is None and child['exit_code']==125 and child['reason']=='signal' and child['workload_pid']==10200,'separate unknown monitor child exit versus signalled wrapper125')
ck(root['session_id']==96601 and root['actual_root_exit']==1 and root['terminal_chunk']=='86d0cd' and root['polls'][-1]['exit_code']==1,'actual original Root handle exit')
for name,digest in observer['evidence_sha256'].items():ck(sha(read(N/name))==digest,'actual observer evidence '+name)
ck(observer['owner_sha256']==sha(read(N/'owner.json')) and observer['terminal_sha256']==sha(failedb) and observer['cgroup_empty'] is True and observer['financial_completion'] is False,'observer owner terminal cleanup joins')
ck([x['id'] for x in cells]==exp['cells'] and len(cells)==1 and cells[0]['status']=='unavailable','all registered cells retained unavailable')
ck(unsealed==[] and observer['unsealed_journals']==0,'no representations requiring separate reconciliation')
parent=R/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/ID
ck(json.loads(read(parent/'stdout.log'))==observer and read(parent/'stderr.log')==b'','actual Parent output matches observer')
repfailed=js(REP/'failed.json');ck(repfailed['status']=='failed' and repfailed['events']==[] and len(repfailed['required_graphs'])==7,'actual failed representation no completed graph events')
mcmroot=R/'research_artifacts/onchain_compact_mcm'/REP.parent.name/ID/S.name;mcmstart=js(mcmroot/'start.json');mcmfailed=js(mcmroot/'failed.json');ck(mcmfailed['status']=='failed' and mcmfailed['error_type']=='SystemExit','actual failed first MCM')
pilotref=exp['inputs']['pilot'];pilotb=read(pilotref['path']);ck(sha(pilotb)==pilotref['sha256'],'selected pilot pin');pilot=json.loads(pilotb);ck(set(pilot['graph_inputs'])==set(repfailed['required_graphs']),'original seven graph denominator')
footb=read(F/'pilot29-neural-tensor-footprint-review01-2026-10-10/REVIEW01.json');ck(sha(footb)=='44ba14fcaccbf3f94b3fc7d65978574e027df06d194dba6bc982de1af5cd3d42','accepted header arithmetic anchor');foot=json.loads(footb);totalcells=foot['totals']['N']*32;ck(totalcells==415968128,'whole seven graph original cell denominator')
refs=[('first','b5404a0518d32561d638e5407d0e63707fbf0e2b26089474c0cd9acac1624f15','6fa06bb16d0805ca4b2acb7465809e99dc5443dfd4d8351f5b0cfb23710d53f9'),('second','f13a006dd79d21a0eb1815b983f9c870c9ecc6dd5709d60ed86f896377ab7e76','952508542414ef149fa79453ecc202843cab31aa978b8ab24d4e5971d7f3fda4'),('third','5d6f432a3eed9cbb13d06f72ceb6951531ae5833c7ba365335572c8e03927328','4eccb990820274c3b1edc10dc3013090b792a7f988b132ebfc18872fed1c01b2')]
for group,digest,manifesthash in refs:
 d=F/f'pilot29-{group}-group-recovery-review01-2026-10-10';ck(sha(read(d/'REVIEW01.json'))==digest and sha(read(d/'MANIFEST01.json'))==manifesthash,'reuse exact accepted '+group+' group recovery')
names=sorted((S/'stream/numeric-batches').iterdir());ck([p.name for p in names]==[f'{i:012d}.json' for i in range(52)],'exact final52 numerical summaries')
summaries=[js(p) for p in names];computed=reused=0;seconds=0.
for i,s in enumerate(summaries):
 ck((s['batch'],s['start'],s['stop'])==(i,i*4096,(i+1)*4096) and s['computed']+s['reused']==4096,'actual summary coverage '+str(i));computed+=s['computed'];reused+=s['reused'];seconds+=s['elapsed_seconds']
ck((computed,reused)==(208448,4544),'terminal computed/reused summary aggregate');journalcells=52*4096
ck([p.name for p in sorted((S/'matching').iterdir())]==sorted(f'{i:08d}{suffix}' for i in range(48,52) for suffix in ('.pending.json','.records.bin','.complete.json')),'only four completed local batches no pending52')
tokens=read(S/'stream/closure-tokens.bin');ck(len(tokens)==52*168 and (S/'stream/scores.f32').stat().st_size==journalcells*4 and (S/'stream/numeric-origins.bin').stat().st_size==journalcells*9,'terminal token score origin extents')
for i in range(48,52):
 bs=[read(S/'matching'/f'{i:08d}{s}') for s in ('.pending.json','.records.bin','.complete.json')];p=json.loads(bs[0]);m=json.loads(bs[2]);ck((p['start'],p['stop'])==(i*4096,(i+1)*4096),'local tail pending range '+str(i));ck(m['pending_sha256']==sha(bs[0]) and m['payload_sha256']==sha(bs[1]) and m['payload_bytes']==len(bs[1])==92+4096*53,'local tail actual body closure '+str(i))
 for j,b in enumerate(bs):
  dev,ino,size,digest=struct.unpack_from('>QQQ32s',tokens,(i*3+j)*56);ck(size==len(b) and digest.hex()==sha(b),'local tail original token '+str(i)+'/'+str(j))
# Passive terminal process and path observations only; no process actions.
pids=[8425,9258,9741,10197,10200];absence={str(pid):not Path('/proc',str(pid)).exists() for pid in pids};ck(all(absence.values()) and not Path(final['cgroup']).exists(),'all five observed processes and original cgroup currently absent')
ck(all(str(pid) in processhistory['processes'] for pid in pids),'all five original process observations retained')
for name in ('job.py','resources.py','compact_mcm_batched.py','batched_driver.py','real_pilot_import_caller.py'):
 path='tradingagents/research/onchain_replication/'+name;ck(sha(read(path,False))==exp['source_files'][path],'selected terminal/ordering source '+name)
missing=[str(p.relative_to(R)) for p in [RUN/'complete.json',RUN/'artifacts',REP/'complete.json',REP/'compact/complete.json',S/'stage-complete.json',mcmroot/'complete.json'] if not p.exists()]
result={'disposition':'ACCEPT_ACTUAL_FAILED_TERMINAL_AND_BOUNDED_PARTIAL_PROGRESS','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'read_bytes':nbytes,'input_limit_bytes':16*1024**2,'source':claim['source'],'claim_sha256':sha(claimb),'failed_sha256':sha(failedb),'registered_cells':cells,'root_exit':1,'monitor_child_exit':None,'guard_wrapper_exit':125,'guard_wrapper_reason':'signal','worker_exit':None,'process_absence':absence,'cgroup_absent':not Path(final['cgroup']).exists(),'completed_journal_cells':journalcells,'computed_summary_cells':computed,'reused_summary_cells':reused,'first_graph_cells':mcmstart['cells'],'whole_seven_graph_cells':totalcells,'whole_mcm_graphs_completed':0,'reviewed_external_groups':3,'external_reviewed_cells':196608,'local_complete_tail_cells':16384,'pending_only_batches':0,'unstarted_or_without_journal_evidence_cells':totalcells-journalcells,'last_post_batch_return_proved_cells':51*4096,'last_batch_post_sink_final_callback_unknown':True,'numeric_inclusive_seconds_sum':seconds,'wall_seconds':final['elapsed_seconds'],'journal_cells_per_guard_elapsed_second':journalcells/final['elapsed_seconds'],'journal_cells_per_summed_numeric_second':journalcells/seconds,'observed_whole_denominator_fraction':journalcells/totalcells,'resource_fields':{k:final[k] for k in ('elapsed_time_kill','memory_current_bytes','peak_sampled_memory_current_bytes','memory_events','optional_memory_telemetry','storage_peak_allocated_bytes','storage_peak_logical_file_bytes','minimum_sampled_disk_free_bytes','storage_enforcement')},'financial_fits':0,'training_result':None,'training_complete':False,'absent_terminal_paths':missing,'incremental_accounting':{'accepted_preexisting_closed':68,'accepted_preexisting_complete':33,'accepted_preexisting_failed':35,'new_failed_claims':1,'closed_now':69,'complete_now':33,'failed_now':36,'active_now':0,'effective_attempt_budget':100,'qualification':'Incremental reconciliation from accepted preceding state plus exact original29 failed claim; no independent replay of all historical claim bodies. No refund, reopened identity or fresh-sample credit.'},'limits':{'cpu_seconds':30,'address_space_bytes':384*1024**2,'output_file_bytes':4*1024**2,'affinity':[3],'nice':10},'inventory':inventory,'not_claimed':['worker actual wait status or fabricated missing PID exit history','whole MCM completion or complete numeric binding','journaled scores mathematical correctness','training/optimizer/financial result from absent output','sampled peaks as continuous maximum or whole capacity','current remote availability beyond reused exact recovered groups','exact last-batch post_batch return or delivered counter from token/spool extents']}
(P/'REVIEW01.json').write_bytes(raw(result));print(json.dumps({k:result[k] for k in ('disposition','read_bytes','completed_journal_cells','first_graph_cells','numeric_inclusive_seconds_sum','journal_cells_per_guard_elapsed_second','journal_cells_per_summed_numeric_second','observed_whole_denominator_fraction')}));print('checks',len(checks),'sha',sha(raw(result)))
