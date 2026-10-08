import hashlib,json,os,stat,datetime
from pathlib import Path
R=Path.cwd();NAME='eth-paper-real-data-end-to-end-resource-20261008-20';F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N=F/'real-data-pilot-final20-2026-10-08';H=Path(__file__).resolve().parent;RR=R/'research_runs'/NAME;RUN=R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME
evidence={};checks=[]
def read(p):
 b=p.read_bytes();evidence[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(read(p))
def check(n,v):
 assert v,n
 checks.append(n)
claim=load(RR/'claim.json');failed=load(RR/'failed.json');guard=load(RUN/'guard/final.json');observer=load(RUN/'observer.json');owner=load(RUN/'owner.json');launch=load(RUN/'launch.json');child=load(RUN/'guard/child_exit.json');closed=load(N/'ROOT_IO_CLOSED01.json');storage=load(N/'FINAL_STORAGE01.json');handle=load(N/'EXEC_HANDLE02.json')
check('claim_exact',evidence[str((RR/'claim.json').relative_to(R))]==failed['claim_sha256']=='ce05e82e44bdc4f53dd9a41b5d0ae2395c7eeda3f0a4064ec1e0d30a3fb00466')
check('genuine_consumed91',claim['effective_attempt_budget']==91 and claim['experiment_id']==NAME and failed['status']=='failed' and not (RR/'complete.json').exists())
source=claim['source'];check('all_source_joins',source=='2ee1b9aa88e28401f6ae73db2188ab16910692c1' and all(x==source for x in (owner['source_commit'],launch['source_commit'],storage['source'],handle['source'])))
check('primary_failure',failed['reason']=='ValueError: pair limits differ')
for name,h in failed['output_sha256'].items():check('terminal_output_'+name,hashlib.sha256(read(RR/'outputs'/name)).hexdigest()==h)
summary=load(RR/'outputs/pilot-summary.json');diagnostic=load(RR/'outputs/real-pilot-scoring-diagnostic.json');cell=load(RR/'outputs/cell-ledger.json');postmortem=load(RUN/'postmortem-cells.json')
check('no_scoring',diagnostic['completed_scalar_pairs']==0 and all(v['calls']==0 and v['seconds']==0 for v in diagnostic['phase_timings'].values()) and diagnostic['planned_stop_reached'] is False)
check('all_seven_unavailable',len(summary['throughput']['graphs'])==7 and all(v['status']=='unavailable' and v['reason']=='not_attempted_after_failure' for v in summary['throughput']['graphs']))
check('no_training_or_credit',summary['training'] is None and summary['retained_target_count']==0 and summary['throughput']['verified_completed_motif_cells']==0 and not summary['financial_fit_complete'])
check('inner_cell_failed',len(cell)==1 and cell[0]['status']=='failed' and cell[0]['reason']==failed['reason'])
check('outer_postmortem_unavailable',len(postmortem)==1 and postmortem[0]['status']=='unavailable')
check('placeholder_binding_and_journal',load(RR/'outputs/resource-binding.json')==load(RR/'outputs/resource-journal.json') and load(RR/'outputs/resource-binding.json')['status']=='failed')
check('cleanup_guard',guard['cleanup_verified'] is True and guard['child_exit_code']==child['exit_code']==1 and not guard['elapsed_time_kill'])
check('no_oom_or_swap',guard['memory_events']['oom']==guard['memory_events']['oom_kill']==0 and guard['optional_memory_telemetry']['unit']['swap_current_bytes']==0)
check('actual_parent_closed',closed['actual_parent_exit_code']==1 and closed['supervisor_reaped'] and closed['outer_log_handles_closed'])
check('current_observed_cleanup',storage['actual_current_cgroup_absent'] and storage['original_monitor_process_absent'] and storage['actual_current_unit_properties']['MainPID']=='0')
check('observer_failed_cleanup',observer['status']=='failed' and observer['cgroup_empty'] and observer['unsealed_journals']==0)
for name,h in observer['evidence_sha256'].items():check('observer_evidence_'+name,hashlib.sha256(read(RUN/name)).hexdigest()==h)
check('observer_terminal',observer['terminal_sha256']==evidence[str((RR/'failed.json').relative_to(R))])
for key,p in [('guard',RUN/'guard/final.json'),('owner',RUN/'owner.json'),('launch',RUN/'launch.json')]:check('finalstorage_'+key,storage['original_metadata_sha256'][key]==hashlib.sha256(read(p)).hexdigest())
log=read(RUN/'guard/child.log').decode();check('actual_trace_seam','matching_owner.py", line 200, in bind' in log and "set(limits)==matching_pair.POLICY_FIELDS" in log and log.rstrip().endswith('ValueError: pair limits differ'))
# No source execution: confirm frozen declared bytes only.
source_mismatch=[]
for p,h in claim['experiment']['source_files'].items():
 if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h:source_mismatch.append(p)
check('source_still_frozen',not source_mismatch)
pids={int(owner['monitor_pid']),int(owner['supervisor_pid']),int(child['workload_pid'])}|{int(p) for p in guard['cpu_thread_readback']}
proc={str(p):(Path('/proc')/str(p)).exists() for p in sorted(pids)};check('original_pids_absent',not any(proc.values()))
archive=load(RR/'outputs/archive-terminal.json');check('no_archive_commands',archive['status']=='failed' and archive['spent']['commands']==0)
result={'schema_version':1,'decision':'accepted-failed-outcome','identity':NAME,'source':source,'claim_sha256':failed['claim_sha256'],'effective_attempt_budget':91,'evidence':evidence,'checks':checks,'primary_reason':failed['reason'],'diagnostic_completed_pairs':0,'planned_stop_reached':False,'graphs_unavailable':7,'training':None,'root_supervisor_exit':1,'native_child_exit':1,'guard_elapsed_seconds':guard['elapsed_seconds'],'sampled_peak_memory_current_bytes':guard['peak_sampled_memory_current_bytes'],'last_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes'],'pid_observation':proc,'source_mismatch':source_mismatch,'qualification':'Genuine failed20 consumes91; never rerun. Inner worker cell is failed; separate postmortem cell remains unavailable and is not silently rewritten. Original monitor/supervisor/workload PIDs absent at review; guarded cleanup corroborated by final receipts. Source bytes remain frozen. Root CLI tool exit receipt still joined separately. Kernel peak includes charged cache and is last read, not guaranteed final lifetime RSS. Public increment selection/recovery is separate; no numerical/source tests or native work performed.'}
(H/'OUTCOME_REVIEW01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':result['decision'],'checks':len(checks),'sha256':hashlib.sha256((H/'OUTCOME_REVIEW01.json').read_bytes()).hexdigest()}))
