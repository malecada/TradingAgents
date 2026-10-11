"""Bounded source/AST checks only. No native/scientific imports or live inputs."""
import ast,copy,difflib,hashlib,json,os,resource,signal,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(20)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2]
A=F/'matching-compiled-uncached-edge-chunk01-2026-10-11';G=F/'graph-hash-current-serialization-candidate01-2026-10-11';S=R/'tradingagents/research/onchain_replication'
refs={};checks=[]
def read(p):
 assert not {'.git','.venv','research_artifacts','research_runs','keys','apis'}&set(p.parts)
 assert p.suffix!='.so' and p.stat().st_size<2*1024**2
 b=p.read_bytes();refs[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b.decode()
def ck(v,n):
 checks.append({'name':n,'pass':bool(v)})
 if not v:raise AssertionError(n)
def fn(text,name):return next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
def dump(node):return ast.dump(node,include_attributes=False)
def save(n,v):
 with (P/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
for d in (A,G):
 m=json.loads(read(d/'MANIFEST01.json'))
 for name,row in m['files'].items():
  if name.endswith('.so'):continue
  text=read(d/name);ck(hashlib.sha256(text.encode()).hexdigest()==row['sha256'] and len(text.encode())==row['bytes'],'frozen textual member '+d.name+'/'+name)
old=read(S/'matching_annealing.py');new=read(A/'matching_annealing.py')
ck(hashlib.sha256(old.encode()).hexdigest()==json.loads(read(A/'BASELINE.json'))['sha256'],'exact installed matching baseline')
ot=ast.parse(old);nt=ast.parse(new);of=next(n for n in ot.body if isinstance(n,ast.FunctionDef) and n.name=='_advance_checked');nf=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='_advance_checked')
nt.body[nt.body.index(nf)]=of;ck(dump(nt)==dump(ot),'only private advance AST changed')
ck(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='matching_annealing.py',tofile='matching_annealing.py'))==read(A/'FORWARD.patch'),'literal native forward diff exact')
ck(''.join(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile='matching_annealing.py',tofile='matching_annealing.py'))==read(A/'INVERSE.patch'),'literal native inverse diff exact')
# Execute only the actual changed try/except AST with inert Python objects.
# Adapter allocation/currentness may raise before progress[0] is set.
tries=[n for n in ast.walk(nf) if isinstance(n,ast.Try) and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='native_used' for t in x.targets) for x in n.body)]
ck(len(tries)==1,'single actual changed weight-fill exception region')
actual_try=tries[0]
prefix=ast.parse('def probe():\n native_progress=None\n').body[0];prefix.body.append(actual_try)
env={'edge_chunk_fill':lambda *args:(_ for _ in ()).throw(MemoryError('adapter prefill allocation')), 'reuse':False,'_reuse_runtime':lambda:True,'_immutable_edges':lambda g:True,'a':types.SimpleNamespace(edge_features=None),'b':types.SimpleNamespace(edge_features=None),'weights':None,'left':None,'right':None,'count':8,'agreement':None}
exec(compile(ast.fix_missing_locations(ast.Module(body=[prefix],type_ignores=[])),'actual-new-try-only','exec'),env)
try:env['probe']()
except BaseException as e:actual_error={'type':type(e).__name__,'message':str(e),'context_type':type(e.__context__).__name__,'context_message':str(e.__context__)}
else:raise AssertionError('expected prefill failure')
ck(actual_error['type']=='UnboundLocalError' and actual_error['context_type']=='MemoryError','counterexample: prefill error masked by unbound offset')
# The adapter's actual eligibility path contains two real pre-marker failure sites.
adapter=read(A/'adapter.py');apply=next(n for n in ast.walk(ast.parse(adapter)) if isinstance(n,ast.FunctionDef) and n.name=='apply')
mark=next(i for i,n in enumerate(apply.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='progress' for t in n.targets))
ck(any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='indices' for t in n.targets) for n in apply.body[:mark]),'tuple(range(count)) allocation precedes progress initialization')
ck(any(isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='native' and n.attr=='fill' for st in apply.body[:mark] for n in ast.walk(st)),'native fill attribute currentness lookup precedes progress initialization')
c=read(A/'edge_chunk.c');ck(c.index('PyList_SetItem(progress')<c.index('PyObject_GetItem(left')<c.index('PyObject_GetItem(af')<c.index('PyObject_GetItem(right')<c.index('PyObject_GetItem(bf')<c.index('PyObject_CallFunctionObjArgs')<c.index('PyNumber_Multiply')<c.index('PyObject_SetItem(w'),'C ordered callbacks/progress/write source sequence')
ck('Py_BEGIN_ALLOW_THREADS' not in c and 'count>1024' in c and 'PyLong_AsSsize_t(index)!=i' in c,'C GIL retained and count/index bounds explicit')
fixture=read(A/'fixture01.py');ck('native_calls[0]>0' in fixture and "errors[0][0]=='OverflowError'" in fixture and 'eq(x,y)' in fixture and "progress==[None]" in fixture,'queued fixture covers route hit state equality late error and unsupported no-write')
ck('MemoryError' not in fixture and 'del native.fill' not in fixture,'queued fixture misses pre-progress failure case')
# Shared helper remains the exact accepted02 AST; only graph_hash import changes.
prior=read(F/'authority-current-pins-serialization02-2026-10-11/imported_mcm_identity.py');prior_review=json.loads(read(F/'authority-current-pins-serialization-review02-2026-10-11/REVIEW01.json'))
ck(prior_review['decision']=='ACCEPT_NARROW_SERIALIZER02_FUNCTIONAL_SOURCE_CORRECTION','accepted02 source review reused')
gp=read(G/'provenance.py');gn=read(G/'neighborhoods.py');op=read(S/'provenance.py');on=read(S/'neighborhoods.py')
h=fn(gp,'current_canonical_bytes');h.name='_current_bytes';ck(dump(h)==dump(fn(prior,'_current_bytes')),'shared helper exact accepted02 AST name-only')
pt=ast.parse(gp);pt.body=[n for n in pt.body if not(isinstance(n,ast.FunctionDef) and n.name=='current_canonical_bytes')];ck(dump(pt)==dump(ast.parse(op)),'provenance whole AST helper-only insertion')
nt=ast.parse(gn);gf=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='graph_hash');imp=next(n for n in gf.body if isinstance(n,ast.ImportFrom) and n.module=='provenance');ck([(n.name,n.asname) for n in imp.names]==[('current_canonical_bytes','canonical_bytes')],'only selected graph local serializer')
imp.names=[ast.alias(name='canonical_bytes')];ck(dump(nt)==dump(ast.parse(on)),'entire graph AST inverse preserves validation/traversal/framing/order')
helper=ast.get_source_segment(gp,fn(gp,'current_canonical_bytes'));ck(gp.replace('\n\n'+helper+'\n','',1)==op and gn.replace('from .provenance import current_canonical_bytes as canonical_bytes','from .provenance import canonical_bytes',1)==on,'both graph candidate literal inverses exact')
ns={'json':json};nodes=[n for n in ast.parse(gp).body if isinstance(n,ast.FunctionDef) and n.name in {'thaw','canonical_bytes','current_canonical_bytes'}];exec(compile(ast.Module(body=nodes,type_ignores=[]),'pure-serializer-only','exec'),ns)
base=ns['canonical_bytes'];fast=ns['current_canonical_bytes']
def outcome(f,v):
 try:return ['bytes',f(v).hex()]
 except Exception as e:return [type(e).__name__,str(e)]
