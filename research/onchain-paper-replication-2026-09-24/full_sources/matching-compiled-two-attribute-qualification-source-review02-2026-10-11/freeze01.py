import hashlib,json,os,resource
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'matching-compiled-two-attribute-qualification02-2026-10-11'
def ref(p):
 b=p.read_bytes();return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(n,v):
 with (P/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
out={'schema_version':1,'decision':'REFUSED_FAILURE_REPORTING_REPAIR_REQUIRED','reviewer':'independent outcome16_release_review','candidate_manifest':ref(D/'MANIFEST02.json'),'fixture':ref(D/'fixture02.py'),'evidence':ref(P/'RESULT01.json'),'prior_review':ref(F/'matching-compiled-two-attribute-agreement-source-review01-2026-10-11/REVIEW01.json'),'findings':[{'severity':'P1','path':str((D/'fixture02.py').relative_to(R)),'line':77,'issue':'Fallible traceback write precedes failure assignment; finally emits PASS after original exception when traceback storage fails.','repair':'Mark failure before all fallible reporting and retain primary/secondary failures; no success after any original or reporting failure.'}],'accepted_seams':['Exclusive attempt and result refusal preserve spent output','Raw descriptor setup precedes loader/import','Original references and literal inverses match','Numerical case/criteria body unchanged'],'not_executed':['native or scientific imports','fixture or numerical cases','genuine authority','live process inspection'],'execution_released':False,'reviewer_initial_failure':'Original checker expected different diff labels; preserved check01/stderr01. check02 only corrects header expectation.'}
write('REVIEW01.json',out);write('MANIFEST01.json',{'decision':out['decision'],'files':{str(p.relative_to(P)):{k:v for k,v in ref(p).items() if k!='path'} for p in sorted(P.rglob('*')) if p.is_file() and p.name!='MANIFEST01.json'}})
print(json.dumps({'review':ref(P/'REVIEW01.json'),'manifest':ref(P/'MANIFEST01.json')},sort_keys=True))
