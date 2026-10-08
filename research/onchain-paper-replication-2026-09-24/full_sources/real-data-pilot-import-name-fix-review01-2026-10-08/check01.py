import ast,hashlib,json,tempfile
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;R=P.parents[3];A=P.parent/'real-data-pilot-import-name-fix01-2026-10-08';N=R/'tradingagents/research/onchain_replication'
ns={};exec(compile((N/'workflow_storage.py').read_text(),'workflow_storage','exec'),ns)
t=ast.parse((N/'real_pilot_storage.py').read_text());t.body=[n for n in t.body if not isinstance(n,ast.ImportFrom) or not n.level];exec(compile(t,'real_pilot_storage','exec'),ns)
def need(ok,msg):
 if not ok:raise ValueError(msg)
ns.update(require=need,_source_authority_root=lambda ad:ad.source_ok)
def seam(path):
 t=ast.parse(path.read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='admitted');branch=next(n for n in f.body if isinstance(n,ast.If) and ast.unparse(n.test)=="budget.get('schema_version') == 2")
 body=[n for n in branch.body if not isinstance(n,ast.ImportFrom)]
 return compile(ast.Module(body=body,type_ignores=[]),str(path),'exec')
before=(A/'baseline.py').read_bytes();after=(A/'real_pilot_import_caller.py').read_bytes();manifest=json.loads((A/'MANIFEST.json').read_text());assert hashlib.sha256(after).hexdigest()=='c7520b84b2f37cdb2676a26b281bcc3e7488bcbbad118f2f5225035749f117b2';assert after.replace(manifest['literal_after'].encode(),manifest['literal_before'].encode(),1)==before
B=seam(A/'baseline.py');C=seam(A/'real_pilot_import_caller.py');checks=[]
with tempfile.TemporaryDirectory(dir=P) as tmp:
 root=Path(tmp);(root/'research_runs').mkdir();(root/'research_artifacts').mkdir();old=ns['EXPERIMENT'];new='eth-paper-real-data-end-to-end-resource-20261008-22'
 def budget(name):return {'schema_version':2,'kind':ns['KIND'],'authority_root':str(root),'experiment':name,'roots':[str(root/'research_artifacts'),str(root/'research_runs'/name)],'shared_files':[str(root/'research_runs/.lock')],'limits':{'max_allocated_bytes':10**8,'max_logical_bytes':10**8,'max_entries':1000,'max_depth':64,'max_scan_seconds':5}}
 def run(code,name,b,version=2,source_ok=True):exec(code,dict(ns,ad=SimpleNamespace(root=root,experiment_id=name,source_ok=source_ok),budget=b,p={'schema_version':version}))
 run(B,old,budget(old));run(C,old,budget(old));run(C,new,budget(new));checks+=['legacy_same','new_named_join']
 cases=[('baseline_new',B,new,budget(new),2,True),('old_budget',C,new,budget(old),2,True),('bad_name',C,'../x',budget(new),2,True),('bad_type',C,22,budget(new),2,True),('old_schema',C,new,budget(new),1,True),('source_root_refusal',C,new,budget(new),2,False)]
 for field,value in [('roots',[str(root/'research_artifacts'),str(root/'research_runs'/old)]),('authority_root','/wrong'),('shared_files',['/wrong'])]:
  b=budget(new);b[field]=value;cases.append((field,C,new,b,2,True))
 for label,code,name,b,v,s in cases:
  try:run(code,name,b,v,s)
  except ValueError:checks.append(label+'_refused')
  else:raise AssertionError(label)
# Whole-source inverse also establishes unchanged schema, upstream and downstream code.
assert b'    _bind_resources(ad,job,p)' in before
up=(N/'job.py').read_text();assert 'not isinstance(ad,Admission)' in up and 'execution[\'resources\']!=value' in up and 'validate(budget,Path(root),experiment=ad.experiment_id)' in up
result={'status':'SOURCE_ACCEPTED','candidate_sha256':hashlib.sha256(after).hexdigest(),'checks':checks+['whole_source_literal_inverse','upstream_genuine_type_and_resource_join_present'],'scope':'isolated actual branch and actual storage validator on tiny metadata fixtures, no Admission/Run/Owner instance or admission claim'}
(P/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
