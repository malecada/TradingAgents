import hashlib,json,os,stat,datetime
from pathlib import Path
import resource,signal
os.sched_setaffinity(0,{3,4});os.nice(10);resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(60)
R=Path.cwd();NAME='eth-paper-real-data-end-to-end-resource-20261008-22';F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N=F/'real-data-pilot-final22-2026-10-08';H=Path(__file__).resolve().parent;RR=R/'research_runs'/NAME;RUN=R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME
evidence={};checks=[]
def read(p):
 b=p.read_bytes();evidence[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(read(p))
def check(n,v):
 assert v,n
 checks.append(n)
claim=load(RR/'claim.json');failed=load(RR/'failed.json');guard=load(RUN/'guard/final.json');observer=load(RUN/'observer.json');owner=load(RUN/'owner.json');launch=load(RUN/'launch.json');child=load(RUN/'guard/child_exit.json');closed=load(N/'ROOT_IO_CLOSED01.json');storage=load(N/'FINAL_STORAGE01.json');terminal=load(N/'ROOT_TERMINAL01.json')
check('claim_exact',evidence[str((RR/'claim.json').relative_to(R))]==failed['claim_sha256']=='03e46135def01a13cef89b236f41e861a121a67b3e8fb0bec844d4f12aaf0a46')
check('genuine_consumed93',claim['effective_attempt_budget']==93 and claim['experiment_id']==NAME and failed['status']=='failed' and not (RR/'complete.json').exists())
source=claim['source'];check('all_source_joins',source=='d00d8dfb34acce77f965dfcc87c79f264d132a69' and all(x==source for x in (owner['source_commit'],launch['source_commit'],storage['source'])))
check('primary_failure',failed['reason']=='PlannedScoringStop: registered completed scalar comparison limit reached')
for name,h in failed['output_sha256'].items():check('terminal_output_'+name,hashlib.sha256(read(RR/'outputs'/name)).hexdigest()==h)
summary=load(RR/'outputs/pilot-summary.json');diagnostic=load(RR/'outputs/real-pilot-scoring-diagnostic.json');cell=load(RR/'outputs/cell-ledger.json');postmortem=load(RUN/'postmortem-cells.json')
check('registered_partial_stop',diagnostic['completed_scalar_pairs']==1024 and diagnostic['graph_completed_scalar_pairs']==1024 and diagnostic['planned_stop_reached'] is True and diagnostic['tail_observation']=={'acknowledged_tail_cells':1023,'durable_tail_cells':1023,'completed_batch_cells':0,'durability_poisoned':False})
check('all_seven_dispositions',len(summary['throughput']['graphs'])==7 and summary['throughput']['graphs'][0]['status']=='failed' and all(v['status']=='unavailable' and v['reason']=='not_attempted_after_failure' for v in summary['throughput']['graphs'][1:]) and all(v['completed_motif_cells'] is None and v['completed_nodes'] is None for v in summary['throughput']['graphs']))
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
log=read(RUN/'guard/child.log').decode();check('actual_trace_stop', 'PlannedScoringStop: registered completed scalar comparison limit reached' in log)
# No source execution: confirm frozen declared bytes only.
source_mismatch=[]
for p,h in claim['experiment']['source_files'].items():
 if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h:source_mismatch.append(p)
check('source_still_frozen',not source_mismatch)
pids={int(owner['monitor_pid']),int(owner['supervisor_pid']),int(child['workload_pid'])}|{int(p) for p in guard['cpu_thread_readback']}
proc={str(p):(Path('/proc')/str(p)).exists() for p in sorted(pids)};check('original_pids_absent',not any(proc.values()))
archive=load(RR/'outputs/archive-terminal.json');check('no_archive_commands',archive['status']=='failed' and archive['spent']['commands']==0)
check('Root_actual_terminal',terminal['session_id']==83120 and terminal['tool_chunk_id']=='b1503c' and terminal['actual_root_exit_code']==1 and terminal['original_root_io_closed']==closed)
check('original_owner_launch_join',owner['nonce']==launch['nonce'] and owner['supervisor_pid']==launch['supervisor_pid']==closed['supervisor_pid'])
check('actual_cgroup_absent',not Path(guard['cgroup']).exists())
check('no_full_science',not diagnostic['full_mcm_complete'] and not diagnostic['model_update_complete'] and diagnostic['representation_credit']==diagnostic['paper_financial_fits']==0)
checkpoint=load(RR/'artifacts/scoring-diagnostic/progress.json')
check('distinct_original_timings',diagnostic['matching_elapsed_seconds']!=checkpoint['matching_elapsed_seconds'])
result={'final_matching_elapsed_seconds':diagnostic['matching_elapsed_seconds'],'checkpoint_matching_elapsed_seconds':checkpoint['matching_elapsed_seconds'],'decision':'accepted-failed-outcome-public-selection-pending','identity':NAME,'source':source,'claim_sha256':failed['claim_sha256'],'effective_attempt_budget':93,'evidence':evidence,'checks':checks,'primary_reason':failed['reason'],'diagnostic_completed_pairs':1024,'acknowledged_tail_cells':1023,'planned_stop_reached':True,'graphs_failed':1,'graphs_unavailable':6,'training':None,'root_exit':1,'native_child_exit':1,'guard_elapsed_seconds':guard['elapsed_seconds'],'pid_observation':proc,'qualification':'Permanent FAILED/spent93 despite expected planned diagnostic stop.1024acknowledgements and1023tail are original diagnostic metadata, not independent full binary chain authentication. All7 dispositions/null completed values preserved. No complete MCM/model/financial fit. Phase timings overlap and are not disjoint. Public scope selection and returned recovery remain separate and pending; no new94 authority.'}
(H/'OUTCOME_REVIEW01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':result['decision'],'checks':len(checks),'sha256':hashlib.sha256((H/'OUTCOME_REVIEW01.json').read_bytes()).hexdigest()}))
