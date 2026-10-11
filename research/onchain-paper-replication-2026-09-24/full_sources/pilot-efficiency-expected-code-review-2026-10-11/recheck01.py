import ast,hashlib,json,resource,os,signal,difflib
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
H=Path(__file__).resolve().parent;R=H.parents[3];C=H.parent/'authority-expected-code-cache-candidate02-2026-10-11';D=R/'tradingagents/research/onchain_replication'
requirements=json.loads((C/'SOURCE_REQUIREMENTS02.json').read_bytes());checks=[];forward=[];inverse=[]
def ck(value,name):
 if not value:raise AssertionError(name)
 checks.append(name)
for name in ('imported_authority_lease.py','real_pilot_import_caller.py'):
 old=(D/name).read_text();new=(C/name).read_text();rel=str((D/name).relative_to(R));row=requirements[rel]
 ck(hashlib.sha256(old.encode()).hexdigest()==row['baseline_sha256'],'current baseline '+name)
 ck(hashlib.sha256(new.encode()).hexdigest()==row['candidate_sha256'],'candidate pin '+name)
 ast.parse(new)
 forward.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=rel,tofile=name));inverse.extend(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile=name,tofile=rel))
ck(''.join(forward)==(C/'LITERAL_PATCH02.diff').read_text(),'forward current exact')
ck(''.join(inverse)==(C/'LITERAL_INVERSE02.diff').read_text(),'inverse current exact')
oldtree=ast.parse((D/'imported_authority_lease.py').read_text());tree=ast.parse((C/'imported_authority_lease.py').read_text())
def find(t,n):return next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==n)
ck(ast.dump(find(tree,'_authenticate_loaded'))==ast.dump(find(oldtree,'_authenticate_loaded')),'default authenticator identical')
def require(v,s):
 if not v:raise ValueError(s)
nodes=[x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED_POLICY' for t in x.targets) or isinstance(x,ast.FunctionDef) and x.name=='expected_code_policy']
ns={'require':require};exec(compile(ast.Module(body=nodes,type_ignores=[]),'policy-extraction','exec'),ns)
p=json.loads((C/'POLICY02.json').read_bytes());ck(ns['expected_code_policy'](None) is None,'default None');ck(ns['expected_code_policy'](p)==tuple(sorted(p.items())),'exact opted contract')
for k,v in [('schema_version',True),('max_loaded_modules',2049),('assumption','universal hook equivalence')]:
 bad=dict(p);bad[k]=v
 try:ns['expected_code_policy'](bad)
 except ValueError:checks.append('refusal '+k)
 else:raise AssertionError(k)
result={'status':'AUTHOR_RECHECK_ONLY_NOT_INDEPENDENT_ACCEPTANCE','checks':checks,'count':len(checks),'measured_speedup':None,'numerical_or_authority_execution':False,'prior_36_mutation_controls':'reused, not rerun','manifest_self_entry_issue':'historical MANIFEST02 lists itself as empty; actual external manifest hash required'}
with (H/'RESULT01.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
