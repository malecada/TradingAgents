import json,pathlib,hashlib,collections,resource,signal,os
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30);os.nice(10);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
R=pathlib.Path(__file__).resolve().parent;F=R.parent;ROOT=pathlib.Path.cwd();C=F/'real-data-pilot-grouped-registration01-2026-10-09';O=F/'real-data-pilot-retry23-registration01-2026-10-09'
j=lambda p:json.loads(pathlib.Path(p).read_bytes());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
e=j(C/'EXTENSION_PROPOSED95_01.json');a=j(C/'CUMULATIVE_ALLOCATION_PROPOSED95_01.json');old=j(O/'EXTENSION_PROPOSED94_01.json');oa=j(O/'CUMULATIVE_ALLOCATION_PROPOSED94_01.json')
assert h(ROOT/e['allocation']['path'])==e['allocation']['sha256']
assert e['base_family']==old['base_family'] and e['base_family']['attempt_budget']==51 and e['base_family']['prior_attempts']==17
assert e['claims'][:-1]==old['claims'] and len(e['claims'])==46 and a['closed_claims']==e['claims']
assert e['claims'][-1]['experiment']==old['initial_experiment']
changed={k for k in a if a[k]!=oa.get(k)}
assert changed=={'closed_claims','consumed_before','prior_adopted_cumulative_ceiling','prior_reviewed_reserved_ceiling','proposed_cumulative_ceiling','identities','new_fixed_allocation','equation','question','qualification'},changed
assert set(a)==set(oa)
assert a['unchanged_pending_allocation']==oa['unchanged_pending_allocation'] and sum(a['unchanged_pending_allocation'].values())==28
assert a['preserved_reserved_preclaim_allowances']==oa['preserved_reserved_preclaim_allowances'] and len(a['preserved_reserved_preclaim_allowances'])==3
assert a['refunds']==a['historical_claims_reopened']==a['new_financial_fits']==0 and a['maximum_unique_financial_fits_unchanged']==1420
seen=set();counts=collections.Counter();hist=[]
for row in e['claims']:
 name=row['experiment'];assert name not in seen;seen.add(name)
 p=ROOT/'research_runs'/name;c=j(p/'claim.json');t=j(p/(row['terminal_status']+'.json'))
 assert h(p/'claim.json')==row['claim_sha256'] and h(p/(row['terminal_status']+'.json'))==row['terminal_sha256']
 assert c['experiment_id']==t['experiment_id']==name and c['program_id']==e['program_id'] and c['family']==e['base_family']
 assert t['status']==row['terminal_status'] and t['claim_sha256']==row['claim_sha256']
 counts[t['status']]+=1;hist.append({'experiment':name,'source':c['source'],'effective_attempt_budget':c.get('effective_attempt_budget',c['family']['attempt_budget']),'claim_sha256':row['claim_sha256'],'terminal_sha256':row['terminal_sha256']})
actual=set()
for p in (ROOT/'research_runs').glob('*/claim.json'):
 c=j(p)
 if c.get('family',{}).get('mechanism_id')==e['base_family']['mechanism_id']:actual.add(c['experiment_id'])
assert actual==seen and max(x['effective_attempt_budget'] for x in hist)==94
assert e['consumed_before']==a['consumed_before']==46+17==63
assert e['cumulative_ceiling']==a['proposed_cumulative_ceiling']==63+28+3+1==95
name=e['initial_experiment'];assert a['identities']==[name] and name.endswith('20261009-24') and name not in seen
for p in [ROOT/'research_runs'/name,ROOT/'research_artifacts/archive-dispatch-ethpilot-20261009-24',ROOT/'runs'/name]:assert not p.exists(),p
for r in a['preserved_reserved_preclaim_allowances']:
 for k in ('outcome_review','recovery_review','terminal_root'):assert h(ROOT/r[k]['path'])==r[k]['sha256']
review94=F/'pilot-throughput23-review01-2026-10-09/EXTENSION94_REVIEW01.json';assert j(review94)['extension_sha256']==h(O/'EXTENSION_PROPOSED94_01.json') and j(review94)['decision']=='accepted'
newclaim=j(ROOT/'research_runs'/old['initial_experiment']/'claim.json');assert newclaim['effective_attempt_budget']==94
scope='Cumulative allocation only:46 actual closed same-family claims plus17 preserved historical=63 spent;28 unchanged pending+3 closed preclaim reserves+1 fresh full resource pilot=95. Original base51, source history, all failed starts and financial-fit ceiling1420 preserved. One unused24 namespace. No capacity, source installation, entry, release, execution or financial permission granted.'
r={'schema_version':1,'decision':'accepted','extension_sha256':h(C/'EXTENSION_PROPOSED95_01.json'),'reviewer':'Independent full-pilot allocation reviewer; actual receipt namespace and prior94 comparison','scope':scope}
(R/'EXTENSION95_REVIEW01.json').write_text(json.dumps(r,indent=2)+'\n')
s={'decision':'accepted','scope':scope,'evidence':{str(p.relative_to(ROOT)):h(p) for p in [C/'EXTENSION_PROPOSED95_01.json',C/'CUMULATIVE_ALLOCATION_PROPOSED95_01.json',C/'ACCOUNTING_CHECK01.json',C/'prepare_allocation95.py',review94]},'actual_terminal_counts':dict(counts),'claim_source_history':hist,'unchanged_allocation_fields':sorted(set(a)-changed),'fresh_identity':name,'scientific_scope_declared_only':{'graphs':7,'scalar_cells':415968128,'motifs':32,'original_spent_samples':512,'financial_fits_added':0,'prefix_stop':False},'limitations':['Scientific policy/capacity/source binding is not established by this allocation review.','No claims, registrations, numerical jobs or external actions performed.','Actual23 outcome/recovery acceptance reused; no historical scientific test repeated.']}
(R/'SOURCE_REVIEW01.json').write_text(json.dumps(s,indent=2)+'\n')
print(json.dumps({'decision':'accepted','counts':dict(counts),'extension_review_sha256':h(R/'EXTENSION95_REVIEW01.json'),'source_review_sha256':h(R/'SOURCE_REVIEW01.json')}))
