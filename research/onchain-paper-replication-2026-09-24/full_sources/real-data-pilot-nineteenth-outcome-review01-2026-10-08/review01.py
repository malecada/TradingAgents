"""Bounded public pilot19 outcome joins and opaque incremental byte selection."""
from pathlib import Path
import datetime, hashlib, json, stat, subprocess
H=Path(__file__).resolve().parent;F=H.parent;R=H.parents[3]
D=F/'real-data-pilot-final19-2026-10-08'
N='eth-paper-real-data-end-to-end-resource-20261008-19'
S='123e259a998a4aac4817b661434b1ef16c94c999'
W='f6ed2b5697184fe4c2d89810035f6ac69f5645e1f8e0cd05a6f7b18646f0c664'
G='0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba'
PFX=R/'research_artifacts/onchain-paper-replication-2026-09-24'
L=R/'research_runs'/N;B=PFX/'runs'/N;P=PFX/'pilot-parent'/N
J=R/'research_artifacts/onchain_representations'/W/N
O=R/'research_artifacts/onchain_compact_mcm'/W/N
A=R/'research_artifacts/archive-dispatch-ethpilot-20261008-19'
roots=[L,B,P,J,O,A];cache={};evidence={}
def sig(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def raw(p):
    p=Path(p);p=p if p.is_absolute() else R/p
    assert any(p.is_relative_to(q) for q in roots+[D]) or p.parent==R/'tradingagents/research/onchain_replication'
    if p not in cache:
        s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4194304
        cache[p]=p.read_bytes();assert sig(s)==sig(p.lstat())
    evidence[str(p.relative_to(R))]=hashlib.sha256(cache[p]).hexdigest();return cache[p]
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):return json.loads(raw(p))
def write(name,v):
    with (H/name).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
t=read(D/'ROOT_TERMINAL01.json');failed=read(L/'failed.json');claim=read(L/'claim.json')
assert t['source']==claim['source']==S and claim['experiment_id']==N and claim['effective_attempt_budget']==90
assert t['disposition']=='PERMANENT_FAILED_SPENT90_NEVER_REUSE'
for p,h in t['raw_sha256'].items():assert sha(p)==h
assert failed['claim_sha256']==sha(L/'claim.json') and failed['status']=='failed'
reason='CleanupFailure: score storage cleanup unresolved; worker must stop'
assert failed['reason']==t['actual_failed_reason']==reason
for p,h in failed['output_sha256'].items():assert sha(L/'outputs'/p)==h
summary=read(L/'outputs/pilot-summary.json');cells=read(L/'outputs/cell-ledger.json')
assert len(cells)==1 and cells[0]==summary['cell'] and cells[0]['status']=='failed' and cells[0]['reason']==reason
assert summary['full_graphs']==7 and summary['original_motifs']==32 and summary['original_samples']==512
assert summary['training'] is None and not summary['financial_fit_complete'] and not summary['full_size_capacity'] and summary['retained_target_count']==0
th=summary['throughput'];graphs=th['graphs'];assert len(graphs)==th['graph_denominator']==7
assert [x['status'] for x in graphs]==['failed']+['unavailable']*6
assert graphs[0]['graph_hash']==G and graphs[0]['reason']==reason
assert all(x['reason']=='not_attempted_after_failure' for x in graphs[1:])
assert all(x['completed_nodes'] is None and x['completed_motif_cells'] is None and x['expected_motif_cells']==x['expected_nodes']*32 for x in graphs)
assert th['complete_graphs']==th['verified_completed_nodes']==th['verified_completed_motif_cells']==0
assert th['failed_graphs']==1 and th['unavailable_graphs']==6 and th['one_update_phase_seconds'] is None
assert read(J/'failed.json')['required_graphs']==[x['graph_hash'] for x in graphs]
for name in ['resource-journal.json','resource-binding.json']:
    q=read(L/'outputs'/name);assert q['status']=='failed' and q['reason']==reason and q['resource_only']
