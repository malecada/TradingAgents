"""Independent finite metadata-only allocation check; never creates a claim."""
import json,pathlib,hashlib,collections,resource,signal,os,sys
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(60);os.nice(10);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
H=pathlib.Path(__file__).resolve().parent;F=H.parent;ROOT=H.parents[3];C=F/'real-data-pilot-full25-entry01-2026-10-09';P=F/'real-data-pilot-grouped-registration01-2026-10-09'
j=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=j(C/'EXTENSION_PROPOSED96_01.json');a=j(C/'CUMULATIVE_ALLOCATION_PROPOSED96_01.json');old=j(P/'EXTENSION_PROPOSED95_01.json');oa=j(P/'CUMULATIVE_ALLOCATION_PROPOSED95_01.json')
prior=F/'mcm-batched-full-pilot-allocation-review01-2026-10-09/EXTENSION95_REVIEW01.json';assert j(prior)['decision']=='accepted' and j(prior)['extension_sha256']==sha(P/'EXTENSION_PROPOSED95_01.json')
assert sha(ROOT/e['allocation']['path'])==e['allocation']['sha256']
assert e['base_family']==old['base_family']==a['base_family'] and e['base_family']['attempt_budget']==51 and e['base_family']['prior_attempts']==17
assert len(e['claims'])==47 and e['claims'][:-1]==old['claims'] and a['closed_claims']==e['claims'];assert e['claims'][-1]['experiment']==old['initial_experiment']
changed={k for k in a if a[k]!=oa.get(k)}
assert set(a)==set(oa) and changed=={'closed_claims','consumed_before','equation','identities','prior_adopted_cumulative_ceiling','prior_reviewed_reserved_ceiling','proposed_cumulative_ceiling','question'}
assert sum(a['unchanged_pending_allocation'].values())==28 and len(a['preserved_reserved_preclaim_allowances'])==3
assert a['refunds']==a['category_transfers']==a['historical_claims_reopened']==a['new_financial_fits']==0 and a['maximum_unique_financial_fits_unchanged']==1420
seen=set();counts=collections.Counter();claims=[];receipt_pins={}
for row in e['claims']:
 name=row['experiment'];assert name not in seen;seen.add(name);p=ROOT/'research_runs'/name
 cp=p/'claim.json';tp=p/(row['terminal_status']+'.json');assert cp.is_file() and not cp.is_symlink() and tp.is_file() and not tp.is_symlink()
 c=j(cp);t=j(tp);assert sha(cp)==row['claim_sha256'] and sha(tp)==row['terminal_sha256']
 assert c['experiment_id']==t['experiment_id']==name and c['program_id']==e['program_id'] and c['family']==e['base_family']
 assert t['status']==row['terminal_status'] and t['claim_sha256']==row['claim_sha256']
 assert not (p/('failed.json' if row['terminal_status']=='complete' else 'complete.json')).exists()
 counts[t['status']]+=1;claims.append(c);receipt_pins.update({str(cp.relative_to(ROOT)):sha(cp),str(tp.relative_to(ROOT)):sha(tp)})
actual=set()
for p in (ROOT/'research_runs').glob('*/claim.json'):
 c=j(p)
 if c.get('family',{}).get('mechanism_id')==e['base_family']['mechanism_id']:actual.add(c['experiment_id'])
assert actual==seen and counts=={'complete':20,'failed':27}
assert max(c.get('effective_attempt_budget',51) for c in claims)==95
history_path=ROOT/'research/onchain-paper-replication-2026-09-24/history.json';history=j(history_path);hc=collections.Counter()
assert history['prior_attempts']==17 and len(history['lineage'])==17
for name in history['lineage']:
 p=ROOT/'research_runs'/name;present=[p/(v+'.json') for v in ('complete','failed') if (p/(v+'.json')).exists()];assert len(present)==1;hc[present[0].stem]+=1
for path,pin in history['metadata_hashes'].items():assert sha(ROOT/path)==pin
assert hc=={'complete':13,'failed':4}
assert e['consumed_before']==a['consumed_before']==47+17==64
assert e['cumulative_ceiling']==a['proposed_cumulative_ceiling']==64+28+3+1==96
assert a['prior_adopted_cumulative_ceiling']==a['prior_reviewed_reserved_ceiling']==95
name=e['initial_experiment'];assert a['identities']==[name] and name=='eth-paper-real-data-end-to-end-resource-20261009-25'
unused=[ROOT/'research_runs'/name,ROOT/'research_artifacts/archive-dispatch-ethpilot-20261009-25',ROOT/'runs'/name,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/name,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/name]
for p in unused:assert not os.path.lexists(p),p
for r in a['preserved_reserved_preclaim_allowances']:
 assert not (ROOT/'research_runs'/r['identity']/'claim.json').exists()
 for k in ('outcome_review','recovery_review','terminal_root'):assert sha(ROOT/r[k]['path'])==r[k]['sha256']
recovery=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome05/returned-review01/RECOVERY_REVIEW01.json';assert j(recovery)['decision']=='accepted' and j(recovery)['regular_files']==50
scope='Same-family cumulative allowance only:47 actual closed claims (20 complete/27 failed) plus17 preserved historical (13 complete/4 failed)=64 permanently spent;28 unchanged pending+3 closed preclaim reserves+ONE unused fixed25 resource pilot=96. Base51, prior17, all failures, original financial allocations/1420 ceiling and zero refunds/transfers/reopenings preserved. No source/capacity/entry/release/launch or financial permission.'
r=dict(schema_version=1,decision='accepted',extension_sha256=sha(C/'EXTENSION_PROPOSED96_01.json'),reviewer='Independent full25 allocation reviewer; actual47 receipt hashes and prior95 literal allocation comparison',scope=scope)
(H/'EXTENSION96_REVIEW01.json').write_text(json.dumps(r,indent=2)+'\n')
sys.path.insert(0,str(ROOT));from tradingagents.research.budget_extensions import effective_budget
ref=lambda p:dict(path=str(p.relative_to(ROOT)),sha256=sha(p))
def read_bound(ref):
 p=ROOT/ref['path'];assert sha(p)==ref['sha256'];return p.read_bytes()
value=effective_budget(ROOT,e['program_id'],name,{'cumulative_budget_extension':{'extension':ref(C/'EXTENSION_PROPOSED96_01.json'),'review':ref(H/'EXTENSION96_REVIEW01.json')}},e['base_family'],claims,read_bound)
assert value==96
result=dict(decision='accepted',scope=scope,actual_counts=dict(counts),historical_counts=dict(hc),spent=64,effective_budget_actual_function=value,changed_allocation_fields=sorted(changed),unchanged_allocation_fields=sorted(set(a)-changed),claim_terminal_pins=receipt_pins,unused_paths=[str(p.relative_to(ROOT)) for p in unused],evidence={str(p.relative_to(ROOT)):sha(p) for p in [C/'EXTENSION_PROPOSED96_01.json',C/'CUMULATIVE_ALLOCATION_PROPOSED96_01.json',prior,history_path,recovery]},scientific_scope='Declared unchanged only; final policy/source/resource entry joins require separate review.',no_run_or_claim=True)
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':'accepted','review_sha256':sha(H/'EXTENSION96_REVIEW01.json'),'check_sha256':sha(H/'CHECK01.json'),'actual_counts':dict(counts),'history':dict(hc)}))
