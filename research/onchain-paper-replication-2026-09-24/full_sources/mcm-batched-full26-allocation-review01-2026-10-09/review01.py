"""Changed accounting seam only; inherited96 evidence retained, no research execution."""
import json,hashlib,os,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30)
H=Path(__file__).resolve().parent;F=H.parent;ROOT=H.parents[3];N=F/'real-data-pilot-full26-entry01-2026-10-09';P=F/'real-data-pilot-full25-entry01-2026-10-09';R=F/'mcm-batched-full25-allocation-review01-2026-10-09'
j=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=j(N/'EXTENSION_PROPOSED97_01.json');a=j(N/'CUMULATIVE_ALLOCATION_PROPOSED97_01.json');old=j(P/'EXTENSION_PROPOSED96_01.json');oa=j(P/'CUMULATIVE_ALLOCATION_PROPOSED96_01.json')
review=j(R/'EXTENSION96_REVIEW01.json');assert sha(R/'EXTENSION96_REVIEW01.json')=='6ffa07fdc8f9e966d040a685b950c9f4a69c8fca15fb4b516352768ee8534507' and review['decision']=='accepted' and review['extension_sha256']==sha(P/'EXTENSION_PROPOSED96_01.json')
assert sha(R/'CHECK01.json')=='7da1c46267e98edbc274f336e5c1b764688fb201166b1ff5f500fc87fa0bf33b'
priorcheck=j(R/'CHECK01.json');assert priorcheck['spent']==64 and priorcheck['evidence'][str((P/'CUMULATIVE_ALLOCATION_PROPOSED96_01.json').relative_to(ROOT))]==sha(P/'CUMULATIVE_ALLOCATION_PROPOSED96_01.json')
assert e['base_family']==old['base_family']==a['base_family'] and e['base_family']['attempt_budget']==51 and e['base_family']['prior_attempts']==17
assert e['claims'][:-1]==old['claims'] and len(e['claims'])==48 and a['closed_claims']==e['claims']
assert sha(ROOT/e['allocation']['path'])==e['allocation']['sha256']
changed={k for k in a if a[k]!=oa.get(k)};assert set(a)==set(oa) and changed=={'closed_claims','consumed_before','equation','identities','prior_adopted_cumulative_ceiling','prior_reviewed_reserved_ceiling','proposed_cumulative_ceiling','question'}
row=e['claims'][-1];name=row['experiment'];assert name==old['initial_experiment']=='eth-paper-real-data-end-to-end-resource-20261009-25' and row['terminal_status']=='failed'
p=ROOT/'research_runs'/name;cpath=p/'claim.json';tpath=p/'failed.json'
assert cpath.is_file() and tpath.is_file() and not cpath.is_symlink() and not tpath.is_symlink() and not (p/'complete.json').exists()
c=j(cpath);t=j(tpath);assert sha(cpath)==row['claim_sha256'] and sha(tpath)==row['terminal_sha256']
assert c['experiment_id']==t['experiment_id']==name and t['status']=='failed' and t['claim_sha256']==sha(cpath)
assert c['family']==e['base_family'] and c['program_id']==e['program_id']==old['program_id'] and c['effective_attempt_budget']==96
actual={}
for path in (ROOT/'research_runs').glob('*/claim.json'):
 value=j(path)
 if value.get('family',{}).get('mechanism_id')==e['base_family']['mechanism_id']:actual[value['experiment_id']]=value.get('effective_attempt_budget',51)
assert set(actual)=={r['experiment'] for r in e['claims']} and max(actual.values())==96
assert e['consumed_before']==a['consumed_before']==48+17==65
assert sum(a['unchanged_pending_allocation'].values())==28 and len(a['preserved_reserved_preclaim_allowances'])==3
assert e['cumulative_ceiling']==a['proposed_cumulative_ceiling']==65+28+3+1==97
assert a['prior_adopted_cumulative_ceiling']==a['prior_reviewed_reserved_ceiling']==96
assert a['refunds']==a['category_transfers']==a['historical_claims_reopened']==a['new_financial_fits']==0 and a['maximum_unique_financial_fits_unchanged']==1420
new=e['initial_experiment'];assert a['identities']==[new] and new=='eth-paper-real-data-end-to-end-resource-20261009-26'
unused=[ROOT/'research_runs'/new,ROOT/'runs'/new,ROOT/'research_artifacts/archive-dispatch-ethpilot-20261009-26',ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/new,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/new]
for path in unused:assert not os.path.lexists(path),path
scope='Same-family cumulative allowance only:48 actual closed claims plus17 preserved historical=65 permanently spent (33 complete/32 failed);28 unchanged pending+3 closed preclaim reserves+ONE unused fixed26 resource pilot=97. Base51/prior17, prior96 history and financial allocations/1420 ceiling preserved; no refund, transfer or reopening. No entry, capacity, source adoption, launch or financial permission.'
result=dict(schema_version=1,decision='accepted',extension_sha256=sha(N/'EXTENSION_PROPOSED97_01.json'),reviewer='Independent full26 allocation reviewer; new actual25 terminal binding and exact inherited96 accounting delta',scope=scope)
assert set(result)==set(review)
(H/'EXTENSION97_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n')
facts=dict(decision='accepted_allowance_only',spent=65,actual_closed=48,actual_counts={'complete':20,'failed':28},historical_counts={'complete':13,'failed':4},new_terminal=row,highest_adopted=96,changed_allocation_fields=sorted(changed),unchanged_fields=sorted(set(a)-changed),unused_paths=[str(p.relative_to(ROOT)) for p in unused],evidence={str(p.relative_to(ROOT)):sha(p) for p in [N/'EXTENSION_PROPOSED97_01.json',N/'CUMULATIVE_ALLOCATION_PROPOSED97_01.json',R/'EXTENSION96_REVIEW01.json',R/'CHECK01.json',cpath,tpath]},old47_terminal_checks_reused=True,no_claim_or_execution=True)
(H/'CHECK01.json').write_text(json.dumps(facts,indent=2)+'\n');print(json.dumps({'decision':'accepted_allowance_only','review_sha256':sha(H/'EXTENSION97_REVIEW01.json'),'check_sha256':sha(H/'CHECK01.json')}))
