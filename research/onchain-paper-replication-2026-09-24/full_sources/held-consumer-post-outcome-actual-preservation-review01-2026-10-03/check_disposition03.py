"""Read only already restored scalar lifecycle metadata, never claims or arrays."""
import hashlib,json,pathlib,stat
OUT=pathlib.Path(__file__).resolve().parent;BASE=OUT.parent;F=BASE/'held-consumer-post-outcome-root-flat-recovery01-2026-10-03/flat01';H=lambda b:hashlib.sha256(b).hexdigest();checks=0
def ok(v,n):
 global checks
 if not v:raise AssertionError(n)
 checks+=1
def raw(p):
 s=p.lstat();ok(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2 and p.resolve()==p,'bounded regular scalar metadata');return p.read_bytes()
q=json.loads(raw(BASE/'held-consumer-post-outcome-root-capture01-2026-10-03/REQUEST01.json'));meta=json.loads(raw(F/'capsule-metadata.json'));mapping=meta['flat_members']
def body(n):return raw(F/mapping[n])
def js(n):return json.loads(body(n))
reg=js(q['baseline']['registration']);rows=[]
for n,exp in reg['experiments'].items():
 d='research_runs/'+n
 if d+'/claim.json' not in mapping:continue
 c=js(d+'/claim.json');fl=js(d+'/failed.json')
 ok(fl['status']=='failed' and fl['claim_sha256']==H(body(d+'/claim.json')) and d+'/complete.json' not in mapping,'failed claim exact no complete')
 actual={x.removeprefix(d+'/outputs/') for x in mapping if x.startswith(d+'/outputs/')}
 ok(actual==set(fl['output_sha256']),'all attempted output bodies denominator exact')
 for name,pin in fl['output_sha256'].items():ok(H(body(d+'/outputs/'+name))==pin,'every failed output retained')
 rows.append({'identity':n,'effective_attempt_budget':c['effective_attempt_budget'],'status':fl['status'],'output_count':len(actual),'claim_sha256':H(body(d+'/claim.json')),'failed_sha256':H(body(d+'/failed.json'))})
ok(len(rows)==5 and sorted(r['effective_attempt_budget'] for r in rows)==[2,3,4,5,6],'all five spent original claims highest6')
exp=reg['experiments'][q['identity']];refs=exp['cumulative_budget_extension']
for r in refs.values():ok(H(body(r['path']))==r['sha256'],'adopted extension metadata pin')
e=js(refs['extension']['path']);rv=js(refs['review']['path']);ok(e['consumed_before']==4 and e['cumulative_ceiling']==6 and rv['decision']=='accepted' and rv['extension_sha256']==refs['extension']['sha256'],'actual current extension/review join')
for r in e['claims']:
 d='research_runs/'+r['experiment'];ok(H(body(d+'/claim.json'))==r['claim_sha256'] and H(body(d+'/failed.json'))==r['terminal_sha256'] and r['terminal_status']=='failed','all extension antecedents actual preserved')
dep='original-import-held-publication-failure-20261003-01';ok(not any(n.startswith('research_runs/'+dep+'/') for n in mapping),'dependent unavailable unclaimed')
g='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+q['identity']+'/guard/'
original=js(g+'final.json');child=js(g+'child_exit.json');ok(original['child_exit_code'] is None and original['cleanup_verified'] is False and child['exit_code']==125,'raw original null false distinct child125')
ledger=js('research_runs/'+q['identity']+'/outputs/cell-ledger.json');ok([x['status'] for x in ledger]==['failed','unavailable'] and all(x['resource_only'] is True for x in ledger),'complete failed unavailable engineering denominator')
r={'schema_version':1,'checks':checks,'actual_original_claims':rows,'highest_adopted':6,'extension_sha256':refs['extension']['sha256'],'extension_review_sha256':refs['review']['sha256'],'dependent':'UNAVAILABLE_UNCLAIMED','original_guard_child_exit_code':None,'original_guard_cleanup_verified':False,'separate_child_exit_code':125,'ledger':ledger,'no_budget_transfer_or_paper_credit':True}
with (OUT/'DISPOSITION_CHECKS03.json').open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'checks':checks,'claims':len(rows),'highest':6,'status':'all_failed'}))
