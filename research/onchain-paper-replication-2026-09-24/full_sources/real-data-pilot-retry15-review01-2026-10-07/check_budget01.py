import hashlib,json
from pathlib import Path
from collections import Counter
from tradingagents.research.budget_extensions import effective_budget
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-retry15-review01-2026-10-07';D=F/'real-data-pilot-retry15-registration01-2026-10-07'
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(r):
 p=R/r['path'];assert ref(p)['sha256']==r['sha256'];return p.read_bytes()
a=json.loads((D/'CUMULATIVE_ALLOCATION_PROPOSED86_01.json').read_text());p=D/'EXTENSION_PROPOSED86_01.json';e=json.loads(p.read_text());old=json.loads((F/'real-data-pilot-retry14-registration01-2026-10-06/EXTENSION_PROPOSED85_01.json').read_text());olda=json.loads((F/'real-data-pilot-retry14-registration01-2026-10-06/CUMULATIVE_ALLOCATION_PROPOSED85_01.json').read_text());assert e['claims'][:-1]==old['claims'] and len(e['claims'])==38
assert a['closed_claims']==e['claims'] and a['unchanged_pending_allocation']==olda['unchanged_pending_allocation'] and a['preserved_reserved_preclaim_allowances']==olda['preserved_reserved_preclaim_allowances']
assert sum(a['unchanged_pending_allocation'].values())==28 and len(a['preserved_reserved_preclaim_allowances'])==2 and sum(a['new_fixed_allocation'].values())==1 and a['refunds']==a['category_transfers']==a['historical_claims_reopened']==a['new_financial_fits']==0
claims=[]
for cp in (R/'research_runs').glob('*/claim.json'):
 c=json.loads(cp.read_text())
 if c.get('program_id')==e['program_id'] and c.get('family')==e['base_family']:claims.append(c)
assert len(claims)==38 and max(c.get('effective_attempt_budget',e['base_family']['attempt_budget']) for c in claims)==85 and e['initial_experiment'] not in {c['experiment_id'] for c in claims}
review={'schema_version':1,'decision':'accepted','extension_sha256':ref(p)['sha256'],'reviewer':'pilot14_review independent cumulative86 reviewer','scope':'Same-family fresh15 only: 55 genuine closed (17 prior +38 current),28 unchanged pending,2 permanently closed preclaim03/08 reserves,1 fixed unused15=86. No refund, transfer, historical reopening, resampling, cap increase or financial-fit credit. Exact committed source/input/runtime and separate release remain required.'}
rp=H/'EXTENSION_REVIEW01.json';rp.write_text(json.dumps(review,indent=2,sort_keys=True)+'\n');er={'extension':ref(p),'review':ref(rp)}
budget=effective_budget(R,e['program_id'],e['initial_experiment'],{'cumulative_budget_extension':er},e['base_family'],claims,read);assert budget==86
result={'schema_version':1,'decision':'accepted','allocation':ref(D/'CUMULATIVE_ALLOCATION_PROPOSED86_01.json'),'extension':ref(p),'review':ref(rp),'actual_current_claims':38,'current_terminal_counts':dict(Counter(r['terminal_status'] for r in e['claims'])),'correlated_prior':17,'consumed_before':55,'unchanged_prior_snapshot_rows':37,'new_actual_row':e['claims'][-1],'highest_actual_claimed_ceiling':85,'effective_attempt_budget':budget,'pending':28,'closed_preclaim_reserved':2,'fresh_fixed15':1,'equation':'55+28+2+1=86','genuine_metadata_validator':ref(R/'tradingagents/research/budget_extensions.py'),'not_tested':'No claim, ledger or registration mutation; no private input, scientific arrays, real admission or numerical execution.'};mp=H/'EXTENSION_MACHINE_REVIEW01.json';mp.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps([ref(rp),ref(mp)]))
