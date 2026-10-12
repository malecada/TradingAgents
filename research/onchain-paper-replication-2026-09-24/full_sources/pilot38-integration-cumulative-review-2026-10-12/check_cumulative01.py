"""Bounded proposed110 accounting review; no admission, claim or mutation."""
import hashlib,json,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parent; F=P.parent; R=F.parents[2]
C=F/'real-data-pilot-full38-cumulative-preparation01-2026-10-12'
OLD=F/'real-data-pilot-full36-cumulative-preparation01-2026-10-11'
pins={}
def raw(p):
 b=p.read_bytes();pins[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def load(p):return json.loads(raw(p))
def ref(p):
 raw(p);return {'path':str(p.relative_to(R)),'sha256':pins[str(p.relative_to(R))]['sha256']}
e=load(C/'EXTENSION_PROPOSED110_01.json');a=load(C/'CUMULATIVE_ALLOCATION_PROPOSED110_01.json')
oe=load(OLD/'EXTENSION_PROPOSED108_01.json');oa=load(OLD/'CUMULATIVE_ALLOCATION_PROPOSED108_01.json')
assert ref(OLD/'EXTENSION_PROPOSED108_01.json')['sha256']=='2713b819522f8c2c42c4ebc60d85eb06c7242eac0378ea59775b3dc85aa5a2dc'
assert ref(OLD/'CUMULATIVE_ALLOCATION_PROPOSED108_01.json')['sha256']=='3d2596bf40f4844c05295fff85b1e613f2d5210725a55887279f0c61983ded66'
outcome=load(F/'pilot36-outcome-review-2026-10-12/OUTCOME_REVIEW01.json')
assert ref(F/'pilot36-outcome-review-2026-10-12/OUTCOME_REVIEW01.json')['sha256']=='d1fae63a7248b3f3fb1fbabe1c2fe4f9ec63dd9c57bb57b58a718b164606fb19'
assert e['claims'][:-1]==oe['claims'] and a['closed_claims']==e['claims'] and len(e['claims'])==59
assert e['base_family']==oe['base_family']==a['base_family']
assert e['allocation']==ref(C/'CUMULATIVE_ALLOCATION_PROPOSED110_01.json')
last=e['claims'][-1]; assert last['experiment']=='eth-paper-real-data-end-to-end-resource-20261011-36' and last['terminal_status']=='failed'
for field,name in [('claim_sha256','claim.json'),('terminal_sha256','failed.json')]:
 p=R/'research_runs'/last['experiment']/name
 assert ref(p)['sha256']==last[field]==outcome['evidence'][str(p.relative_to(R))]['sha256']
changed={'status','closed_claims','consumed_before','prior_adopted_cumulative_ceiling','prior_reviewed_reserved_ceiling','proposed_cumulative_ceiling','identities','new_fixed_allocation','equation','question','qualification','preserved_unused37'}
assert set(a)==set(oa)|{'preserved_unused37'}
assert all(a[k]==oa[k] for k in oa if k not in changed)
assert a['unchanged_pending_allocation']=={'financial_fit_batches':15,'missing_body_batches':12,'remaining_graph_matching_mcm_resource':1}
assert len(a['preserved_reserved_preclaim_allowances'])==3
assert a['preserved_unused37']=={'identity':'eth-paper-real-data-end-to-end-resource-20261011-37','allowance':1,'status':'reserved_unavailable_dependency36_qualification_failed','claim':False}
names=['eth-paper-real-data-end-to-end-resource-20261012-38','eth-paper-real-data-end-to-end-resource-20261012-39']
assert a['identities']==names and e['initial_experiment']==names[0]
assert a['new_fixed_allocation']=={'first_graph_entry_preparation_qualification_claims':1,'full_seven_graph_joint_update_resource_pilot_claims':1}
assert e['consumed_before']==a['consumed_before']==76
assert e['cumulative_ceiling']==a['proposed_cumulative_ceiling']==76+28+3+1+2==110
assert a['prior_adopted_cumulative_ceiling']==a['prior_reviewed_reserved_ceiling']==108
assert a['new_financial_fits']==a['refunds']==a['category_transfers']==a['historical_claims_reopened']==0
assert a['maximum_unique_financial_fits_unchanged']==1420
assert all(not os.path.lexists(R/'research_runs'/n) for n in names+[a['preserved_unused37']['identity']])
assert outcome['accounting']['total']=={'closed':76,'complete':33,'failed':43}
relevant=[]
for item in e['claims']:
 p=R/'research_runs'/item['experiment']/'claim.json';c=load(p)
 assert c['family']==e['base_family'] and c['program_id']==e['program_id']
 assert ref(p)['sha256']==item['claim_sha256']==outcome['evidence'][str(p.relative_to(R))]['sha256']
 relevant.append(c)
review={'schema_version':1,'decision':'accepted','extension_sha256':ref(C/'EXTENSION_PROPOSED110_01.json')['sha256'],'reviewer':'Independent pilot38 integration and cumulative reviewer /root/pilot_efficiency_integration_review','scope':'Exact proposed110 metadata only. Preserve original108 allocations:76spent (59actual20complete39failed plus17historical13complete4failed, cumulative33complete43failed),28unchangedpending,3closedpreclaimreserved,1unused37reserved with failed36qualification dependency; add only fixed fresh38preparation and39seven-wholegraph joint-update resource claims. First adoption38 only; no refund, transfer, reopening, financial-fit allowance, resampling or physical cap increase. Original36 failure is immutable. Actual source/policy/runtime/capacity, accepted and recovered38 prerequisite for39, complete external preservation and final native release remain separately required. No adoption, claim or execution performed.'}
review_raw=(json.dumps(review,indent=2,sort_keys=True)+'\n').encode()
review_ref={'path':str((P/'EXTENSION110_REVIEW01.json').relative_to(R)),'sha256':hashlib.sha256(review_raw).hexdigest()}
def bound(r):
 if r==review_ref:return review_raw
 b=raw(R/r['path']);assert hashlib.sha256(b).hexdigest()==r['sha256'];return b
helper=R/'tradingagents/research/budget_extensions.py';raw(helper)
effective=runpy.run_path(str(helper))['effective_budget']
experiment={'cumulative_budget_extension':{'extension':ref(C/'EXTENSION_PROPOSED110_01.json'),'review':review_ref}}
assert effective(R,e['program_id'],names[0],experiment,e['base_family'],relevant,bound)==110
try:effective(R,e['program_id'],names[1],experiment,e['base_family'],relevant,bound)
except ValueError as error:
 assert 'first-adopter' in str(error);refusal=str(error)
else:raise AssertionError('39 accepted as first adopter')
(P/'EXTENSION110_REVIEW01.json').write_bytes(review_raw)
(P/'CUMULATIVE_CHECK01.json').write_text(json.dumps({'status':'PASS_METADATA_ONLY','first38':110,'first39_refusal':refusal,'reused_exact_original36_outcome':True,'all108_allocations_preserved':True,'new_claim':False,'evidence':pins},indent=2)+'\n')
print(json.dumps({'status':'PASS_METADATA_ONLY','extension_sha256':review['extension_sha256'],'review_sha256':review_ref['sha256'],'first38':110,'first39':'refused'}))