values=[{'μ':[0,-0.0,True,None,2**90]},[[],[1,2]],types.MappingProxyType({'x':(1,2)}),{1:'x'},['\ud800'],[float('nan')]]
for i,v in enumerate(values):ck(outcome(base,v)==outcome(fast,v),'new graph chunk canonical byte/error boundary '+str(i))
v=[[1,2],[3,4]];before=fast(v);v[1][1]=5;ck(fast(v)==base(v)!=before,'fresh chunk mutation changes identity');v[1][1]=4;ck(fast(v)==before,'restoration returns original bytes')
result={'decision':'SPLIT_SOURCE_REVIEW_GRAPH_ACCEPTED_NATIVE_REFUSED_PENDING_FIX','checks':checks,'references':refs,'native_counterexample':actual_error,'native_finding':{'severity':'P2','path':str((A/'matching_annealing.py').relative_to(R)),'lines':[233,235,250,253],'impact':'An adapter error before progress is recorded is replaced by UnboundLocalError on a first chunk; a stale offset from a prior fallback chunk may instead replay the wrong prefix. Actual adapter indices tuple allocation and native.fill lookup occur before progress[0]=0.','fix':'Initialize the current chunk offset/progress to zero before invoking eligibility/filler code, and consume native progress only for the current fill. Preserve the original prefill exception; add a queued pre-progress failure/prefix fixture.'},'graph_scope':'Narrow shared helper and graph_hash caller source acceptance only. Exact accepted02 helper reused; no other graph AST change.','native_scope':'Source/compile candidate remains uninstalled; normal ordered C arithmetic sequence appears consistent, but prefill error path requires correction.','withheld':['native numerical/equivalence and ABI loading proof','full real ndarray/dataclass graph equivalence','allocation/asynchronous/concurrent mutation universal equivalence','performance or memory savings','loaded-source authentication and genuine Owner/caller admission','installation or active pilot source changes'],'runtime_envelope':{'cpu_affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'cpu_seconds':10,'as_bytes':512*1024**2,'file_bytes':4*1024**2},'native_executed':False,'scientific_imports':False}
save('REVIEW01.json',result);print(json.dumps({'decision':result['decision'],'checks':len(checks),'counterexample':actual_error,'review_sha256':hashlib.sha256((P/'REVIEW01.json').read_bytes()).hexdigest()},sort_keys=True))
