"""One finite stdlib synthetic-module check. No real Lease/Owner/Run."""
import ast,builtins,contextlib,copy,difflib,hashlib,json,os,resource,signal,sys,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10);resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
H=Path(__file__).resolve().parent;R=H.parents[3];D=R/'tradingagents/research/onchain_replication';checks=[]
def ck(v,n):assert v,n;checks.append(n)
def require(v,n):
 if not v:raise ValueError(n)
def refuse(f,n):
 try:f()
 except ValueError:ck(True,n)
 else:raise AssertionError(n)
def named(tree,name):return next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
old=(D/'imported_authority_lease.py').read_text();new=(H/'imported_authority_lease.py').read_text();ot=ast.parse(old);nt=ast.parse(new)
ck(ast.dump(named(ot,'_authenticate_loaded'))==ast.dump(named(nt,'_authenticate_loaded')),'default authenticator exact original AST')
for n in ('_loaded','_checked_value','check','target_lease'):
 # First check is Lease.check in both, module check also separately compared below.
 ck(ast.dump(named(ot,n))==ast.dump(named(nt,n)),'unchanged '+n)
for text in H.glob('*.py'):ast.parse(text.read_text())
req=json.loads((H/'SOURCE_REQUIREMENTS02.json').read_bytes());patch=[];inverse=[]
for n in ('imported_authority_lease.py','real_pilot_import_caller.py'):
 a=(D/n).read_text();b=(H/n).read_text();path=str((D/n).relative_to(R));ck(hashlib.sha256(a.encode()).hexdigest()==req[path]['baseline_sha256'] and hashlib.sha256(b.encode()).hexdigest()==req[path]['candidate_sha256'],'exact two bodies '+n)
 patch.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=path,tofile=n));inverse.extend(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile=n,tofile=path))
ck(''.join(patch)==(H/'LITERAL_PATCH02.diff').read_text() and ''.join(inverse)==(H/'LITERAL_INVERSE02.diff').read_text(),'full two-file literal inverse')
names={'_loaded','_authenticate_loaded','expected_code_policy','_expected_context','_expected_current','_authenticate_expected'}
assigns={'AUTHORITY_CLASSES','EXPECTED_POLICY','_EXPECTED_COMPILE'}
nodes=[n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in assigns for t in n.targets)]
ns=dict(contextlib=contextlib,hashlib=hashlib,json=json,sys=sys,types=types,Path=Path,builtins=builtins,require=require)
exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-extracted-authenticator','exec'),ns)
policy=json.loads((H/'POLICY02.json').read_bytes());selected=ns['expected_code_policy'](policy)
ck(ns['expected_code_policy'](None) is None,'None remains unselected')
for key,value in [('assumption','hooks absent'),('max_loaded_modules',2049),('schema_version',True)]:
 bad=dict(policy);bad[key]=value;refuse(lambda:ns['expected_code_policy'](bad),'policy refuses '+key)
fixture=H/'ordinary_source03.py';body=b'def twice(x):\n    return x + x\n'
with fixture.open('xb') as f:f.write(body)
name='_ordinary_expected_code_fixture03';mod=types.ModuleType(name);mod.__file__=str(fixture);exec(compile(body,str(fixture),'exec',dont_inherit=True,optimize=sys.flags.optimize),mod.__dict__);sys.modules[name]=mod
sources={fixture.name:hashlib.sha256(body).hexdigest()};loaded=ns['_loaded'](H,sources);ck(list(loaded)==[name],'single ordinary loaded fixture only')
lease=types.SimpleNamespace(loaded=loaded,sources=sources,run=types.SimpleNamespace(admission=types.SimpleNamespace(root=H)),_expected_policy=selected,_expected_policy_pin=selected,_expected_tables=None,_expected_tables_pin=None)
lease._expected_context=lease._expected_context_pin=ns['_expected_context'](lease,selected)
events=[];mode={'reject_second':False};primary=RuntimeError('second compile audit refusal')
def hook(event,args):
 if event=='compile' and len(args)>1 and args[1]==str(fixture):
  events.append(args[1])
  if mode['reject_second'] and len(events)==2:raise primary
sys.addaudithook(hook)
ns['_authenticate_loaded'](loaded,sources,H);ns['_authenticate_loaded'](loaded,sources,H);ck(len(events)==2,'default two auth calls compile twice')
events.clear();lease._expected_tables=lease._expected_tables_pin=ns['_authenticate_expected'](lease);result=ns['_authenticate_expected'](lease)
ck(len(events)==1 and result is lease._expected_tables,'selected two auth calls compile once per module')
ck(type(result) is tuple and type(result[0][2]) is types.MappingProxyType and all(type(v) is tuple and all(type(c) is types.CodeType for c in v) for v in result[0][2].values()),'immutable exact expected code tables')
try:result[0][2]['x']=()
except TypeError:ck(True,'table mapping immutable')
else:raise AssertionError('mapping mutable')
# Real fresh read/hash detects mutated bytes even though expected code remains.
fixture.write_bytes(body.replace(b'x + x',b'x - x'))
try:refuse(lambda:ns['_authenticate_expected'](lease),'source byte mutation refused before reuse')
finally:fixture.write_bytes(body)
for attr,value in [('_expected_tables',tuple(list(lease._expected_tables))),('_expected_policy',tuple(list(selected))),('_expected_context',tuple(list(lease._expected_context)))]:
 saved=getattr(lease,attr);setattr(lease,attr,value)
 try:refuse(lambda:ns['_authenticate_expected'](lease),'replacement refused '+attr)
 finally:setattr(lease,attr,saved)
