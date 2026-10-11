import ast,hashlib,json,re,datetime,resource
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(20,20));resource.setrlimit(resource.RLIMIT_AS,(268435456,268435456))
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2]
D=F/'real-data-pilot-full32-cumulative-preparation01-2026-10-11';O=F/'real-data-pilot-full31-cumulative-preparation01-2026-10-11';V=F/'pilot31-cumulative-machine-review01-2026-10-11'
refs={};checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 assert not p.is_symlink() and p.stat().st_size<2097152
 b=p.read_bytes();refs[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)};return b
def js(p):return json.loads(read(p))
def ck(v,n):
 assert v,n
 checks.append(n)
def bound(ref):
 ck(set(ref)=={'path','sha256'},'strict reference '+ref['path'])
 b=read(R/ref['path']);assert sha(b)==ref['sha256'];return b
m=js(D/'MANIFEST01.json')
for ref in m['files'].values():bound(ref)
a=js(D/'CUMULATIVE_ALLOCATION_PROPOSED103_01.json');x=js(D/'EXTENSION_PROPOSED103_01.json')
oa=js(O/'CUMULATIVE_ALLOCATION_PROPOSED102_01.json');ox=js(O/'EXTENSION_PROPOSED102_01.json')
pr=js(V/'EXTENSION102_REVIEW01.json');pv=js(V/'VALIDATION01.json');pm=js(V/'MANIFEST01.json')
for name in ['EXTENSION102_REVIEW01.json','VALIDATION01.json']:
 ck(refs[str((V/name).relative_to(R))]['sha256']==pm['files'][name]['sha256'],'prior accepted manifest '+name)
ck(pr['decision']=='accepted' and pr['extension_sha256']==sha((O/'EXTENSION_PROPOSED102_01.json').read_bytes()),'accepted102 exact extension')
ck(x['claims']==a['closed_claims'] and x['claims'][:-1]==ox['claims']==oa['closed_claims'] and len(x['claims'])==54,'exact single closed31 append')
ck(x['claims'][-1]['experiment']=='eth-paper-real-data-end-to-end-resource-20261011-31' and x['claims'][-1]['terminal_status']=='failed','new row original failed31')
for new,old,allowed in [(a,oa,{'consumed_before','equation','identities','prior_adopted_cumulative_ceiling','prior_reviewed_reserved_ceiling','proposed_cumulative_ceiling','question','qualification','closed_claims'}),(x,ox,{'allocation','claims','consumed_before','cumulative_ceiling','initial_experiment','reason'})]:
 ck(set(new)==set(old) and {k for k in new if new[k]!=old[k]}==allowed,'exact proposal changed-field inverse')
ck(json.loads(bound(x['allocation']))==a,'allocation binding')
ck(a['unchanged_pending_allocation']=={'financial_fit_batches':15,'missing_body_batches':12,'remaining_graph_matching_mcm_resource':1} and len(a['preserved_reserved_preclaim_allowances'])==3,'28 pending3 reserved unchanged')
ck(all(a[k]==0 for k in ['refunds','category_transfers','historical_claims_reopened','new_financial_fits']) and a['maximum_unique_financial_fits_unchanged']==1420,'no refund transfer reopening financial increment')
ck(a['identities']==[x['initial_experiment']]==['eth-paper-real-data-end-to-end-resource-20261011-32'] and a['new_fixed_allocation']=={'full_seven_graph_joint_update_resource_pilot_claims':1},'one fixed fresh32')
relevant=[];counts={'complete':0,'failed':0}
for row in x['claims']:
 d=R/'research_runs'/row['experiment'];cb=read(d/'claim.json');tb=read(d/(row['terminal_status']+'.json'));c=json.loads(cb);t=json.loads(tb)
 ck(sha(cb)==row['claim_sha256'] and sha(tb)==row['terminal_sha256'] and t['claim_sha256']==sha(cb) and t['experiment_id']==c['experiment_id']==row['experiment'] and t['status']==row['terminal_status'] and c['family']==x['base_family'],'actual closed claim family/hash '+row['experiment'])
 ck(not (d/('complete.json' if row['terminal_status']=='failed' else 'failed.json')).exists(),'single terminal '+row['experiment'])
 relevant.append(c);counts[row['terminal_status']]+=1
