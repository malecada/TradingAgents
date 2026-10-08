"""Genuine budget validator, named metadata only; no registration/admission writes."""
from pathlib import Path
import collections,hashlib,json,sys
H=Path(__file__).resolve().parent;R=H.parents[4];F=H.parent.parent
sys.path.insert(0,str(R))
from tradingagents.research.budget_extensions import effective_budget
D=F/'real-data-pilot-retry18-registration01-2026-10-08'
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def bound(v):
    p=R/v['path'];b=p.read_bytes();assert not p.is_symlink() and hashlib.sha256(b).hexdigest()==v['sha256'];return b
newref=ref(D/'EXTENSION_PROPOSED89_01.json');assert newref['sha256']=='9a4d06a017c272652f4721f535ba911b2d1a04dea87d959897b5c5e76149850e'
new=json.loads(bound(newref));allocation=json.loads(bound(new['allocation']))
claim=json.loads((R/'research_runs/eth-paper-real-data-end-to-end-resource-20261008-17/claim.json').read_bytes())
oldref=claim['experiment']['cumulative_budget_extension'];old=json.loads(bound(oldref['extension']));oldreview=json.loads(bound(oldref['review']));oldallocation=json.loads(bound(old['allocation']))
assert oldreview['decision']=='accepted' and oldreview['extension_sha256']==oldref['extension']['sha256']
assert oldref['review']['sha256']=='438ed590a36a25360a99c194ba6e199fef5c420ff3217b59c180939087143c2f'
assert new['claims'][:-1]==old['claims'] and len(old['claims'])==40 and len(new['claims'])==41
assert new['claims']==allocation['closed_claims']
assert new['base_family']==old['base_family']==allocation['base_family']==claim['family']
assert new['base_family']['attempt_budget']==51 and new['base_family']['prior_attempts']==17
retained=['unchanged_pending_allocation','preserved_reserved_preclaim_allowances','maximum_unique_financial_fits_unchanged','prior_reviewed_reserved_ceiling','refunds','category_transfers','historical_claims_reopened','new_financial_fits']
assert all(allocation[k]==oldallocation[k] for k in retained)
last=new['claims'][-1];assert last['experiment']==claim['experiment_id'] and last['terminal_status']=='failed' and claim['effective_attempt_budget']==88
assert ref(R/'research_runs'/claim['experiment_id']/'claim.json')['sha256']==last['claim_sha256']
assert ref(R/'research_runs'/claim['experiment_id']/'failed.json')['sha256']==last['terminal_sha256']
assert new['consumed_before']==allocation['consumed_before']==17+41==58
assert dict(collections.Counter(x['terminal_status'] for x in new['claims']))=={'complete':20,'failed':21}
assert sum(allocation['unchanged_pending_allocation'].values())==28 and len(allocation['preserved_reserved_preclaim_allowances'])==2
assert sum(allocation['new_fixed_allocation'].values())==1 and allocation['prior_adopted_cumulative_ceiling']==88
assert new['cumulative_ceiling']==allocation['proposed_cumulative_ceiling']==58+28+2+1==89
assert allocation['identities']==[new['initial_experiment']]==['eth-paper-real-data-end-to-end-resource-20261008-18']
assert not (R/'research_runs'/new['initial_experiment']).exists()
source_review=ref(H.parent/'live-guard-review01/SOURCE_REVIEW01.json');assert source_review['sha256']=='e3a272f5fb0143b9b0d01f8202b1e00c50e9dd58f3cac9736397670757d27f7e'
recovery_review=ref(H.parent/'returned-git-recovery01/RECOVERY_REVIEW01.json');assert recovery_review['sha256']=='29cf984e620ea3161b498695c7c0ffd47e6329ead076580a6265b93e996be91d'
review={'schema_version':1,'decision':'accepted','extension_sha256':newref['sha256'],'reviewer':'pilot17 independent cumulative89 reviewer','scope':'Exact same-family proposed89 only:40 unchanged typed closed rows plus actual failed17/spent88=41 current claims, plus17 carried prior=58;28 unchanged pending+2 permanently closed preclaim reserves+1 fixed unused18=89. Familybase51/prior17 and1420-fit ceiling retained; no refund, transfer, cap ladder, resampling or financial credit. Changed-source and actual17 recovery accepted separately. This review does not adopt89, admit or launch18. Exact committed metadata/source/runtime and independent entry/final release remain required; full lease activation timing remains unmeasured.'}
review_raw=(json.dumps(review,indent=2,sort_keys=True)+'\n').encode();review_ref={'path':str((H/'EXTENSION89_REVIEW01.json').relative_to(R)),'sha256':hashlib.sha256(review_raw).hexdigest()}
def read_bound(v):return review_raw if v==review_ref else bound(v)
relevant=[json.loads((R/'research_runs'/x['experiment']/'claim.json').read_bytes()) for x in new['claims']]
result=effective_budget(R,new['program_id'],new['initial_experiment'],{'cumulative_budget_extension':{'extension':newref,'review':review_ref}},new['base_family'],relevant,read_bound)
assert result==89
machine={'schema_version':1,'decision':'accepted-proposed-budget-only','extension':newref,'allocation':new['allocation'],'review':review_ref,'effective_budget_result':result,'genuine_validator':ref(R/'tradingagents/research/budget_extensions.py'),'prior_extension':oldref['extension'],'prior_review':oldref['review'],'changed_source_review':source_review,'actual17_recovery_review':recovery_review,'unchanged_prior_snapshot_count':40,'actual_snapshot_count':41,'typed_snapshot_status_counts':{'complete':20,'failed':21},'carried_prior_claims':17,'carried_prior_status_counts_reused':{'complete':13,'failed':4},'cumulative_status_counts':{'complete':33,'failed':25},'consumed_before':58,'pending':28,'closed_preclaim_reserves':2,'unused_fixed_allocation':1,'prior_adopted_ceiling':88,'future_namespace_absent':True,'unchanged_allocation_fields':retained,'claim_or_admission_executed':False,'qualification':'Unmodified effective_budget called with pinned proposal and exact in-memory review;41 named current claim/terminal pairs independently read and checked by the genuine validator. Prior17 carry and its13COMPLETE/4FAILED attribution reused from accepted history, not freshly recounted. No historical scientific stores or numerical imports. Proposed18 resources/method statements do not replace review of its future actual metadata.'}
assert not (H/'EXTENSION89_REVIEW01.json').exists()
(H/'EXTENSION89_REVIEW01.json').write_bytes(review_raw)
(H/'BUDGET89_MACHINE_REVIEW01.json').write_text(json.dumps(machine,indent=2,sort_keys=True)+'\n')
print(json.dumps({'effective_budget':result,'review':ref(H/'EXTENSION89_REVIEW01.json'),'machine':ref(H/'BUDGET89_MACHINE_REVIEW01.json')}))
