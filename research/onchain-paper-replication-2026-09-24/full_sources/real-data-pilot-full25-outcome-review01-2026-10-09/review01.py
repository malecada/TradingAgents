import pathlib,json,hashlib,subprocess,datetime
ROOT=pathlib.Path.cwd();R=pathlib.Path(__file__).resolve().parent;F=R.parent;E=F/'real-data-pilot-full25-entry01-2026-10-09';name='eth-paper-real-data-end-to-end-resource-20261009-25';L=ROOT/'research_runs'/name;N=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/name
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();j=lambda p:json.loads(p.read_bytes());evidence={}
def load(p):evidence[str(p.relative_to(ROOT))]=h(p);return j(p)
c=load(L/'claim.json');f=load(L/'failed.json');assert f['claim_sha256']==h(L/'claim.json') and f['status']=='failed' and f['reason']=='ValueError: pair policy schema' and c['effective_attempt_budget']==96
outputs={}
for n,pin in f['output_sha256'].items():assert h(L/'outputs'/n)==pin;outputs[n]=load(L/'outputs'/n)
assert len(outputs)==8
s=outputs['pilot-summary.json'];t=s['throughput'];assert s['training'] is None and s['retained_target_count']==0 and not s['financial_fit_complete'] and outputs['cell-ledger.json']==[s['cell']]
assert s['cell']['status']=='failed' and s['cell']['paper_financial_fits']==0 and t['complete_graphs']==0 and t['failed_graphs']==1 and t['unavailable_graphs']==6
assert t['verified_completed_motif_cells']==t['verified_completed_nodes']==0 and sum(g['expected_motif_cells'] for g in t['graphs'])==415968128
assert t['graphs'][0]['status']=='failed' and t['graphs'][0]['reason']==f['reason'] and t['graphs'][0]['elapsed_seconds']==t['attempted_mcm_seconds']
for g in t['graphs']:assert g['completed_motif_cells'] is None and g['completed_nodes'] is None
for g in t['graphs'][1:]:assert g['status']=='unavailable' and g['elapsed_seconds'] is None
assert outputs['resource-binding.json']==outputs['resource-journal.json'] and outputs['resource-binding.json']['status']=='failed'
assert outputs['archive-terminal.json']['spent']=={'commands':0,'logical_bytes':0,'rounded_bytes':0}
guard=load(N/'guard/final.json');launch=load(N/'launch.json');owner=load(N/'owner.json');observer=load(N/'observer.json');post=load(N/'postmortem-cells.json');child=load(N/'guard/child_exit.json');cpu=load(N/'guard/cpu_ready.json');io=load(E/'ROOT_IO_CLOSED01.json');fs=load(E/'FINAL_STORAGE01.json')
assert guard['cleanup_verified'] and guard['child_exit_code']==child['exit_code']==io['actual_parent_exit_code']==1
assert io['supervisor_reaped'] and io['outer_log_handles_closed'] and io['supervisor_pid']==owner['supervisor_pid']==launch['supervisor_pid']
assert owner['nonce']==launch['nonce'] and owner['monitor_pid']==guard['monitor_pid'] and launch['source_commit']==c['source']==fs['source']
for n,pin in observer['evidence_sha256'].items():assert h(N/n)==pin
assert observer['terminal_sha256']==h(L/'failed.json') and observer['owner_sha256']==h(N/'owner.json') and observer['cgroup_empty']
assert post[0]['status']=='unavailable' and post[0]['reason']=='owned worker ended before durable cell disposition; no retry'
for k,p in [('guard',N/'guard/final.json'),('owner',N/'owner.json'),('launch',N/'launch.json')]:assert fs['original_metadata_sha256'][k]==h(p)
assert fs['actual_current_cgroup_absent'] and fs['original_monitor_process_absent'] and not pathlib.Path(guard['cgroup']).exists()
nativepids=sorted({owner['supervisor_pid'],owner['monitor_pid'],cpu['pid'],child['workload_pid']});assert nativepids==[1764785,1765212,1765648,1765651]
pids=[1763948]+nativepids;ps=subprocess.run(['ps','-o','pid=,ppid=,stat=,args=','-p',','.join(map(str,pids))],capture_output=True,text=True);assert ps.returncode==1 and ps.stdout=='' and all(not pathlib.Path('/proc',str(p)).exists() for p in pids)
assert all(guard['memory_events'][k]==0 for k in ('high','max','oom','oom_kill','oom_group_kill'))
assert guard['peak_sampled_memory_current_bytes']==5182185472 and guard['optional_memory_telemetry']['unit']['kernel_peak_bytes']==5294460928
phase=load(E/'PHASE_OBSERVATION02.json');ref=phase['actual_intent'];assert h(ROOT/ref['path'])==ref['sha256'];intent=load(ROOT/ref['path']);assert intent==ref['body'] and intent['kind']=='mcm'
stage=(ROOT/ref['path']).parent;pending=load(stage/'matching/00000000.pending.json');assert pending['disposition']=='attempted_unknown_without_complete' and pending['start']==0 and pending['stop']==4096
assert not (stage/'matching/00000000.complete.json').exists() and not (stage/'stage-complete.json').exists()
imp=load(stage.parent/'dictionary-import/import-complete.json');assert imp['kind']=='dictionary-import-complete';assert [x['phase'] for x in s['events']]==['original_import']
prior=load(F/'real-data-pilot-full24-outcome-review01-2026-10-09/OUTCOME_REVIEW01.json');assert prior['accounting']['total_closed']==64 and c['family']['prior_attempts']==17
rootreceipt=F/'real-data-pilot-full25-root-closure01-2026-10-09/ROOT_TERMINAL01.json';rootjoin=None
if rootreceipt.exists():rootjoin=load(rootreceipt)
r={'decision':'accepted_failed_disposition_native_cleanup','identity':name,'evidence':evidence,'claim_sha256':h(L/'claim.json'),'failed_sha256':h(L/'failed.json'),'source':c['source'],'failure':f['reason'],'scientific_disposition':{'original_import_receipt_exists':True,'attempted_failed_graphs':1,'unavailable_graphs':6,'complete_graphs':0,'completed_cell_credit':0,'pending_declared_range':[0,4096],'pending_status':'attempted_unknown_without_complete','training':None,'financial_fit_credit':0,'attempted_mcm_seconds':t['attempted_mcm_seconds'],'qualification':'Pending range and first-stage intent do not prove4096 computations or any completed score. No original array/binary parsing performed. Worker research ledger FAILED and native postmortem cell unavailable are distinct original records.'},'native':{'elapsed_seconds':guard['elapsed_seconds'],'child_exit':1,'supervisor_exit':1,'cleanup_verified':True,'observed_absent_native_pids':nativepids,'root_pid_current_absent':1763948,'root_pid_identity_provenance':'Root task observation; original native receipts cover only four native/supervisor PIDs.','ps_returncode':ps.returncode,'ps_stdout':ps.stdout,'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cgroup_absent':True,'sampled_memory_current_peak_bytes':5182185472,'optional_last_kernel_peak_bytes':5294460928,'memory_events':guard['memory_events'],'unit_optional_swap_bytes':guard['optional_memory_telemetry']['unit']['swap_current_bytes'],'qualification':'Optional last kernel peak includes charged cache and may precede final lifetime peak. User ancestor telemetry is not workload-only. No RSS or wholecapacity conclusion.'},'root_terminal_receipt':rootjoin,'accounting':{'prior_review_closed':64,'this_irrevocably_spent':1,'closed_total':65,'complete_total':33,'failed_total':32,'highest_claimed_allowance':96,'refunds':0,'qualification':'Prior accepted cumulative accounting reused; only actual25 failed claim added, no historical recount.'},'qualification':'Original eight output hashes, import/first-MCM metadata, native cleanup and sampled final storage joined. Rootsession terminal receipt, if absent, remains pending rather than inferred from supervisor exit. No new trial, mathematical success, preservation/recovery, binary semantics or deletion authority.'}
(R/'OUTCOME_REVIEW01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'sha256':h(R/'OUTCOME_REVIEW01.json'),'root_receipt_present':rootjoin is not None}))