ck(counts=={'complete':20,'failed':34} and max(c.get('effective_attempt_budget',51) for c in relevant)==102,'actual54 closed highest adopted102')
# Reuse prior authenticated census for unchanged unrelated claims; inspect directory identities only.
old_dirs={Path(p).parent.name for p in pv['references'] if p.startswith('research_runs/') and p.endswith('/claim.json')}
current_dirs={d.name for d in (R/'research_runs').iterdir() if not d.name.startswith('.')}
ck(current_dirs==old_dirs|{x['claims'][-1]['experiment']},'no unreviewed additional claim directory since102')
ck(not (R/'research_runs'/x['initial_experiment']).exists(),'fresh32 unclaimed')
for row in a['preserved_reserved_preclaim_allowances']:ck(not (R/'research_runs'/row['identity']).exists(),'reserve not reclaimed '+row['identity'])
ck(x['base_family']==ox['base_family'] and x['base_family']['prior_attempts']==17 and pv['historical_counts_reused_from_original_index']=={'complete':13,'failed':4},'unchanged17 historical review reused')
ck(a['consumed_before']==x['consumed_before']==71 and a['prior_adopted_cumulative_ceiling']==a['prior_reviewed_reserved_ceiling']==102 and 71+28+3+1==a['proposed_cumulative_ceiling']==x['cumulative_ceiling']==103,'103=71+28+3+1')
review={'schema_version':1,'decision':'accepted','extension_sha256':sha((D/'EXTENSION_PROPOSED103_01.json').read_bytes()),'reviewer':'Independent pilot32 cumulative accounting reviewer','scope':'Exact budget-extension proposal only:103=71 permanently spent(17 historical+54 actual closed;33 complete/38 failed)+28 unchanged pending+3 preserved closed preclaim reserves+1 fresh fixed unused32. Actual54 claim/terminal hashes and family authenticated; highest adopted102 and unchanged prior102 rows/categories retained. No refunds, transfers, reopening, paper65 or new financial fits; maximum1420 unchanged. No allowance adoption, source installation, admission, native/transport/full-entry or empirical launch authority. Preserve original scientific method,60s lease and resource limits. Actual complete declared failed31 external recovery and independently accepted exact successor source/caller/entry remain separate prerequisites.'}
rb=(json.dumps(review,sort_keys=True,indent=2)+'\n').encode();rp=str((P/'EXTENSION103_REVIEW01.json').relative_to(R));reference={'extension':m['files']['EXTENSION_PROPOSED103_01.json'],'review':{'path':rp,'sha256':sha(rb)}}
source=read(R/'tradingagents/research/budget_extensions.py');ck(sha(source)=='59d22880e9ff7909508db6b0c15a7a833df30be365af4e31d643ed64afabb25a','unchanged validator')
ns={'hashlib':hashlib,'json':json,'re':re};nodes=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='effective_budget'];exec(compile(ast.Module(body=nodes,type_ignores=[]),'original-metadata-budget-validator','exec'),ns)
def read_bound(ref):
 assert set(ref)=={'path','sha256'}
 b=rb if ref['path']==rp else read(R/ref['path']);assert sha(b)==ref['sha256'];return b
ck(ns['effective_budget'](R,x['program_id'],x['initial_experiment'],{'cumulative_budget_extension':reference},x['base_family'],relevant,read_bound)==103,'actual metadata helper returns103; no admission')
(P/'EXTENSION103_REVIEW01.json').write_bytes(rb)
result={'decision':'ACCEPT_EXACT103_BUDGET_PROPOSAL_ONLY','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'references':refs,'equation':'103=71+28+3+1','actual_closed_counts':counts,'historical_counts_reused':{'complete':13,'failed':4},'highest_adopted':102,'review_ref':reference['review'],'new_claim_or_adoption':False}
(P/'VALIDATION01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'review':reference['review'],'equation':result['equation']}))