saved=mod.twice.__code__;mod.twice.__code__=saved.replace()
try:refuse(lambda:ns['_authenticate_expected'](lease),'equal but different loaded code identity refused')
finally:mod.twice.__code__=saved
savedfn=mod.twice;mod.twice=types.FunctionType(saved,mod.__dict__,'twice');mod.twice.__module__=name
try:refuse(lambda:ns['_authenticate_expected'](lease),'replaced loaded function refused before reuse')
finally:mod.twice=savedfn
compiler=builtins.compile;builtins.compile=lambda *a,**k:None
try:refuse(lambda:ns['_authenticate_expected'](lease),'replaced compiler refused')
finally:builtins.compile=compiler
lease.sources[fixture.name]='0'*64
try:refuse(lambda:ns['_authenticate_expected'](lease),'changed source digest scope refused')
finally:lease.sources[fixture.name]=hashlib.sha256(body).hexdigest()
# Deliberately material auxiliary deviation, not a universal equivalence claim.
events.clear();mode['reject_second']=True
ns['_authenticate_loaded'](loaded,sources,H)
try:ns['_authenticate_loaded'](loaded,sources,H)
except BaseException as error:ck(error is primary,'default retains second compile hook refusal identity')
else:raise AssertionError('default hook missing')
events.clear();lease._expected_tables=lease._expected_tables_pin=None;lease._expected_tables=lease._expected_tables_pin=ns['_authenticate_expected'](lease);ns['_authenticate_expected'](lease)
ck(len(events)==1,'selected explicitly omits second audit event/refusal')
mode['reject_second']=False
# A separate activation-owned context compiles again, not process cache.
lease2=types.SimpleNamespace(**vars(lease));lease2._expected_tables=lease2._expected_tables_pin=None;lease2._expected_context=lease2._expected_context_pin=ns['_expected_context'](lease2,selected)
events.clear();lease2._expected_tables=lease2._expected_tables_pin=ns['_authenticate_expected'](lease2);ck(len(events)==1 and lease2._expected_tables is not lease._expected_tables,'separate activation has independent compilation and table')
# Actual small input-selector prefix: no genuine producer plan or Admission.
caller=ast.parse((H/'real_pilot_import_caller.py').read_text());plan=named(caller,'validate_plan');prefix=[]
for stmt in plan.body:
 if isinstance(stmt,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='partial' for t in stmt.targets):break
 prefix.append(copy.deepcopy(stmt))
f=ast.parse('def selection(p):\n return None').body[0];f.body=prefix+[ast.Return(ast.Constant(True))];v={'require':require};exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),'actual-selection-prefix','exec'),v)
good={'schema_version':2,'imported_authority_lease_input':'interval','expected_code_cache_input':'expected_code_policy'}
ck(v['selection'](good),'actual distinct registered selector prefix')
for bad in [dict(good,expected_code_cache_input='interval'),dict(good,schema_version=1),{'schema_version':2,'expected_code_cache_input':'cache'}]:refuse(lambda:v['selection'](bad),'actual selector refuses absent/schema/conflicting interval')
ck("expected_code_policy(_read(ad,p['expected_code_cache_input']))" in ast.unparse(caller).replace(' ','' ) if False else "expected_code_policy(_read(ad,p['expected_code_cache_input']))" in (H/'real_pilot_import_caller.py').read_text(),'admitted policy input read wired')
ck("expected=expected_code_policy(json.loads(run.read_input(role)))" in new and "expected_policy':dict(expected)" in new,'actual activation genuine read and policy forwarding')
ck('_authenticate_expected(self)' in ast.unparse(named(nt,'_full')) and '_expected_current(self, check_scope=True)' in ast.unparse(named(nt,'_finger')),'full reuse and fingerprint currentness wired')
ck('_expected_current(self, check_scope=True)' not in ast.unparse(named(nt,'_identity')) and 'if not check_scope:' in ast.unparse(named(nt,'_expected_current')), 'lightweight identity avoids extra full-roster scan')
with (H/'RESULT03.json').open('x') as f:json.dump({'status':'FINITE_SOURCE_AND_SYNTHETIC_AUTH_CONTROLS_PASS','checks':checks,'compile_hook_deviation':'Observed selected omission of second compile/refusal is explicit policy behavior, not equivalence.','real_authority_created':False,'scientific_imported':False},f,indent=2);f.write('\n')
sys.modules.pop(name)
print(len(checks),'finite checks passed')
