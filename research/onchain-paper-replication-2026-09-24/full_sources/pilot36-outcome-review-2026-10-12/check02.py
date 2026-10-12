"""Read-only original outcome and finite policy-predicate authentication."""
import ast, hashlib, json, os, stat
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent; F=P.parent; R=F.parents[2]
ID='eth-paper-real-data-end-to-end-resource-20261011-36'
SOURCE='998d353d86d683e8a095ebffb4e539a5c849ca68'
RUN=R/'research_runs'/ID
NATIVE=R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID
ENTRY=F/'real-data-pilot-full36-entry-preparation01-2026-10-11'
FEATURE=R/'research_artifacts/onchain_representations/4c1d07a983d266df70164d623a20d61a71499c9fec9e9d6a64a1f7ba6b1583e6'/ID
PARENT=R/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/ID
pins={}
def raw(p):
    a=p.lstat(); assert stat.S_ISREG(a.st_mode) and not p.is_symlink()
    b=p.read_bytes(); z=p.lstat()
    assert (a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
    pins[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
    return b
def sha(p): return hashlib.sha256(raw(p)).hexdigest()
def load(p): return json.loads(raw(p))
claim=load(RUN/'claim.json'); failed=load(RUN/'failed.json')
assert failed['claim_sha256']==sha(RUN/'claim.json')
assert claim['source']==SOURCE and claim['effective_attempt_budget']==108
assert claim['experiment_id']==ID and failed['status']=='failed'
assert not (RUN/'complete.json').exists()
assert set(failed['output_sha256'])==set(p.name for p in (RUN/'outputs').iterdir())
for name,h in failed['output_sha256'].items(): assert sha(RUN/'outputs'/name)==h
assert sha(R/claim['registration'])==claim['registration_sha256']
source_mismatches=[]
for name,h in claim['experiment']['source_files'].items():
    if sha(R/name)!=h: source_mismatches.append(name)
assert not source_mismatches, source_mismatches
summary=load(RUN/'outputs/pilot-summary.json'); timing=load(RUN/'outputs/phase-timing.json')
cells=load(RUN/'outputs/cell-ledger.json'); terminal=load(RUN/'outputs/archive-terminal.json')
assert cells==[summary['cell']] and cells[0]['status']=='failed'
assert summary['training'] is None and summary['retained_target_count']==0
assert summary['original_motifs']==32 and summary['original_samples']==512
throughput=summary['throughput']; assert len(throughput['graphs'])==7
assert throughput['complete_graphs']==0 and throughput['failed_graphs']==1 and throughput['unavailable_graphs']==6
assert all(x['completed_motif_cells'] is None and x['completed_nodes'] is None for x in throughput['graphs'])
assert sum(x['expected_motif_cells'] for x in throughput['graphs'])==415968128
assert terminal['spent']=={'commands':0,'logical_bytes':0,'rounded_bytes':0}
assert timing['invalid_measurements']==0 and timing['numeric_counts']=={}
assert not any(k in timing['phases'] for k in ('matching','checkpoint','publication','offload'))
feature_failed=load(FEATURE/'failed.json'); feature_claim=load(FEATURE/'claim.json')
owner=load(FEATURE/'compact/owner.json')
intent=load(FEATURE/'compact/dictionary-import/intent.json')
imported=load(FEATURE/'compact/dictionary-import/import-complete.json')
assert imported['intent_sha256']==sha(FEATURE/'compact/dictionary-import/intent.json')
assert imported['owner']==intent['owner']
assert imported['current_matching_pairs']==0 and imported['historical_work_recomputed'] is False
assert len(imported['numeric']['ordered_motifs'])==32
assert feature_claim['descriptor']['configs']['dictionary']['sample_count']==512
assert feature_failed['reason']==failed['reason'] and feature_failed['events']==[]
assert feature_failed['workflow_identity'] is None
assert feature_claim['owner']['source_commit']==SOURCE
assert set(x.name for x in (FEATURE/'compact').iterdir())=={'owner.json','dictionary-import'}
assert not (FEATURE/'complete.json').exists()
closure=load(ENTRY/'ROOT_IO_CLOSED01.json'); storage=load(ENTRY/'FINAL_STORAGE01.json')
guard=load(NATIVE/'guard/final.json'); child=load(NATIVE/'guard/child_exit.json')
observer=load(NATIVE/'observer.json'); load(NATIVE/'guard/observer-death.json')
postmortem=load(NATIVE/'postmortem-cells.json'); load(NATIVE/'unsealed-journals.json')
parent=load(PARENT/'stdout.log'); sha(PARENT/'stderr.log')
assert parent['terminal_sha256']==sha(RUN/'failed.json')
for n,h in parent['evidence_sha256'].items(): assert sha(NATIVE/n)==h
assert parent['owner_sha256']==sha(NATIVE/'owner.json')
assert closure['actual_parent_exit_code']==child['exit_code']==guard['child_exit_code']==1
assert closure['supervisor_reaped'] and closure['outer_log_handles_closed'] and guard['cleanup_verified']
assert storage['supervisor_reaped'] and storage['actual_current_cgroup_absent'] and storage['original_monitor_process_absent']
assert storage['source']==SOURCE and storage['actual_current_unit_properties']['MainPID']=='0'
for name,rel in [('guard','guard/final.json'),('owner','owner.json'),('launch','launch.json')]:
    assert storage['original_metadata_sha256'][name]==sha(NATIVE/rel)
known_pids=[closure['supervisor_pid'],guard['monitor_pid'],child['workload_pid']]
known_pid_absence={str(p):not Path('/proc',str(p)).exists() for p in known_pids}
assert all(known_pid_absence.values())
assert not Path(guard['cgroup']).exists()
assert all(guard['memory_events'][k]==0 for k in ('max','oom','oom_kill','oom_group_kill'))
assert guard['optional_memory_telemetry']['unit']['swap_current_bytes']==0
# Compile only the actual standalone Boolean AST; no project imports or authority.
source_path=R/'tradingagents/research/onchain_replication/compact_mcm.py'
tree=ast.parse(raw(source_path))
predicate=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='compact MCM policy/cell/metadata allowance differs')
role=claim['inputs']['mcm_policy']; policy=load(R/role['path']); assert sha(R/role['path'])==role['sha256']
env={'policy':policy,'pairs':56584576,'owner':SimpleNamespace(required=owner['required_stages']),'io':SimpleNamespace(META_LIMIT=8192),'durability_selected':False,'batched_selected':True}
expression=compile(ast.Expression(predicate.args[0]),str(source_path),'eval')
red=eval(expression,env); assert red is False
legacy=dict(policy); del legacy['entry_qualification']
without=eval(expression,{**env,'policy':legacy}); assert without is True
assert failed['reason']=='ValueError: compact MCM policy/cell/metadata allowance differs'
prior=load(F/'pilot36-public-cumulative-review-2026-10-11/EXTENSION108_REVIEW01.json')
assert sha(F/'pilot36-public-cumulative-review-2026-10-11/EXTENSION108_REVIEW01.json')=='40b2cc61792e29f80ecbad86530b2963fb0d6ea197ad80b0b3e09325695a6db4'
actual=[]
for path in sorted((R/'research_runs').glob('*/claim.json')):
    # Metadata only; exclude unrelated programs and mechanism families.
    item=json.loads(path.read_bytes())
    if item['program_id']!=claim['program_id'] or item['family']['mechanism_id']!=claim['family']['mechanism_id']: continue
    sha(path); terminals=[path.parent/n for n in ('failed.json','complete.json') if (path.parent/n).exists()]
    assert len(terminals)==1
    end=load(terminals[0]); assert end['claim_sha256']==sha(path)
    actual.append({'experiment':item['experiment_id'],'status':end['status'],'effective_attempt_budget':item['effective_attempt_budget']})
counts={s:sum(x['status']==s for x in actual) for s in ('complete','failed')}
assert counts=={'complete':20,'failed':39}
assert max(x['effective_attempt_budget'] for x in actual)==108
out={'status':'ACCEPTED_FAILED_ORIGINAL36_CLOSURE_ONLY','reviewer':'Independent outcome reviewer /root/pilot_efficiency_integration_review','source':SOURCE,'source_bodies_authenticated':len(claim['experiment']['source_files']),'reason':failed['reason'],'entry_preparation_complete':False,'policy_predicate':{'source_line':predicate.lineno,'actual_policy_passes':red,'only_entry_qualification_removed_passes':without,'qualification':'Counterfactual metadata control only; no source or policy mutation.'},'dictionary_import':{'receipt_authenticated':True,'original_motifs':32,'original_samples':512,'current_matching_pairs':0,'historical_work_recomputed':False,'numeric_owner_stage_completed':imported['numeric']['owner_stage_completed'],'numeric_mcm_execution_admitted':imported['numeric']['mcm_execution_admitted']},'actual_current_family':actual,'accounting':{'current':counts,'accepted_original_historical':{'complete':13,'failed':4},'total':{'closed':76,'complete':33,'failed':43},'highest_effective_budget':108,'qualification':'17 historical original joins reused from exact accepted extension108 review; no allowance refund or transfer.'},'run_cell':cells,'original_postmortem_cells':postmortem,'throughput':throughput,'phase_timing':timing,'known_pid_absence':known_pid_absence,'process_closure':{'guard_cleanup_verified':True,'root_supervisor_reaped':True,'cgroup_absent':True,'known_processes_absent':True,'parent_exit':1,'source_freeze_release_supported':True,'qualification':'This attempt only; no global writer/process exclusion.'},'guard_elapsed_seconds':guard['elapsed_seconds'],'unit_last_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes'],'unit_memory_high_events':guard['memory_events']['high'],'final_storage':{k:storage['storage_observation'][k] for k in ('logical_file_bytes','allocated_bytes','entries')},'evidence':pins,'limitations':['No original data arrays, labels or numerical results opened.','No fresh source Git/object ancestry operation; original claim/source body pins and prior release provenance used.','No completed preparation qualification, verified MCM output, training update, financial fit or economic inference.','Partial graph counts and throughput remain null; absent MCM stage plus source-order proof supplies no-computation inference separately.','No external preservation/recovery of actual36 is established by this review.']}
(P/'OUTCOME_REVIEW01.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ('status','source_bodies_authenticated','policy_predicate','accounting','process_closure')},indent=2))
