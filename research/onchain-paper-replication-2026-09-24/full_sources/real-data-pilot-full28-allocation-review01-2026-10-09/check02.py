from pathlib import Path
import json,hashlib,os,datetime
R=Path.cwd();D=Path(__file__).resolve().parent;F=D.parent;E=F/'real-data-pilot-full28-entry01-2026-10-09';P=F/'real-data-pilot-full27-entry01-2026-10-09';refs={}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):refs[str(p.relative_to(R))]=h(p);return json.loads(p.read_bytes())
a=load(E/'CUMULATIVE_ALLOCATION_PROPOSED99_01.json');e=load(E/'EXTENSION_PROPOSED99_01.json');prep=load(E/'ACCOUNTING_PREPARATION01.json');pa=load(P/'CUMULATIVE_ALLOCATION_PROPOSED98_01.json');pe=load(P/'EXTENSION_PROPOSED98_01.json');prior=load(F/'real-data-pilot-full27-allocation-review01-2026-10-09/EXTENSION98_REVIEW01.json')
assert prior['decision']=='accepted' and prior['extension_sha256']==h(P/'EXTENSION_PROPOSED98_01.json')
assert prep['prior_allocation']=={'path':str((P/'CUMULATIVE_ALLOCATION_PROPOSED98_01.json').relative_to(R)),'sha256':h(P/'CUMULATIVE_ALLOCATION_PROPOSED98_01.json')}
assert a['closed_claims']==e['claims'] and a['closed_claims'][:-1]==pa['closed_claims']==pe['claims'] and len(e['claims'])==50 and len({x['experiment'] for x in e['claims']})==50
new=e['claims'][-1];assert new==prep['new_terminal'] and new['terminal_status']=='failed' and new['experiment']=='eth-paper-real-data-end-to-end-resource-20261009-27'
claim=load(R/'research_runs'/new['experiment']/'claim.json');failed=load(R/'research_runs'/new['experiment']/'failed.json');assert h(R/'research_runs'/new['experiment']/'claim.json')==new['claim_sha256'] and h(R/'research_runs'/new['experiment']/'failed.json')==new['terminal_sha256'];assert failed['claim_sha256']==new['claim_sha256'] and failed['status']=='failed' and failed['experiment_id']==new['experiment'] and claim['effective_attempt_budget']==98
assert a['base_family']==e['base_family']==pa['base_family']==pe['base_family']==claim['family'] and a['base_family']['prior_attempts']==17
changed_a={k for k in a if a[k]!=pa[k]};assert changed_a=={'closed_claims','consumed_before','equation','identities','prior_adopted_cumulative_ceiling','prior_reviewed_reserved_ceiling','proposed_cumulative_ceiling','qualification','question'}
changed_e={k for k in e if e[k]!=pe[k]};assert changed_e=={'allocation','claims','consumed_before','cumulative_ceiling','initial_experiment','reason'}
assert e['allocation']=={'path':str((E/'CUMULATIVE_ALLOCATION_PROPOSED99_01.json').relative_to(R)),'sha256':h(E/'CUMULATIVE_ALLOCATION_PROPOSED99_01.json')}
assert a['consumed_before']==e['consumed_before']==17+50==67
assert sum(a['unchanged_pending_allocation'].values())==28 and len(a['preserved_reserved_preclaim_allowances'])==3 and sum(a['new_fixed_allocation'].values())==1 and 67+28+3+1==a['proposed_cumulative_ceiling']==e['cumulative_ceiling']==99
assert a['prior_adopted_cumulative_ceiling']==a['prior_reviewed_reserved_ceiling']==98
assert a['refunds']==a['category_transfers']==a['historical_claims_reopened']==a['new_financial_fits']==0 and a['maximum_unique_financial_fits_unchanged']==1420
outcome=load(F/'real-data-pilot-full27-outcome-review01-2026-10-09/OUTCOME_REVIEW01.json');acc=outcome['accounting'];assert (acc['closed_total'],acc['complete_total'],acc['failed_total'],acc['highest_claimed_allowance'])==(67,33,34,98);assert outcome['claim_sha256']==new['claim_sha256'] and outcome['failed_sha256']==new['terminal_sha256']
name='eth-paper-real-data-end-to-end-resource-20261009-28';assert a['identities']==[name] and e['initial_experiment']==name and prep['new_identity']==name
paths=[R/'research_runs'/name,R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/name]
for base in ['onchain_representations','onchain_compact_mcm']:
 root=R/'research_artifacts'/base
 if root.exists():
  for child in root.iterdir():
   if child.is_dir() and not child.is_symlink():paths.append(child/name)
assert all(not os.path.lexists(p) for p in paths)
assert 'unchanged' in a['question'] and 'limits retained' in a['qualification']
assert 'immutable closure-token correction' in a['question'] and 'inclusive genuine authority callback' in a['question']
checks={'closed_lists':'both exact49-row prefixes unchanged; one failed27 appended identically','changed_allocation_keys':sorted(changed_a),'changed_extension_keys':sorted(changed_e),'counts':{'historical':17,'actual':50,'closed':67,'complete':33,'failed':34,'pending':28,'reserved':3,'fixed_new':1,'proposed_ceiling':99,'highest_actual_claimed':98},'fresh_namespace_lstat_absence':{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'paths':[str(p.relative_to(R)) for p in paths],'all_absent':True,'qualification':'Scoped local name checks only. Future derived owner/transport namespaces need exact bound-entry review; no blanket filesystem exclusion.'}}
(D/'CHECK01.json').write_text(json.dumps(checks,indent=2)+'\n')
review={'schema_version':1,'decision':'accepted','extension_sha256':h(E/'EXTENSION_PROPOSED99_01.json'),'reviewer':'Independent full28 allocation changed-seam review','scope':'Same-family machine budget only.67 permanently spent=17 preserved historical+50 actual;33 complete34 failed;28 unchanged pending+3 closed preclaim reserves+1 fresh fixed28=99. Prior49 claims/status/hash rows unchanged in both lists. Actual27 permanently FAILED at originalclaim738ca092/terminal873bc460; no refund, transfer, prior reopening, financial fit or paper65 allowance. Exact source/input/science/limits/entry release and recovery/adoption remain separate.'}
(D/'EXTENSION99_REVIEW01.json').write_text(json.dumps(review,indent=2)+'\n')
result={'harness_correction':'CHECK01 used overly strict prose assertion unchanged in qualification; actual qualification says limits retained. All prior substantive checks passed. Original script/failure retained; CHECK02 checks actual wording.','decision':'accepted_allocation_delta_only','extension_review_sha256':h(D/'EXTENSION99_REVIEW01.json'),'evidence':refs,'checks':checks,'limits_of_review':['No proposal adoption, admission/claim or launch performed.','Unchanged family/pending/reserved/financial allowances are literal metadata equality; historical receipts reused through accepted98 review, not reread/reexecuted.','Question states original science/limits unchanged; these allocation documents do not contain complete operational/source/input policies, so exact joined equality is deferred to Root combined entry release.','New28 namespace absence is a point observation; no future exclusion or process claim.','Outcome status and permanent spending do not convert partial4096 durable scores into completed graph/training.']}
(D/'SOURCE_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'extension_review_sha256':h(D/'EXTENSION99_REVIEW01.json'),'source_review_sha256':h(D/'SOURCE_REVIEW01.json')}))
