import ast,copy,hashlib,json,os,resource,signal,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(20)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'pilot34-shared-serialization-integration01-2026-10-11';A=F/'authority-current-pins-serialization02-2026-10-11';G=F/'graph-hash-current-serialization-candidate01-2026-10-11';refs={};checks=[]
def read(p):
 assert not ({'.git','.venv','research_artifacts','research_runs','keys','apis'}&set(p.parts))
 b=p.read_bytes();assert len(b)<2*1024**2;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b.decode()
def ck(v,n):
 checks.append({'name':n,'pass':bool(v)})
 if not v:raise AssertionError(n)
def dump(v):return ast.dump(v,include_attributes=False)
m=json.loads(read(D/'MANIFEST01.json'));ck(refs[str((D/'MANIFEST01.json').relative_to(R))]['sha256']=='ec60b4f8c27c0e344955f331c567f1f54daac65157c83e401214ccafeb55bd49','exact shared candidate manifest')
for name,row in m['files'].items():s=read(D/name);ck(hashlib.sha256(s.encode()).hexdigest()==row['sha256'] and len(s.encode())==row['bytes'],'frozen shared textual member '+name)
for name in ('provenance.py','neighborhoods.py'):ck(read(D/name)==read(G/name),'exact unchanged accepted graph source '+name)
accepted=read(A/'imported_mcm_identity.py');current=read(R/'tradingagents/research/onchain_replication/imported_mcm_identity.py');combined=read(D/'imported_mcm_identity.py');at=ast.parse(accepted);ct=ast.parse(combined)
helper=next(n for n in at.body if isinstance(n,ast.FunctionDef) and n.name=='_current_bytes');at.body.remove(helper)
for n in ast.walk(at):
 if isinstance(n,ast.Name) and n.id=='_current_bytes':n.id='current_canonical_bytes'
for n in at.body:
 if isinstance(n,ast.ImportFrom) and n.module=='provenance':n.names.append(ast.alias(name='current_canonical_bytes'))
ck(dump(at)==dump(ct),'entire accepted adapter AST changes only shared helper relocation/import')
ck(combined.replace(',current_canonical_bytes\n','\n',1).replace('current_canonical_bytes(', 'canonical_bytes(')==current,'exact literal inverse to current frozen adapter')
calls=[n for n in ast.walk(ct) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='current_canonical_bytes'];target=next(n for n in ct.body if isinstance(n,ast.ClassDef) and n.name=='Target');pins=next(n for n in target.body if isinstance(n,ast.FunctionDef) and n.name=='_pins')
ck(len(calls)==3 and all(n in list(ast.walk(pins)) for n in calls),'only three existing pins calls share helper')
pt=ast.parse(read(D/'provenance.py'));shared=next(n for n in pt.body if isinstance(n,ast.FunctionDef) and n.name=='current_canonical_bytes');renamed=copy.deepcopy(shared);renamed.name='_current_bytes';ck(dump(renamed)==dump(helper),'shared definition identical to accepted helper')
ns={'json':json};nodes=[n for n in pt.body if isinstance(n,ast.FunctionDef) and n.name in ('canonical_bytes','thaw','current_canonical_bytes')];exec(compile(ast.Module(body=nodes,type_ignores=[]),'shared-stdlib-only','exec'),ns)
def require(ok,msg):
 if not ok:raise ValueError(msg)
calls_seen=[]
def route(v):calls_seen.append(v);return ns['current_canonical_bytes'](v)
env={'require':require,'current_canonical_bytes':route};exec(compile(ast.Module(body=[pins],type_ignores=[]),'pins-shared-routing-only','exec'),env)
n=types.SimpleNamespace;owner=object();dictionary=object();graph=object();mapping={'graph':'input'};stage=n(reference='receipt',prepared=n(_selection={'selected':{'descriptor':{'resource_graph_inputs':mapping}}}));execution=n(_owner=owner,_materialized=n(_dictionary=dictionary),_stage=stage)
t=n(execution=execution,graph=graph,owner=owner,dictionary=dictionary,receipt_sha256='receipt',key='graph',_input='input',_execution=types.MappingProxyType({'nested':[1,2]}),scope={'edge':(1,2)},_arrays=lambda:())
t._objects=(id(execution),id(graph),id(owner),id(dictionary),());t._mapping=ns['canonical_bytes'](mapping);t._execution_pin=ns['canonical_bytes'](t._execution);t._scope_pin=ns['canonical_bytes'](t.scope)
env['_pins'](t);ck(len(calls_seen)==3 and all(a is b for a,b in zip(calls_seen,(mapping,t._execution,t.scope))),'actual shared route sees original mapping/execution/scope in order')
calls_seen.clear();t._execution['nested'].append(3)
try:env['_pins'](t)
except ValueError as e:ck(str(e)=='target execution/workload changed' and len(calls_seen)==2,'frozen wrapper nested mutation refuses before scope serialization')
else:raise AssertionError('mutation must refuse')
t._execution['nested'].pop();calls_seen.clear();env['_pins'](t);ck(len(calls_seen)==3,'restoration reserializes all three originals')
original=MemoryError('shared serialization failed')
def fail(v):raise original
env['current_canonical_bytes']=fail
try:env['_pins'](t)
except BaseException as e:ck(e is original,'shared serializer primary exception identity preserved')
else:raise AssertionError('must preserve serialization error')
out={'decision':'ACCEPT_NARROW_SHARED_HELPER_RELOCATION_SOURCE_ONLY','checks':checks,'references':refs,'source_hashes':{name:m['files'][name]['sha256'] for name in ('provenance.py','neighborhoods.py','imported_mcm_identity.py')},'scope':'Single shared exact accepted02 helper; existing three pin calls and graph caller reuse only. Original object routing, fallback nested mutation refusal, restoration and primary exception identity checked through extracted stdlib functions.','limits':['No genuine Target/Owner/Lease instantiated; inert scalar metadata objects only.','Actual graph/native/runtime/source authenticity, loaded callable currentness, caller admission, numerical equivalence, performance/capacity and installation remain unproved.','Concurrent mutation, replaced encoder instrumentation and allocation timing equivalence retain prior limitations.','Prior C28 operator _serial/compiler-source authority limitation is unchanged.']}
with (P/'SHARED_SOURCE_REVIEW01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'decision':out['decision'],'checks':len(checks),'sha256':hashlib.sha256((P/'SHARED_SOURCE_REVIEW01.json').read_bytes()).hexdigest()},sort_keys=True))
