"""Prospective accounting metadata only; genuine validator, no claim/admission."""
from pathlib import Path
import collections,hashlib,json,sys
H=Path(__file__).resolve().parent;F=H.parent;R=H.parents[3];sys.path.insert(0,str(R))
from tradingagents.research.budget_extensions import effective_budget
D=F/'real-data-pilot-retry19-registration01-2026-10-08';O=F/'real-data-pilot-retry18-registration01-2026-10-08'
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def bound(v):
 p=R/v['path'];assert p.resolve(strict=True)==p and p.stat().st_size<1024**2
 b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==v['sha256'];return b
newref=ref(D/'EXTENSION_PROPOSED90_01.json');assert newref['sha256']=='ccb3514db30e7b74597ca117656ea3c9e6eb05dce87f2dd97302f594d0ed7798'
new=json.loads(bound(newref));allocation=json.loads(bound(new['allocation']));oldref=ref(O/'EXTENSION_PROPOSED89_01.json');old=json.loads(bound(oldref));oldallocation=json.loads(bound(old['allocation']))
oldreviewref=ref(F/'real-data-pilot-seventeenth-resource-failed-review01-2026-10-08/budget89-review01/EXTENSION89_REVIEW01.json');assert oldreviewref['sha256']=='f8a7d0d95fc9b3bbbbe8a8ae445fc2d38e912412e28d4fd9786dfef3ccb5aa38'
oldreview=json.loads(bound(oldreviewref));assert oldreview['decision']=='accepted' and oldreview['extension_sha256']==oldref['sha256']
assert new['claims']==old['claims']==allocation['closed_claims'] and len(new['claims'])==41
assert new['base_family']==old['base_family']==allocation['base_family'] and new['base_family']['attempt_budget']==51 and new['base_family']['prior_attempts']==17
retained=['unchanged_pending_allocation','maximum_unique_financial_fits_unchanged','prior_adopted_cumulative_ceiling','refunds','category_transfers','historical_claims_reopened','new_financial_fits']
assert all(allocation[k]==oldallocation[k] for k in retained)
reserves=allocation['preserved_reserved_preclaim_allowances'];assert reserves[:-1]==oldallocation['preserved_reserved_preclaim_allowances'] and len(reserves)==3
last=reserves[-1];assert last['identity']=='eth-paper-real-data-end-to-end-resource-20261008-18' and last['allowance_ceiling']==89 and last['research_claim'] is None
assert last['disposition']=='CLOSED_NATIVE_SETUP_REFUSAL_PRECLAIM_NEVER_REUSE_NO_REFUND'
terminal=json.loads(bound(last['terminal_root']));outcome=json.loads(bound(last['outcome_review']));recovery=json.loads(bound(last['recovery_review']))
assert terminal['disposition']==outcome['disposition']==last['disposition'] and terminal['actual_research_claim'] is None and terminal['reserved_allowance_ceiling']==89
assert last['recovery_review']['sha256']=='d571da318c68652309b79a554a1e7733a70100a0b95ff2c5eabef202eb101e16' and recovery['actual_external_recovery_accepted'] and recovery['decision']=='accepted'
assert not (R/'research_runs'/last['identity']).exists()
assert new['consumed_before']==allocation['consumed_before']==17+41==58
assert dict(collections.Counter(x['terminal_status'] for x in new['claims']))=={'complete':20,'failed':21}
assert sum(allocation['unchanged_pending_allocation'].values())==28 and sum(allocation['new_fixed_allocation'].values())==1
assert allocation['prior_adopted_cumulative_ceiling']==88 and allocation['prior_reviewed_reserved_ceiling']==89
assert new['cumulative_ceiling']==allocation['proposed_cumulative_ceiling']==58+28+3+1==90
assert allocation['identities']==[new['initial_experiment']]==['eth-paper-real-data-end-to-end-resource-20261008-19']
assert not (R/'research_runs'/new['initial_experiment']).exists()
review={'schema_version':1,'decision':'accepted','extension_sha256':newref['sha256'],'reviewer':'pilot19 independent cumulative90 reviewer','scope':'Exact proposed90 accounting only: all41 current typed claim rows unchanged from accepted89 plus17 carried =58closed33COMPLETE25FAILED;28 unchanged pending+three permanently closed preclaim reserves03/08/18+ONEunused19=90. Base51/prior17,1420-fit ceiling and all old claims remain; no refund, transfer, resampling, cap ladder or financial credit. Actual18 terminal/outcome/external recovery joins accepted. Import-placement source correction and exact committed source/metadata/entry review remain required. This review does not adopt90, admit or launch19, validate causal RAM attribution, or prove startup/whole capacity.'}
review_raw=(json.dumps(review,indent=2,sort_keys=True)+'\n').encode();review_ref={'path':str((H/'EXTENSION90_REVIEW01.json').relative_to(R)),'sha256':hashlib.sha256(review_raw).hexdigest()}
def read_bound(v):return review_raw if v==review_ref else bound(v)
relevant=[json.loads((R/'research_runs'/x['experiment']/'claim.json').read_bytes()) for x in new['claims']]
result=effective_budget(R,new['program_id'],new['initial_experiment'],{'cumulative_budget_extension':{'extension':newref,'review':review_ref}},new['base_family'],relevant,read_bound);assert result==90
machine={'schema_version':1,'decision':'accepted-proposed-budget-only','extension':newref,'allocation':new['allocation'],'review':review_ref,'effective_budget_result':result,'genuine_validator':ref(R/'tradingagents/research/budget_extensions.py'),'prior_extension':oldref,'prior_review':oldreviewref,'actual18_terminal':last['terminal_root'],'actual18_outcome_review':last['outcome_review'],'actual18_recovery_review':last['recovery_review'],'unchanged_prior_snapshot_count':41,'actual_snapshot_count':41,'typed_snapshot_status_counts':{'complete':20,'failed':21},'carried_prior_claims':17,'carried_prior_status_counts_reused':{'complete':13,'failed':4},'cumulative_status_counts':{'complete':33,'failed':25},'consumed_before':58,'pending':28,'closed_preclaim_reserves':3,'unused_fixed_allocation':1,'prior_adopted_ceiling':88,'prior_reviewed_reserved_ceiling':89,'future_namespace_absent':True,'unchanged_allocation_fields':retained,'claim_or_admission_executed':False,'qualification':'Unmodified effective_budget called once with exact in-memory review and41 named claim metadata; validator authenticates current claim/terminal bytes. Unchanged17 carry reused from accepted history. Appended18 is a closed reserved native setup identity, not an invented42ndcurrent or59thcumulative claim. No scientific bodies/imports, budget adoption or release. Import measurement statements in proposal were not independently retested by this accounting check.'}
for name,body in [('EXTENSION90_REVIEW01.json',review_raw),('BUDGET90_MACHINE_REVIEW01.json',(json.dumps(machine,indent=2,sort_keys=True)+'\n').encode())]:
 with (H/name).open('xb') as f:f.write(body)
print(json.dumps({'effective_budget':result,'review':ref(H/'EXTENSION90_REVIEW01.json'),'machine':ref(H/'BUDGET90_MACHINE_REVIEW01.json')}))