log=raw(B/'guard/child.log').decode();assert 'ValueError: neighborhood capacity exceeded, no truncation' in log
assert 'score_tail.py", line 117, in durability_barrier' in log and 'import owner/prepared is closed/poisoned/incomplete' in log
assert 'ExceptionGroup: body/cleanup failures (2 sub-exceptions)' in log and log.rstrip().endswith(reason)
progress=[json.loads(s) for s in log.splitlines() if s.startswith('{') and 'real_pilot_partial_mcm_progress' in s]
partial=summary['partial_mcm_progress'];last=partial['last_observation']
assert len(progress)==partial['records']==19 and progress[-1]==last==t['last_partial_mcm_observation']
assert [x['sequence'] for x in progress]==list(range(19))
assert last['source']==S and last['claim_sha256']==sha(L/'claim.json') and last['graph_hash']==G
assert [last[k] for k in ['started_matching_pairs','acknowledged_computed_matching_pairs','acknowledged_tail_cells','durable_tail_cells']]==[736,735,735,734]
assert last['durable_score_batches']==last['durable_score_batch_cells']==0 and not last['full_mcm_completion_verified_here'] and not last['joint_update_verified_here']
stage=J/'compact'/('mcm-'+G);matching=read(stage/'matching/failed.json');ms=read(stage/'matching/start.json')
tail=stage/'stream/tails/tail-000000000000';ts=read(tail/'start.json')
assert matching['events']==1472 and matching['archived_chunks']==0 and matching['status']=='failed'
assert (stage/'matching/events-000000000000.bin').stat().st_size==matching['events']*ms['record_bytes']==247296
assert (tail/'records.bin').stat().st_size==736*ts['record_bytes']==58880
imp=read(J/'compact/dictionary-import/import-complete.json')
assert imp['kind']=='dictionary-import-complete' and imp['historical_work_recomputed'] is False and imp['current_matching_pairs']==0
assert len(imp['numeric']['ordered_motifs'])==32 and imp['numeric']['numeric_bytes']==11136
assert imp['numeric']['owner_stage_completed'] is False and imp['numeric']['mcm_execution_admitted'] is False and imp['execution']['mcm_execution_admitted'] is False
assert imp['execution']['current_source']==S and imp['intent_sha256']==sha(J/'compact/dictionary-import/intent.json')
absent=[L/'complete.json',PFX/'sources'/N,J/'complete.json',stage/'complete.json',stage/'matching/complete.json',stage/'stream/complete.json',tail/'complete.json',O/('mcm-'+G)/'complete.json']
assert all(not p.exists() and not p.is_symlink() for p in absent)
assert sorted(p.name for p in (stage/'stream/batches').iterdir())==['start.json']
arc=read(L/'outputs/archive-terminal.json');assert arc==read(A/'terminal.json') and arc['status']=='failed'
assert arc['intent_sha256']==sha(A/'intent.json') and arc['spent']['commands']==0 and arc['spent']['rounded_bytes']==0 and not arc['wire_bytes_measured']
guard=read(B/'guard/final.json');child=read(B/'guard/child_exit.json');owner=read(B/'owner.json');launch=read(B/'launch.json');obs=read(B/'observer.json')
assert raw(B/'guard/final.json')==raw(B/'guard/live.json')
assert guard['child_exit_code']==child['exit_code']==t['actual_native_child_exit']==1 and child['workload_pid']==297836
assert guard['cleanup_verified'] and guard['phase']=='failed' and not guard['retry']
assert guard['memory_events']==child['terminal_memory_snapshot']['memory_events'] and all(guard['memory_events'][k]==0 for k in ['max','oom','oom_kill','oom_group_kill'])
assert guard['owner_identity']==owner and owner['source_commit']==launch['source_commit']==S and owner['nonce']==launch['nonce']
assert obs['owner_sha256']==sha(B/'owner.json') and obs['terminal_sha256']==sha(L/'failed.json')
for p,h in obs['evidence_sha256'].items():assert sha(B/p)==h
assert obs['cell_ledger_sha256']==sha(B/'postmortem-cells.json') and read(B/'postmortem-cells.json')[0]['status']=='unavailable'
assert read(P/'stdout.log')==obs and raw(P/'stderr.log')==b''
io=read(D/'ROOT_IO_CLOSED01.json');storage=read(D/'FINAL_STORAGE01.json')
assert io['actual_parent_exit_code']==t['actual_root_exit_code']==1 and io['supervisor_pid']==owner['supervisor_pid']==297174 and io['supervisor_reaped'] and io['outer_log_handles_closed']
for k,p in [('guard',B/'guard/final.json'),('owner',B/'owner.json'),('launch',B/'launch.json')]:assert storage['original_metadata_sha256'][k]==sha(p)
pids=[297174,297513,297831,297836];assert all(not Path('/proc',str(pid)).exists() for pid in pids)
assert not Path(guard['cgroup']).exists()
unit=dict(s.split('=',1) for s in subprocess.check_output(['systemctl','--user','show',guard['unit'],'--property=ControlGroup,ActiveState,SubState,ExecMainStatus,Result,MainPID'],text=True).splitlines() if '=' in s)
assert unit==t['actual_unit_properties']==storage['actual_current_unit_properties'] and unit['MainPID']=='0' and unit['ControlGroup']=='' and unit['ExecMainStatus']=='1'
source_names=['array_neighborhoods.py','archive_owner_writer.py','compact_mcm.py','score_tail.py','imported_authority_lease.py','owned_io.py','job.py']
for name in source_names:
    p=R/'tradingagents/research/onchain_replication'/name;assert sha(p)==claim['experiment']['source_files'][str(p.relative_to(R))]
