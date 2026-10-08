import hashlib,json,resource,os,signal
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(60)
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N=F/'real-data-pilot-retry23-registration01-2026-10-09';H=Path(__file__).resolve().parent;ev={};checks=[]
def read(p):
 b=p.read_bytes();ev[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return json.loads(b)
def check(n,v):
 assert v,n
 checks.append(n)
e=read(N/'EXTENSION_PROPOSED94_01.json');a=read(N/'CUMULATIVE_ALLOCATION_PROPOSED94_01.json');prior=read(F/'real-data-pilot-retry22-registration01-2026-10-08/CUMULATIVE_ALLOCATION_PROPOSED93_01.json')
check('allocation_pin',ev[e['allocation']['path']]==e['allocation']['sha256'])
check('claims_join',e['claims']==a['closed_claims'])
actual=[];ceilings=[];active=[]
for p in sorted((R/'research_runs').glob('*/claim.json')):
 # Metadata only; enumerate solely this program's actual lifecycle claims.
 c=json.loads(p.read_bytes())
 if c.get('program_id')!=e['program_id']:continue
 name=c['experiment_id'];terminal=[p.parent/x for x in ('complete.json','failed.json') if (p.parent/x).is_file()]
 if not terminal:active.append(name);continue
 check('one_terminal_'+name,len(terminal)==1)
 c=read(p);t=read(terminal[0]);check('terminal_claim_join_'+name,t['claim_sha256']==ev[str(p.relative_to(R))])
 actual.append({'experiment':name,'claim_sha256':ev[str(p.relative_to(R))],'terminal_sha256':ev[str(terminal[0].relative_to(R))],'terminal_status':t['status']});ceilings.extend([c['effective_attempt_budget']] if 'effective_attempt_budget' in c else [])
check('all_actual_closed_claims_exact',sorted(actual,key=lambda x:x['experiment'])==sorted(e['claims'],key=lambda x:x['experiment']))
check('actual_counts',len(actual)==45 and sum(x['terminal_status']=='complete' for x in actual)==20 and sum(x['terminal_status']=='failed' for x in actual)==25 and not active)
check('highest_actual93',max(ceilings)==93==a['prior_adopted_cumulative_ceiling'])
check('historical17_and_spent62',a['base_family']==prior['base_family']==e['base_family'] and e['base_family']['prior_attempts']==17 and e['consumed_before']==a['consumed_before']==45+17==62)
for k in ('unchanged_pending_allocation','preserved_reserved_preclaim_allowances','new_fixed_allocation','maximum_unique_financial_fits_unchanged','refunds','category_transfers','historical_claims_reopened','new_financial_fits'):check('preserved_'+k,a[k]==prior[k])
check('allocation_equation',sum(a['unchanged_pending_allocation'].values())==28 and len(a['preserved_reserved_preclaim_allowances'])==3 and sum(a['new_fixed_allocation'].values())==1 and 62+28+3+1==e['cumulative_ceiling']==a['proposed_cumulative_ceiling']==94)
name='eth-paper-real-data-end-to-end-resource-20261009-23';check('single_fresh23',e['initial_experiment']==name and a['identities']==[name] and not (R/'research_runs'/name).exists())
old={x['experiment']:x for x in prior['closed_claims']};new={x['experiment']:x for x in actual};check('only22_appended',set(new)-set(old)=={'eth-paper-real-data-end-to-end-resource-20261008-22'} and all(new[k]==v for k,v in old.items()))
result={'schema_version':1,'decision':'accepted','extension_sha256':ev[str((N/'EXTENSION_PROPOSED94_01.json').relative_to(R))],'reviewer':'Independent retry23 reviewer; actual lifecycle and accepted93 allocation comparison','scope':'Prospective cumulative94 metadata only:45 genuine closed local claims20complete25failed plus17preserved historical=62spent,28unchanged pending,3unchanged closed preclaim reserves,1fresh23. All actual claim/terminal hashes joined; highest adopted93. Prior93 claims byte identities retained; only terminal22 added. Base family and no-refund/transfer/reopen/financial-fit limits unchanged. No source/resource/capacity/entry/release/launch admission follows;262145B incremental scratch remains unregistered.'}
(H/'EXTENSION94_REVIEW01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');(H/'BUDGET94_CHECKS01.json').write_text(json.dumps({'checks':checks,'evidence':ev,'actual_claims':actual,'active_claims':active},indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':'accepted','checks':len(checks),'review_sha256':hashlib.sha256((H/'EXTENSION94_REVIEW01.json').read_bytes()).hexdigest()}))
