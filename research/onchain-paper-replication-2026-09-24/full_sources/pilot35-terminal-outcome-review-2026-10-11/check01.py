"""One bounded public-metadata review; no process, Git, transport or array work."""
from pathlib import Path
import hashlib
import json

R = Path.cwd()
F = Path('research/onchain-paper-replication-2026-09-24/full_sources')
O = F/'pilot35-terminal-outcome-review-2026-10-11'
E = F/'real-data-pilot-full35-entry-preparation01-2026-10-11'
N = 'eth-paper-real-data-end-to-end-resource-20261011-35'
W = 'fc3ffe1ecb66f7f7ea20dd78b8a5e6e531c596c227344d3555fc72b257b4c5ab'
D = Path('research_runs')/N
G = Path('research_artifacts/onchain-paper-replication-2026-09-24/runs')/N
P = Path('research_artifacts/onchain_representations')/W/N
refs, checks = {}, []

def ref(p):
    p = Path(p)
    assert not p.is_symlink() and p.stat().st_size <= 4*1024**2, str(p)
    b = p.read_bytes()
    result = {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    refs[str(p)] = result
    return result

def read(p):
    ref(p)
    return json.loads(Path(p).read_bytes())

def ck(value, label):
    checks.append({'check':label,'pass':bool(value)})
    if not value:
        raise AssertionError(label)

def join(r):
    actual = ref(r['path'])
    ck(all(actual[k] == r[k] for k in ('sha256','bytes') if k in r), 'body join '+r['path'])

def write(name, value):
    (O/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

try:
    t = read(E/'ROOT_TERMINAL_OPERATION01.json')
    ck(refs[str(E/'ROOT_TERMINAL_OPERATION01.json')]['sha256'] == 'd30e5e42db78e1fdb53368253c18f5c967d04a1d7f35f2071879eb4b26d5fef6','Root supplied exact terminal receipt')
    for r in t['original_receipts'].values(): join(r)
    c, f = read(D/'claim.json'), read(D/'failed.json')
    ck(refs[str(D/'claim.json')]['sha256'] == f['claim_sha256'] == t['original_failure']['claim_sha256'],'actual claimed identity')
    ck(c['experiment_id'] == f['experiment_id'] == t['original_experiment'] == N and f['status'] == 'failed','original failed35 identity')
    ck(f['reason'] == t['original_failure']['reason'] == 'ValueError: import lease: stale interval cannot refresh','original reason')
    ck(not (D/'complete.json').exists() and c['effective_attempt_budget'] == 106,'closed failure and actual budget106')
    ck(c['bindings'] is None and c['bindings_sha256'] is None,'original top-level binding nulls retained')
    ck(ref(c['registration'])['sha256'] == c['registration_sha256'],'original frozen gate body')
    ck(c['experiment']['parent'] == 'eth-paper-real-data-end-to-end-resource-20261011-34','parent34 retained')
    ck(set(f['output_sha256']) == set(t['actual_output_joins']) and len(f['output_sha256']) == 8,'all eight outputs denominator')
    outputs = {}
    for name, sha in f['output_sha256'].items():
        r = ref(D/'outputs'/name)
        ck(r['sha256'] == sha == t['actual_output_joins'][name]['sha256'] and r['bytes'] == t['actual_output_joins'][name]['bytes'],'output '+name)
        if name != 'resource-population.json': outputs[name] = read(D/'outputs'/name)
    # The population output is authenticated as opaque bytes; labels are not decoded.
    s = outputs['pilot-summary.json']; q = s['throughput']; rows = q['graphs']
    ck((s['original_samples'],s['original_motifs'],s['full_graphs']) == (512,32,7),'unchanged sample motif graph scope')
    ck(len(rows) == 7 and [x['status'] for x in rows] == ['failed']+['unavailable']*6,'all seven target dispositions')
    ck(sum(x['expected_motif_cells'] for x in rows) == 415968128 and all(x['expected_motif_cells'] == 32*x['expected_nodes'] for x in rows),'complete expected cell denominator')
    ck(all(x['completed_motif_cells'] is None and x['completed_nodes'] is None for x in rows),'unknown individual completion values retained')
    ck(q['complete_graphs'] == q['verified_completed_motif_cells'] == q['verified_completed_nodes'] == s['retained_target_count'] == 0 and s['training'] is None,'no whole MCM or training credit')
    ck(q['failed_graphs'] == 1 and q['unavailable_graphs'] == 6 and not s['financial_fit_complete'] and not s['full_size_capacity'] and q['paper_financial_fits'] == 0,'failed resource outcome only')
    ck(outputs['cell-ledger.json'] == [s['cell']],'actual worker cell ledger')
    ck(outputs['resource-binding.json']['status'] == outputs['resource-journal.json']['status'] == 'failed','failed binding and journal stubs remain stubs')
    owner,start,wf = read(P/'owner.json'),read(P/'start.json'),read(P/'failed.json')
    di = read(P/'compact/dictionary-import/import-complete.json')
    ck(owner == start['owner'] == wf['owner'] and owner['workflow_identity'] == W,'genuine representation owner identity')
    ck(start['workflow_identity'] is None and wf['workflow_identity'] is None and wf['parent'] is None and wf['events'] == [],'workflow nulls and empty events preserved')
    ck(start['required_graphs'] == wf['required_graphs'] == [x['graph_hash'] for x in rows] and wf['status'] == 'failed','workflow graph roster and failed disposition')
    ck(di['kind'] == 'dictionary-import-complete' and di['historical_work_recomputed'] is False and di['current_matching_pairs'] == 0,'completed import without historical recomputation')
    ck(len(di['numeric']['ordered_motifs']) == 32 and di['numeric']['owner_stage_completed'] is False and di['numeric']['mcm_execution_admitted'] is False,'import receipt original finite scope')
    ck(ref(P/'compact/dictionary-import/intent.json')['sha256'] == di['intent_sha256'],'dictionary import intent')
    ck(ref(P/'compact/owner.json')['sha256'] == di['owner'],'compact owner body')
    compact_members = sorted(p.name for p in (P/'compact').iterdir())
    ck(compact_members == ['dictionary-import','owner.json'],'no representation MCM subtree')
    guard,child = read(G/'guard/final.json'),read(G/'guard/child_exit.json')
    io,storage = read(E/'ROOT_IO_CLOSED01.json'),read(E/'FINAL_STORAGE01.json')
    ck(c['source'] == c['design_source'] == owner['source_commit'] == guard['owner_identity']['source_commit'] == storage['source'] == di['execution']['current_source'] == 'dd0d8d4cda7bffa6e45629f00da5ce60412cbec1','original source joins, not current modified Main')
    ck(guard['child_exit_code'] == child['exit_code'] == io['actual_parent_exit_code'] == t['root_exec_terminal']['actual_exit_code'] == 1,'original child guard parent Root exits')
    ck(guard['phase'] == 'failed' and guard['cleanup_verified'] and not guard['elapsed_time_kill'],'guard failure and recorded cleanup')
    ck(io['supervisor_reaped'] and io['outer_log_handles_closed'] and storage['supervisor_reaped'] and storage['outer_log_handles_closed'],'reaped supervisor and closed handles')
    ck(storage['actual_current_cgroup_absent'] and storage['original_monitor_process_absent'] and t['original_cgroup_absent'],'recorded monitor and cgroup absence')
    ck(storage['actual_current_unit_properties'] == t['actual_unit_properties'] and t['actual_unit_properties']['MainPID'] == '0' and t['actual_unit_properties']['ControlGroup'] == '' and t['actual_unit_properties']['ActiveState'] == 'failed','recorded failed unit without MainPID/cgroup')
    ck(set(t['observed_pid_sample_absent']) == {2449406,2450350,2450878,2451329,2451332},'known sample only, no lifetime PID census')
    ck(child['terminal_memory_snapshot'] == guard['terminal_memory_snapshot'],'terminal memory snapshot agreement')
    for name,sha in storage['original_metadata_sha256'].items():
        p = G/('guard/final.json' if name == 'guard' else name+'.json')
        ck(ref(p)['sha256'] == sha,'final storage metadata '+name)
    obs = read(G/'observer.json'); post = read(G/'postmortem-cells.json')
    for name,sha in obs['evidence_sha256'].items(): ck(ref(G/name)['sha256'] == sha,'observer '+name)
    ck(obs['terminal_sha256'] == refs[str(D/'failed.json')]['sha256'] and obs['status'] == 'failed' and post[0]['status'] == 'unavailable','outer unavailable and worker failed remain distinct')
    trace = (G/'guard/child.log').read_text()
    ck('compact_mcm_batched.py", line 553' in trace and 'stale interval cannot refresh' in trace,'original third boundary traceback')
    budget_ref = c['experiment']['cumulative_budget_extension']['review']; join(budget_ref); budget = read(budget_ref['path'])
    ck(budget['decision'] == 'accepted' and '74spent' in budget['scope'] and '33complete41failed' in budget['scope'],'reuse accepted predecessor accounting74')
    prior = read(F/'pilot34-terminal-outcome-review01-2026-10-11/REVIEW01.json')
    ck(prior['decision'] == 'accepted' and prior['accounting']['closed'] == 74 and prior['accounting']['failed'] == 41,'accepted actual prior closure, no historical replay')
    ext_ref = c['experiment']['cumulative_budget_extension']['extension']; join(ext_ref)
    ck(budget['extension_sha256'] == ext_ref['sha256'],'genuine106 review to proposal join')
    recovery = read(E/'PREPARATION_RECOVERY_COMPLETE01.json')
    for key in ('actual_return_review','capture','fresh_recovery'):join(recovery[key])
    prior_return = read(recovery['actual_return_review']['path'])
    ck(prior_return['decision'] == 'ACCEPT_ACTUAL_FULL35INCREMENT30_DECLARED_RETURN' and prior_return['source'] == c['source'],'scoped accepted preparation30 predecessor')
    ref(E/'BINDING01.json');ref(E/'RELEASE_REVIEW01.json');ref(E/'launch-attempt01.json')
    roots=[D,G,Path('research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent')/N,P,Path('research_artifacts/archive-dispatch-ethpilot-20261011-35'),Path('research_artifacts/onchain_compact_mcm')/W/N]
    scopes=[{'path':str(p),'exists':p.exists(),'empty_directories_required':True} for p in roots]
    # Scope metadata only: never traverse archive-operation or numerical bodies.
    result={'decision':'accepted','scope':'Original pilot35 failed outcome and exact named public metadata joins; no fresh recovery or numerical validation.','checks':checks,'references':refs,'source':c['source'],'claim_sha256':f['claim_sha256'],'original_reason':f['reason'],'ended_at':f['ended_at'],'root_actual_terminal':t['root_exec_terminal'],'source_freeze_qualification':'Root reports held-source policy ending after closure; no separate SOURCE_FREEZE01 found, no universal writer exclusion inferred. Current engineering source is not original35 source.','accounting':{'closed':75,'complete':33,'failed':42,'active_in_reviewed_cohort':0,'highest_actually_adopted':106,'pending_unchanged':28,'preclaim_reserved_unchanged':3,'basis':'Accepted74 predecessor plus exactly this claimed failed35; no global rescan/refund/transfer.'},'dictionary':{'import_complete':True,'historical_work_recomputed':False,'owner_stage_completed':False,'current_matching_pairs':0},'targets':{'failed':1,'unavailable':6,'complete':0,'expected_cells':415968128,'retained_targets':0,'training':None},'guard_elapsed_seconds':guard['elapsed_seconds'],'known_absent_pid_sample':t['observed_pid_sample_absent'],'cleanup_basis':'Original guard, RootIO, FINAL_STORAGE and Root actual terminal observations only; no fresh process query.','incremental_raw_scopes':scopes,'additional_public_scope':[str(E),str(O)],'preservation_instructions':'Root capture exact original six named outcome scopes with empty directories and typed opaque regular bodies, plus new entry/closure observations and this review. Reuse preparation30 and older accepted scopes; private dispatch/connection/key/runtime bodies and original scientific stores excluded. Archive-operation contents not inspected by this review. Root must inventory/hash actual selected bytes; this is not an archive census or return acceptance.','external_outcome_recovery_verified':False,'unknowns':['Complete lifetime PID history unknown.','Partial uncommitted numerical work not inferred; original completion nulls remain.','No real MCM/training/financial success or whole capacity.','No universal cleanup, writer exclusion, raw-store/runtime/POSIX recovery or deletion authority.','Sourcefreeze is policy evidence, not an independently recorded filesystem snapshot.']}
    write('REVIEW01.json',result)
    print(json.dumps({'decision':result['decision'],'checks':len(checks),'references':len(refs),'scopes':scopes}))
finally:
    write('CHECKS01.json',checks)
