"""Original full33 terminal evidence only; stdlib, no authority or numerical execution."""
import datetime,hashlib,json,os,re,resource,signal,stat,subprocess
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(20,20));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(40)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];E=P/'evidence';E.mkdir()
ID='eth-paper-real-data-end-to-end-resource-20261011-33';SOURCE='2358fca94e45c3416d94a3d9bbfb57c27da25d12'
ENTRY=F/'real-data-pilot-full33-entry-preparation01-2026-10-11';RUN=R/'research_runs'/ID;A=R/'research_artifacts/onchain-paper-replication-2026-09-24';N=A/'runs'/ID
WF='302049e6d5d1f55046c6fc6dfeb187d8ea8903ac21a6444b0d19bcdc2031a02a';REP=R/'research_artifacts/onchain_representations'/WF/ID;ARCH=R/'research_artifacts/archive-dispatch-ethpilot-20261011-33'
inventory={};checks=[];nbytes=0
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(ok,name):
    checks.append({'name':name,'pass':bool(ok)})
    if not ok:raise AssertionError(name)
def raw(p):
    global nbytes
    p=Path(p);p=p if p.is_absolute() else R/p
    assert not ({'.git','.venv','keys','apis'}&set(p.parts)) and p.name not in ('.env','connection.json','archive_transport01.json')
    s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<4*1024**2
    b=p.read_bytes();t=p.lstat();ck(all(getattr(s,k)==getattr(t,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')) and len(b)==s.st_size,'stable original '+str(p.relative_to(R)))
    nbytes+=len(b);assert nbytes<16*1024**2
    key=str(p.relative_to(R))
    if key not in inventory:
        name=f'{len(inventory):03d}-'+p.name;(E/name).write_bytes(b);inventory[key]={'bytes':len(b),'sha256':sha(b),'snapshot':'evidence/'+name}
    else:ck(inventory[key]['sha256']==sha(b),'original unchanged on reread '+p.name)
    return b
def js(p):return json.loads(raw(p))
claimb=raw(RUN/'claim.json');claim=json.loads(claimb);failedb=raw(RUN/'failed.json');failed=json.loads(failedb)
ck(sha(claimb)=='3f810d32d71adbfc625716e157cf061a0c4587a2e2319ab58b310a771a84f0ce' and sha(failedb)=='a537acb807fabc462ff06dcf57506ad6566241f97541976c6bb9e74914d2eb1f' and failed['claim_sha256']==sha(claimb),'original claim/failed anchors')
gateb=raw(ENTRY/'gate01.json');gate=json.loads(gateb);exp=gate['experiments'][ID]
ck(sha(gateb)==claim['registration_sha256']=='6ff8b166d62d901d1e22a49d958656a6390cf6a98ea321c1a379233a90d0f6d4' and exp==claim['experiment'],'claim/gate01 experiment join')
ck(claim['source']==claim['design_source']==SOURCE and claim['effective_attempt_budget']==104 and claim['bindings'] is None and claim['bindings_sha256'] is None,'actual source adopted104 and original null claim bindings')
ck(failed['status']=='failed' and failed['reason']=='ValueError: import lease: stale interval cannot refresh' and not (RUN/'complete.json').exists(),'permanent original failed claim')
outputs={}
ck(set(p.name for p in (RUN/'outputs').iterdir())==set(failed['output_sha256']) and len(failed['output_sha256'])==8,'exact eight original output denominator')
for name,digest in failed['output_sha256'].items():
    b=raw(RUN/'outputs'/name);ck(sha(b)==digest,'failed receipt authenticates '+name);outputs[name]=json.loads(b)
summary=outputs['pilot-summary.json'];through=summary['throughput'];graphs=through['graphs'];cell=summary['cell']
ck(outputs['cell-ledger.json']==[cell] and [cell['id']]==exp['cells'] and cell['status']=='failed','worker output cell failed disposition')
ck(summary['training'] is None and summary['retained_target_count']==0 and summary['financial_fit_complete'] is False and summary['full_size_capacity'] is False,'absent training retained target and financial completion')
ck(len(graphs)==through['graph_denominator']==7 and [g['status'] for g in graphs].count('failed')==1 and [g['status'] for g in graphs].count('unavailable')==6,'complete seven graph failed/unavailable denominator')
ck(through['complete_graphs']==through['verified_completed_motif_cells']==through['verified_completed_nodes']==through['paper_financial_fits']==0 and through['one_update_phase_seconds'] is None,'zero verified completion not imputed partial work')
ck(all(g['completed_motif_cells'] is None and g['completed_nodes'] is None and g['expected_motif_cells']==32*g['expected_nodes'] for g in graphs),'partial quantities unknown and expected denominator arithmetic')
ck(sum(g['expected_motif_cells'] for g in graphs)==415968128,'expected seven graph denominator415968128')
ck(outputs['resource-binding.json']==outputs['resource-journal.json'] and outputs['resource-binding.json']['status']=='failed','failure-only output placeholders not actual Binding/Owner terminals')
pop=outputs['resource-population.json'];pb=outputs['resource-population-binding.json']
ck(len(pop['resource_rows'])==len(pop['decision_dates'])==16 and pop['source_population_eligible_training_count']==22 and pop['paper_financial_fits']==0 and pop['full_fold_population'] is False and pop['full_fold_scaler'] is False,'resource16 subset retains no full-fold claim')
ck(pb['resource_train_hash']==pop['resource_train_hash'] and pb['graph_manifest_hashes']==pop['graph_manifest_hashes'] and len(pb['graph_manifest_hashes'])==7 and pb['plan_sha256']==claim['inputs']['resource_population_plan']['sha256'],'population metadata joins only, no scaler recomputation')
for row in pop['resource_rows']:
    ck(row['max_input_available_at']<=row['decision_at'] and max(row['graph_available_at'])<=row['decision_at'] and len(row['input_dates'])==len(row['graph_available_at'])==28,'reported resource-row availability bounded by decision')
launch=js(N/'launch.json');owner=js(N/'owner.json');finalb=raw(N/'guard/final.json');final=json.loads(finalb);liveb=raw(N/'guard/live.json');death=js(N/'guard/observer-death.json');child=js(N/'guard/child_exit.json');observer=js(N/'observer.json');cells=js(N/'postmortem-cells.json');unsealed=js(N/'unsealed-journals.json')
freeze=js(ENTRY/'SOURCE_FREEZE01.json');closed=js(ENTRY/'ROOT_IO_CLOSED01.json');storage=js(ENTRY/'FINAL_STORAGE01.json');history=js(ENTRY/'LIVE_LAUNCH_OBSERVATION01.json');history2=js(ENTRY/'LIVE_RESOURCE_OBSERVATION02.json');import_history=js(ENTRY/'DICTIONARY_IMPORT_OBSERVATION03.json')
ck(freeze['source']==SOURCE and freeze['identity']==ID and freeze['release']['sha256']=='c611ec6ac8b7828f2de1dbc832b1cdf544666b01e8e79452f702840bce2ec203' and owner==final['owner_identity'] and launch['source_commit']==SOURCE,'same original frozen source and process owner')
for role in ('binding','gate','release','current_preparation_recovery','current_read_only_preflight'):
    row=freeze[role];b=raw(row['path']);ck(sha(b)==row['sha256'] and len(b)==row['bytes'],'original frozen reference '+role)
ck(history['source']==SOURCE and history['root_io_session']==history2['root_io_session']==47250 and history['claim']['sha256']==sha(claimb) and child['workload_pid'] in [p['pid'] for p in history['actual_native_processes']] and history['cgroup']==history2['cgroup']==final['cgroup'],'actual original live session worker and claim joins')
ck(closed['actual_parent_exit_code']==1 and closed['supervisor_reaped'] and closed['outer_log_handles_closed'] and closed['supervisor_pid']==launch['supervisor_pid'],'RootIO original parent reaped and logs closed')
ck(liveb==finalb and final['phase']=='failed' and final['child_exit_code']==child['exit_code']==1 and child['reason']=='workload exited' and child['snapshot_error'] is None,'normal worker exit1 observed by native guard')
ck(final['cleanup_verified'] and final['cleanup_stop_returncode']==0 and final['cleanup_unit_properties']['ControlGroup']=='' and final['cleanup_unit_properties']['Result']=='exit-code' and final['elapsed_time_kill'] is False,'recorded cleanup; not elapsed-time kill')
ck(final['kernel_controls']=={'memory.high':'5368709120','memory.max':'6442450944','memory.swap.max':'0'} and final['native_unit_properties']=={'LimitFSIZE':'1073741824','LimitFSIZESoft':'1073741824','RuntimeMaxUSec':'8h'} and final['cpus']==[0,1],'actual native5/6GiB swap0 twoCPU8h1GiBfile history')
ck(all(v==[0,1] for v in final['cpu_thread_readback'].values()) and final['memory_events']['oom']==final['memory_events']['oom_kill']==final['memory_events']['max']==0,'thread affinity and no recorded OOM/max event')
ck(final['terminal_memory_snapshot']==child['terminal_memory_snapshot'] and child['terminal_memory_snapshot']['optional_memory_telemetry']['unit']['kernel_peak_bytes']==5370646528,'terminal memory evidence join and scoped kernel peak')
for name,digest in observer['evidence_sha256'].items():ck(sha(raw(N/name))==digest,'observer evidence '+name)
ck(observer['owner_sha256']==sha(raw(N/'owner.json')) and observer['terminal_sha256']==sha(failedb) and observer['cgroup_empty'] and observer['financial_completion'] is False,'observer owner terminal cleanup joins')
ck([c['id'] for c in cells]==exp['cells'] and cells[0]['status']=='unavailable' and unsealed==[] and observer['unsealed_journals']==0,'separate unavailable outer postmortem retained, no unsealed journal')
parent=A/'pilot-parent'/ID;ck(json.loads(raw(parent/'stdout.log'))==observer and raw(parent/'stderr.log')==b'','original parent output equals observer')
log=raw(N/'guard/child.log').decode()
ck('compact_mcm_batched.py", line 499, in produce' in log and 'compact_mcm.py", line 176, in _prepare' in log and 'dictionary.check()' in log and 'imported_authority_interval.py", line 44, in validate' in log and 'try:freshness(full_done)' in log,'actual traceback fails inside original preparation full-callback freshness')
match=re.search(r'full_callback_seconds=([0-9.]+); pre_callback_age_seconds=([0-9.]+); total_age_seconds=([0-9.]+)',log);ck(match is not None,'actual original timing diagnostic');full,pre,total=map(float,match.groups())
ck(abs(full+pre-total)<1e-8 and (full,pre,total)==(11.354144623001048,51.80366844699893,63.157813069999975),'actual timing arithmetic')
lease=js(R/claim['inputs']['imported_authority_lease']['path']);ck(lease['max_stale_ms']==60000 and pre*1000<lease['max_stale_ms']<total*1000,'freshness crossed unchanged60second limit during full callback')
ck('loaded module/function identity changed' not in log,'current terminal is freshness refusal, not prior31 identity refusal')
repowner=js(REP/'owner.json');repstart=js(REP/'start.json');repfail=js(REP/'failed.json');compact=js(REP/'compact/owner.json');intentb=raw(REP/'compact/dictionary-import/intent.json');intent=json.loads(intentb);imported=js(REP/'compact/dictionary-import/import-complete.json');archive_start=js(REP/'archive-operations/start.json')
ck(repowner==repfail['owner']==repstart['owner'] and repowner['workflow_identity']==WF and repfail['workflow_identity'] is None and repstart['workflow_identity'] is None and repfail['events']==[],'genuine representation owner and original workflow nulls retained')
binding=compact['binding'];ck(binding['claim_sha256']==sha(claimb) and binding['registration_sha256']==claim['registration_sha256'] and binding['source_commit']==SOURCE and binding['workflow_identity']==WF,'actual compact Binding metadata exists and joins claim')
ck(imported['intent_sha256']==sha(intentb) and imported['owner']==intent['owner']==archive_start['owner'] and imported['current_matching_pairs']==0 and imported['numeric']['owner_stage_completed'] is False and imported['historical_work_recomputed'] is False,'original import-only evidence; no dictionary Owner-stage completion')
ck(len(imported['numeric']['ordered_motifs'])==32 and imported['execution']['mcm_execution_admitted'] is False,'historical32 import receipt not current matching completion')
archreceipt=outputs['archive-receipt.json'];archterminal=outputs['archive-terminal.json'];archintentb=raw(ARCH/'intent.json');archintent=json.loads(archintentb)
ck(sha(archintentb)==archreceipt['intent_sha256']==archterminal['intent_sha256'] and archintent['claim_sha256']==sha(claimb) and archintent['source_commit']==SOURCE,'genuine archive context intent/claim join; no private transport read')
ck(js(ARCH/'terminal.json')==archterminal and archterminal['spent']=={'commands':0,'logical_bytes':0,'rounded_bytes':0} and archterminal['status']=='failed' and archterminal['wire_bytes_measured'] is False,'zero declared archive transfers; no remote recovery claim')
ck(all(x['acknowledged_records']==x['shards']==0 for x in archterminal['control_history'].values()),'no acknowledged archive control operations')
absent=[RUN/'complete.json',RUN/'artifacts',REP/'complete.json',REP/'compact/complete.json',REP/'compact/dictionary-import/stage-complete.json',R/'research_artifacts/onchain_compact_mcm'/WF/ID]
absent.extend(REP/'compact'/('mcm-'+g['graph_hash']) for g in graphs)
ck(all(not p.exists() for p in absent),'no current MCM/stage/Owner/training completion paths')
for name in ['job.py','compact_mcm_batched.py','real_pilot_import_caller.py','compact_mcm.py','imported_mcm_identity.py','imported_authority_interval.py','imported_authority_lease.py']:
    path='tradingagents/research/onchain_replication/'+name;ck(sha(raw(path))==exp['source_files'][path],'actual failure/order source pin '+name)
source=raw('tradingagents/research/onchain_replication/compact_mcm_batched.py').decode();lines=source.splitlines()
ck(sha(source.encode())=='e93d3b7073c8de5d1c3e7f5f30b55ba613b47a014f8fe449a0fe7e8a746941dd' and 'producer._prepare(' in lines[498] and "_entry_lease(target,b['execution'])" in lines[500] and 'root=producer.directory' in lines[511],'actual499failure precedes firstextra501 and MCMdirectory512; no ambiguous ordinal')
ck(final['elapsed_seconds']==1084.079638119998 and through['attempted_mcm_seconds']==220.89301278299536,'scoped original wall and attempted-stage timing only')
priorb=raw(F/'pilot32-terminal-outcome-review01-2026-10-11/REVIEW01.json');ck(sha(priorb)=='bbcd9d0e7474890fecc034e6ea7969c13a885f15ac593cf81e2d1d732bd196e9','accepted prior72closed accounting');prior=json.loads(priorb)['incremental_accounting'];ck((prior['closed_now'],prior['complete_now'],prior['failed_now'],prior['active_now'],prior['highest_adopted_ceiling'])==(72,33,39,0,103),'accepted prior count denominator')
correction=raw(F/'pilot31-terminal-locator-correction01-2026-10-11/CORRECTION01.json');ck(sha(correction)=='6b230b1a18667d06b01682ec50a19293d011ccb0ddae689eef5c8b5edc00911a','prior31 separate second-boundary correction retained')
pids=sorted({launch['supervisor_pid'],owner['monitor_pid'],child['workload_pid'],history['actual_root']['pid']}|{v['pid'] for v in history['actual_native_processes']}|set(map(int,final['cpu_thread_readback'])))
ck({1801052,1801972,1802462,1802890,1802893,1809618}<=set(pids),'all six original Root/native PIDs included')
process_absence={str(pid):not Path('/proc',str(pid)).exists() for pid in pids};ck(all(process_absence.values()) and not Path(final['cgroup']).exists(),'current original process/cgroup absence')
args=['systemctl','--user','show',final['unit'],'--property=LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainStatus'];p=subprocess.run(args,capture_output=True,timeout=10)
(P/'unit-readback.stdout').write_bytes(p.stdout);(P/'unit-readback.stderr').write_bytes(p.stderr);properties=dict(x.split('=',1) for x in p.stdout.decode().splitlines() if '=' in x)
ck(p.returncode==0 and properties['MainPID']=='0' and properties['ControlGroup']=='' and properties['ActiveState'] in ('failed','inactive'),'current exact unit stopped with no MainPID/cgroup')
ck(storage['original_metadata_sha256']=={'guard':sha(finalb),'launch':sha(raw(N/'launch.json')),'owner':sha(raw(N/'owner.json'))} and storage['actual_current_cgroup_absent'] and storage['original_monitor_process_absent'],'Root final storage closure joins originals')
root_terminal=js(ENTRY/'ROOT_TERMINAL_OPERATION01.json')
ck(sha(raw(ENTRY/'ROOT_TERMINAL_OPERATION01.json'))=='175e111cf2d3829951b3130b7fc348fd764b6d0fe6602db41c07eae71f654245','exact Root terminal original metadata')
ck(root_terminal['source']==SOURCE and root_terminal['identity']==ID and root_terminal['actual_root_session']==47250 and root_terminal['actual_root_exit']==1 and root_terminal['actual_terminal_tool']=='bbbbfd','Root terminal original session/source/exit joined')
for k in ('original_final_storage','original_guard_final','original_root_io','original_workflow_failed'):
 v=root_terminal[k];b=raw(v['path']);ck(sha(b)==v['sha256'] and len(b)==v['bytes'],'Root original terminal binding '+k)
ck(all(process_absence[str(pid)] for pid in root_terminal['actual_original_observed_pids_absent']) and root_terminal['actual_original_cgroup_absent'] and root_terminal['scientific_source_freeze_ended'],'Root current closure agrees with original six observed PIDs')
ck(all(properties[k]==v for k,v in root_terminal['actual_current_unit_properties'].items()),'Root actual terminal unit properties equal independent current readback')
ck(sha(raw(import_history['actual_dictionary_import_receipt']['path']))==import_history['actual_dictionary_import_receipt']['sha256']=='f76ec14b15bd61d2b6d36c85f9a587ca42037406d7332a22dea0a5daf39fc88a','original live and terminal dictionary import bytes match')
ck(not (R/'research_runs/eth-paper-real-data-end-to-end-resource-20261011-34').exists(),'no next claim or105 adoption at fixed successor path')
ck(sha(raw('tradingagents/research/onchain_replication/compact_mcm.py'))=='becaab002648c440852553ebf1e662702affee96283a07bcb90bdfc2ca7379ca' and sha(raw('tradingagents/research/onchain_replication/real_pilot_import_caller.py'))=='f65ff353315bfb9e4db80d326170e02e5b2ebc6da1e5d59e5a8e9243b4afd11a','current exact admitted beca/f65 source bodies')

out={'disposition':'ACCEPT_ACTUAL_PILOT33_FAILED_TERMINAL_WITH_PRESERVED_DISPOSITIONS','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':SOURCE,'claim_sha256':sha(claimb),'failed_sha256':sha(failedb),'checks':checks,'inventory':inventory,'read_bytes':nbytes,'original_output_count':8,'worker_output_cells':[cell],'outer_postmortem_cells':cells,'failure_location':{'caller':'compact_mcm_batched.py:499','prepare':'compact_mcm.py:176 dictionary.check','guard':'imported_authority_interval.py:44 freshness(full_done)','reason':failed['reason'],'first_extra_boundary_reached':False},'lease_timing_seconds':{'pre_callback_age':pre,'full_callback':full,'total':total},'wall_seconds':final['elapsed_seconds'],'whole_graphs_completed':0,'expected_whole_motif_cells':415968128,'verified_completed_motif_cells':0,'partial_computed_cells':None,'training':None,'financial_fits':0,'missing_completion_paths':[str(x.relative_to(R)) for x in absent],'process_absence':process_absence,'current_unit':properties,'current_unit_command':args,'recorded_resources':{k:final[k] for k in ['memory_events','peak_sampled_memory_current_bytes','optional_memory_telemetry','storage_peak_allocated_bytes','storage_peak_logical_file_bytes','minimum_sampled_disk_free_bytes']},'incremental_accounting':{'accepted_prior_closed':72,'accepted_prior_complete':33,'accepted_prior_failed':39,'new_failed_claims':1,'closed_now':73,'complete_now':33,'failed_now':40,'active_now':0,'highest_adopted_ceiling':104,'qualification':'Accepted72 baseline plus exact new genuine failed33; historical claim bodies not replayed; no retry/refund or fresh exposure.'},'raw_scopes':[str(x.relative_to(R)) for x in (RUN,N,parent,REP,ARCH)],'pid_history':None,'qualifications':['Only the six originally observed processes and recorded final threads were checked; absent complete native PID history remains unknown.','Worker output cell failed and outer postmortem cell unavailable are separate original dispositions.','Import-complete confirms existing32 import metadata, explicitly not Owner-stage or MCM execution completion.','Claim/representation nulls preserved alongside genuine compact Binding/Owner and archive context; no manufactured replacement fields.','Native cleanup and sampled/kernellifetime memory evidence do not prove capacity or attribute freshness refusal to memory pressure.','No numerical/authority execution, private target/credential read, Git/network operation or remote preservation claim.','Resource-row timing metadata checked against decisions only; source data, labels/scaler correctness, financial return convention/fees/funding and strategy viability untested.']}
with (P/'REVIEW01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:out[k] for k in ['disposition','claim_sha256','failed_sha256','read_bytes','failure_location','incremental_accounting','current_unit']},sort_keys=True));print('checks',len(checks))