assert "raise ValueError('neighborhood capacity exceeded, no truncation')" in raw(R/'tradingagents/research/onchain_replication/array_neighborhoods.py').decode().splitlines()[87]
assert 'finally:ledger.owner.poisoned = True' in raw(R/'tradingagents/research/onchain_replication/archive_owner_writer.py').decode()
# Exact public owned increment: opaque hashes only for binary scientific payloads.
names=['ENTRY_GIT_REFUSAL01.json','REMOTE_CONFIRMATION01.json','REMOTE_CONFIRMATION02.json','launch-attempt01.json','LIVE_LAUNCH01.json','LIVE_OBSERVATION02.json','REPRESENTATION_OBSERVATION01.json','MCM_PROGRESS_OBSERVATION01.json','MCM_PROGRESS_STDOUT_SNAPSHOT01.log','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ROOT_TERMINAL01.json']
dynamic=[D/n for n in names];files=[];dirs=[]
for p in sorted(set(dynamic+[q for root in roots for q in [root,*root.rglob('*')]])):
    s=p.lstat();assert p.resolve(strict=True)==p
    rec={'path':str(p.relative_to(R)),'mode':stat.S_IMODE(s.st_mode)}
    if stat.S_ISDIR(s.st_mode):dirs.append(rec|{'kind':'directory'})
    else:
        assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
        files.append(rec|{'kind':'regular','bytes':s.st_size,'sha256':sha(p),'nlink':s.st_nlink,'stat_identity':sig(s)})
selection={'schema_version':1,'decision':'accepted','experiment':N,'source':S,'scope':'Complete six actual public pilot19 owned roots and twelve new dynamic entry records','files':files,'directories':dirs,'regular_count':len(files),'directory_count':len(dirs),'original_regular_bytes':sum(x['bytes'] for x in files),'dynamic_entry_records':[str(p.relative_to(R)) for p in dynamic],'absent_namespaces':[str((PFX/'sources'/N).relative_to(R))],'exclusions':['Unchanged historical stores, input capsules, source, runtime, gates, templates and earlier review/increment copies','Private transport bodies and credential files','Shared parent directories outside actual owned roots'],'qualification':'Names, regular bytes, modes and empty directories selected; new checkpoint arrays/events/tails hashed opaquely without decoding. No scientific validity, durability, remote availability, extraction or deletion authority.'}
write('INCREMENT_SELECTION01.json',selection)
result={'schema_version':1,'decision':'accepted-failed-outcome-and-increment-selection','experiment':N,'source':S,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_failed_reason':reason,'primary_trace_error':'ValueError: neighborhood capacity exceeded, no truncation','secondary_trace_error':'import lease: import owner/prepared is closed/poisoned/incomplete during score-tail durability barrier','disposition':'PERMANENT_FAILED_SPENT90_NEVER_REUSE','accounting_delta':{'new_failed_claims':1,'closed':59,'complete':33,'failed':26,'highest_actual_claim_budget':90,'closed_preclaim_reservations':3,'pending':28,'qualification':'Prior accepted budget90 allocation reused; no full historical rescan or new allowance.'},'graph_dispositions':graphs,'last_partial_observation':last,'physical_partial_evidence':{'matching_events_metadata':1472,'matching_event_bytes':247296,'tail_bytes':58880,'tail_record_sized_slots':736,'final_completed_matching_pairs':None,'final_durable_tail_cells':None,'qualification':'File lengths and failed metadata; no decoding or durable/full-completion inference.'},'native':{'elapsed_seconds':guard['elapsed_seconds'],'guard_child_exit':1,'separate_child_exit':1,'root_exit':1,'sample_peak_bytes':guard['peak_sampled_memory_current_bytes'],'last_kernel_peak_bytes':child['terminal_memory_snapshot']['optional_memory_telemetry']['unit']['kernel_peak_bytes'],'memory_events':guard['memory_events'],'pids_absent':pids,'unit_properties':unit,'cgroup_absent':True},'findings':[{'severity':'P2-existing','file':'tradingagents/research/onchain_replication/job.py','line':544,'impact':'Observer postmortem labels the registered cell unavailable despite the original failed.json-authenticated FAILED cell ledger. Preserve both; use original ledger for failed disposition. No accounting refund.','action':'Any later engineering correction should recover authenticated original cell-ledger rows before fallback; no original rewrite.'}],'not_tested':['Array values, matching semantic replay, exact failing center or neighborhood size, labels, financial outputs','Completed MCM/update, capacity, isolated matcher speed, restart/durability or external byte recovery','Historical accounting rescans and unchanged admission matrices'],'evidence':evidence,'selection':{'path':str((H/'INCREMENT_SELECTION01.json').relative_to(R)),'sha256':hashlib.sha256((H/'INCREMENT_SELECTION01.json').read_bytes()).hexdigest()},'qualification':'Original terminal and outputs joined; last sampled progress is not final count. No retry, reuse, refund, new registration or release.'}
write('OUTCOME_REVIEW01.json',result)
print(json.dumps({'decision':result['decision'],'files':len(files),'directories':len(dirs),'bytes':selection['original_regular_bytes'],'selection_sha256':result['selection']['sha256'],'outcome_sha256':hashlib.sha256((H/'OUTCOME_REVIEW01.json').read_bytes()).hexdigest()},sort_keys=True))
