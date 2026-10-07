"""Bounded genuine cumulative87 validator; exact39 typed claim/terminal metadata only."""
import hashlib,json
from pathlib import Path
from collections import Counter
from tradingagents.research.budget_extensions import effective_budget
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-retry16-review01-2026-10-07';D=F/'real-data-pilot-retry16-registration01-2026-10-07'
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(r):
 p=R/r['path'];assert ref(p)['sha256']==r['sha256'];return p.read_bytes()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
a=json.loads((D/'CUMULATIVE_ALLOCATION_PROPOSED87_01.json').read_text());p=D/'EXTENSION_PROPOSED87_01.json';e=json.loads(p.read_text())
assert ref(p)['sha256']=='d132bcb2d837393d9becd13f3faf7afcdd56657b878f1e7ebe0c69301dc5fc54'
prior_dir=F/'real-data-pilot-retry15-registration01-2026-10-07';old=json.loads((prior_dir/'EXTENSION_PROPOSED86_01.json').read_text());olda=json.loads((prior_dir/'CUMULATIVE_ALLOCATION_PROPOSED86_01.json').read_text());accepted=json.loads((F/'real-data-pilot-retry15-review01-2026-10-07/EXTENSION_REVIEW01.json').read_text())
assert accepted['decision']=='accepted' and accepted['extension_sha256']==ref(prior_dir/'EXTENSION_PROPOSED86_01.json')['sha256']
assert e['claims'][:-1]==old['claims'] and len(e['claims'])==39
assert a['closed_claims']==e['claims'] and a['unchanged_pending_allocation']==olda['unchanged_pending_allocation'] and a['preserved_reserved_preclaim_allowances']==olda['preserved_reserved_preclaim_allowances']
assert e['base_family']==old['base_family'] and e['program_id']==old['program_id'] and e['consumed_before']==a['consumed_before']==56
assert e['initial_experiment']==a['identities'][0]=='eth-paper-real-data-end-to-end-resource-20261007-16'
assert sum(a['unchanged_pending_allocation'].values())==28 and len(a['preserved_reserved_preclaim_allowances'])==2 and sum(a['new_fixed_allocation'].values())==1
assert a['refunds']==a['category_transfers']==a['historical_claims_reopened']==a['new_financial_fits']==0
assert a['maximum_unique_financial_fits_unchanged']==olda['maximum_unique_financial_fits_unchanged']==1420
last=e['claims'][-1];assert last['experiment']=='eth-paper-real-data-end-to-end-resource-20261007-15' and last['terminal_status']=='failed'
outdir=F/'real-data-pilot-fifteenth-resource-failed-review01-2026-10-07';out=json.loads((outdir/'OUTCOME_REVIEW01.json').read_bytes());recovery=json.loads((outdir/'returned-git-recovery01/RECOVERY_REVIEW01.json').read_bytes())
assert ref(outdir/'OUTCOME_REVIEW01.json')['sha256']=='1c9358bc026c44eabdffed98f29e5e8e0af4d33760f82085983a2fe738686f5e'
assert ref(outdir/'returned-git-recovery01/RECOVERY_REVIEW01.json')['sha256']=='5e05f46442fc168ef571d949196a3e9c0f8bae8a8995d2744ecdfb18d31d18be'
assert out['decision']=='accepted' and recovery['decision']=='accepted' and recovery['actual_external_recovery_accepted']
assert last['claim_sha256']==out['claim_sha256'] and recovery['original_outcome']==ref(outdir/'OUTCOME_REVIEW01.json')
claims=[]
for row in e['claims']:
 cp=R/'research_runs'/row['experiment']/'claim.json';assert ref(cp)['sha256']==row['claim_sha256']
 c=json.loads(cp.read_bytes());assert c['program_id']==e['program_id'] and c['family']==e['base_family'] and c['experiment_id']==row['experiment'];claims.append(c)
assert len(claims)==len({c['experiment_id'] for c in claims})==39 and max(c.get('effective_attempt_budget',e['base_family']['attempt_budget']) for c in claims)==86
assert not (R/'research_runs'/e['initial_experiment']).exists()
review={'schema_version':1,'decision':'accepted','extension_sha256':ref(p)['sha256'],'reviewer':'outcome15_review independent cumulative87 reviewer','scope':'Same-family fresh16 only:56 genuine closed(17 correlated prior+39 current),28 unchanged pending,2 permanently closed preclaim03/08 reserves,1 fixed unused16=87. Genuine failed15 and exact public external recovery retained. Two numeric reservation fields amended from complete7graph metadata; exact user-authorized8.5GiBstartup/2.5GiBreserve with6GiBmax5GiBhigh preserved. No refund, transfer, historical reopening, resampling, cap ladder or financial-fit credit. Exact committed source/input/runtime and separate final release remain required.'}
rp=H/'EXTENSION_REVIEW01.json';save(rp,review);er={'extension':ref(p),'review':ref(rp)}
budget=effective_budget(R,e['program_id'],e['initial_experiment'],{'cumulative_budget_extension':er},e['base_family'],claims,read);assert budget==87
result={'schema_version':1,'decision':'accepted','allocation':ref(D/'CUMULATIVE_ALLOCATION_PROPOSED87_01.json'),'extension':ref(p),'review':ref(rp),'actual_current_claims':39,'current_terminal_counts':dict(Counter(r['terminal_status'] for r in e['claims'])),'correlated_prior':17,'consumed_before':56,'unchanged_prior_snapshot_rows':38,'new_actual_row':last,'highest_actual_claimed_ceiling':86,'effective_attempt_budget':budget,'pending':28,'closed_preclaim_reserved':2,'fresh_fixed16':1,'equation':'56+28+2+1=87','genuine_metadata_validator':ref(R/'tradingagents/research/budget_extensions.py'),'prior_accepted_review':ref(F/'real-data-pilot-retry15-review01-2026-10-07/EXTENSION_REVIEW01.json'),'actual15_outcome':ref(outdir/'OUTCOME_REVIEW01.json'),'actual15_recovery':ref(outdir/'returned-git-recovery01/RECOVERY_REVIEW01.json'),'scope':'Only exact39 typed current claim/terminal metadata read by genuine effective_budget; no historical numerical artifacts or other-family claim rescan.','not_tested':'No claim, ledger or registration mutation; no private input, scientific arrays, real admission or numerical execution. Earlier17 correlated history remains carried through unchanged accepted family.'}
mp=H/'EXTENSION_MACHINE_REVIEW01.json';save(mp,result);print(json.dumps([ref(rp),ref(mp)]))
