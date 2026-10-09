import pathlib,json,hashlib,subprocess,datetime
ROOT=pathlib.Path.cwd();R=pathlib.Path(__file__).resolve().parent;F=R.parent;E=F/'real-data-pilot-full26-entry01-2026-10-09';name='eth-paper-real-data-end-to-end-resource-20261009-26';L=ROOT/'research_runs'/name;N=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/name
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();j=lambda p:json.loads(p.read_bytes());evidence={}
def load(p):evidence[str(p.relative_to(ROOT))]=h(p);return j(p)
c=load(L/'claim.json');f=load(L/'failed.json');assert f['claim_sha256']==h(L/'claim.json') and f['status']=='failed' and f['reason']=='ValueError: import lease: stale interval cannot refresh' and c['effective_attempt_budget']==97
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
nativepids=sorted({owner['supervisor_pid'],owner['monitor_pid'],cpu['pid'],child['workload_pid']});assert nativepids==[1976157,1976569,1976981,1976985]
pids=nativepids;ps=subprocess.run(['ps','-o','pid=,ppid=,stat=,args=','-p',','.join(map(str,pids))],capture_output=True,text=True);assert ps.returncode==1 and ps.stdout=='' and all(not pathlib.Path('/proc',str(p)).exists() for p in pids)
assert all(guard['memory_events'][k]==0 for k in ('high','max','oom','oom_kill','oom_group_kill'))
assert guard['peak_sampled_memory_current_bytes']==4314329088 and guard['optional_memory_telemetry']['unit']['kernel_peak_bytes']==4403785728
phase=load(E/'PHASE_OBSERVATION02.json');ref=phase['intent'];assert h(ROOT/ref['path'])==ref['sha256'];intent=load(ROOT/ref['path']);assert intent==ref['body'] and intent['kind']=='mcm'
stage=(ROOT/ref['path']).parent;pending=load(stage/'matching/00000000.pending.json');assert pending['disposition']=='attempted_unknown_without_complete' and pending['start']==0 and pending['stop']==4096
assert not (stage/'matching/00000000.complete.json').exists() and not (stage/'stage-complete.json').exists()
imp=load(stage.parent/'dictionary-import/import-complete.json');assert imp['kind']=='dictionary-import-complete';assert [x['phase'] for x in s['events']]==['original_import']
prior=load(F/'real-data-pilot-full25-outcome-review01-2026-10-09/OUTCOME_REVIEW01.json');assert prior['accounting']['closed_total']==65 and c['family']['prior_attempts']==17
rootreceipt=F/'real-data-pilot-full26-root-closure01-2026-10-09/ROOT_TERMINAL01.json';rootjoin=None
if rootreceipt.exists():rootjoin=load(rootreceipt)
summary=load(stage/'stream/numeric-batches/000000000000.json');origin=stage/'stream/numeric-origins.bin';evidence[str(origin.relative_to(ROOT))]=h(origin)
assert origin.stat().st_size==36864 and h(origin)==summary['origin_sha256'] and summary['computed']==4000 and summary['reused']==96 and summary['start']==0 and summary['stop']==4096
assert (stage/'stream/scores.f32').stat().st_size==(stage/'stream/closure-tokens.bin').stat().st_size==0
producer=ROOT/phase['producer_start']['path'];assert h(producer)==phase['producer_start']['sha256'];load(producer);producer_failure=load(producer.parent/'failed.json');assert producer_failure['status']=='failed'
trace=(N/'guard/child.log').read_text();evidence[str((N/'guard/child.log').relative_to(ROOT))]=h(N/'guard/child.log');assert 'batched_journal.py\", line 157' in trace and 'imported_authority_interval.py\", line 35' in trace
for module in ('batched_journal.py','batched_numeric_execution.py','imported_authority_interval.py','compact_mcm_batched.py'):
 p=ROOT/'tradingagents/research/onchain_replication'/module;assert h(p)==c['experiment']['source_files'][str(p.relative_to(ROOT))];evidence[str(p.relative_to(ROOT))]=h(p)
r={'decision':'accepted_failed_disposition_native_cleanup','identity':name,'evidence':evidence,'claim_sha256':h(L/'claim.json'),'failed_sha256':h(L/'failed.json'),'source':c['source'],'failure':f['reason'],'scientific_disposition':{'original_import_receipt_exists':True,'attempted_failed_graphs':1,'unavailable_graphs':6,'complete_graphs':0,'completed_cell_credit':0,'pending_declared_range':[0,4096],'pending_status':'attempted_unknown_without_complete','training':None,'financial_fit_credit':0,'attempted_mcm_seconds':t['attempted_mcm_seconds'],'numeric_batch_summary':summary,'opaque_origin_bytes':36864,'trace_inference':'Journal157 is after4096 validated executor returns/finite iterator close but before records and complete publication; summary records4000computed96reused. Numeric result records not durable.', 'qualification':'Pending range does not establish completed MCM score credit; summary and opaque origins are partial execution evidence only, not a complete result or binary semantic proof. No original array/binary parsing performed. Worker research ledger FAILED and native postmortem cell unavailable are distinct original records.'},'native':{'elapsed_seconds':guard['elapsed_seconds'],'child_exit':1,'supervisor_exit':1,'cleanup_verified':True,'observed_absent_native_pids':nativepids,'root_pid_current_absent':None,'root_pid_identity_provenance':'Earlier inferred Root PID1975313 is not authenticated and is excluded; original receipts cover four native/supervisor PIDs only.','ps_returncode':ps.returncode,'ps_stdout':ps.stdout,'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cgroup_absent':True,'sampled_memory_current_peak_bytes':4314329088,'optional_last_kernel_peak_bytes':4403785728,'memory_events':guard['memory_events'],'unit_optional_swap_bytes':guard['optional_memory_telemetry']['unit']['swap_current_bytes'],'qualification':'Optional last kernel peak includes charged cache and may precede final lifetime peak. User ancestor telemetry is not workload-only. No RSS or wholecapacity conclusion.'},'root_terminal_receipt':rootjoin,'accounting':{'prior_review_closed':65,'this_irrevocably_spent':1,'closed_total':66,'complete_total':33,'failed_total':33,'highest_claimed_allowance':97,'refunds':0,'qualification':'Prior accepted cumulative accounting reused; only actual26 failed claim added, no historical recount.'},'qualification':'Original eight output hashes, import/first-MCM metadata, native cleanup and sampled final storage joined. Rootsession terminal receipt, if absent, remains pending rather than inferred from supervisor exit. No new trial, mathematical success, preservation/recovery, binary semantics or deletion authority.'}
(R/'OUTCOME_REVIEW01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'sha256':h(R/'OUTCOME_REVIEW01.json'),'root_receipt_present':rootjoin is not None}))
