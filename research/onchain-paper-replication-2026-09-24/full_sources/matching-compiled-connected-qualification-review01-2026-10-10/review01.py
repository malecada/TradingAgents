"""Qualification entry/source review only; never calls execute or science APIs."""
import ast,builtins,hashlib,importlib.util,inspect,json,os,resource,signal,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;Q=F/'matching-compiled-connected-qualification01-2026-10-10';C=F/'matching-compiled-normalization-connected02-2026-10-10';R=P.parents[3]
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(15,15));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(20)
assert os.sched_getaffinity(0)=={3}
started=time.perf_counter_ns();checks=[];evidence={};observations={}
def sha(b):return hashlib.sha256(b).hexdigest()
def body(p):
 b=p.read_bytes();evidence[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def ok(name,value=True):assert value,name;checks.append(name)
original_import=builtins.__import__
def guarded(name,*a,**kw):
 assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes','tradingagents'},'review prohibited import '+name
 return original_import(name,*a,**kw)
builtins.__import__=guarded
manifest=body(Q/'MANIFEST01.json');ok('frozen harness manifest',sha(manifest)=='1f22a56607ae914ba044c91e00bc550f536a34f44837af565f45a5ade6b4897b')
for name,ref in json.loads(manifest)['artifacts'].items():
 b=body(Q/name);ok('artifact '+name,len(b)==ref['bytes'] and sha(b)==ref['sha256'])
source=(Q/'qualify.py').read_bytes();ok('exact qualification script',sha(source)=='92bcfd69ad6e697dfcf916218519475ab07c71710751444a1a0f836b4859a52f')
prior=F/'matching-compiled-normalization-connected-review02-2026-10-10/REVIEW01.json';ok('reuse exact connected02 review',sha(body(prior))=='99138c00824f25bc6c6ac89abc2380bd1a9248fe15ecd8ac0616ad6bb890fc2d')
req=json.loads((Q/'SOURCE_REQUIREMENTS.json').read_bytes());cases=json.loads((Q/'CASES.json').read_bytes())
ok('connected02 exact manifest',sha(body(C/'MANIFEST01.json'))==req['candidate02_manifest_sha256'])
for name,digest in req['installed_module_sha256'].items():ok('future installed pin '+name,sha(body(C/name))==digest)
ok('eight connected files required',len(req['installed_module_sha256'])==8)
config=body(R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json');ok('unchanged frozen scientific configuration',config==(Q/'matching-config.json').read_bytes())
# Load only the actual stdlib entry definitions; no fake source/runtime inventory.
spec=importlib.util.spec_from_file_location('reviewed_qualification',Q/'qualify.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
frozen=q.inputs();ok('actual frozen input parser',frozen['CASES.json']==cases)
try:q.preflight(R,P/'ABSENT_RUNTIME_POLICY.json')
except ValueError as e:
 observations['actual_preflight_refusal']={'type':type(e).__name__,'message':str(e)}
 ok('current uninstalled baseline refuses before absent policy',str(e).startswith('exact input/source SHA256 differs:') and 'matching_annealing.py' in str(e))
else:raise AssertionError('uninstalled candidate admitted')
# A real bounded metadata read/refusal, without constructing a policy or layout.
fixture=P/'read-only-fixture.txt';fixture.write_bytes(b'bounded ordinary metadata\n')
ok('actual read exact body',q.read(fixture.resolve(),128,sha(fixture.read_bytes()))==fixture.read_bytes())
for label,fn in [('wrong digest',lambda:q.read(fixture.resolve(),128,'0'*64)),('oversize',lambda:q.read(fixture.resolve(),1)),('relative',lambda:q.read(Path('relative'),128))]:
 try:fn()
 except ValueError:ok('actual read refuses '+label)
 else:raise AssertionError(label)
# Full entry and nested API argument compatibility from actual AST/signatures.
t=ast.parse(source);top={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)};ex=top['execute'];nested={n.name:n for n in ex.body if isinstance(n,ast.FunctionDef)}
def src(n):return ast.unparse(n)
for n in t.body:
 if isinstance(n,(ast.Import,ast.ImportFrom)):
  names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module]
  ok('top-level imports stdlib line'+str(n.lineno),not any(x.split('.')[0] in {'numpy','scipy','torch','ctypes','tradingagents'} for x in names))
main_text=src(top['main']);pre_text=src(top['preflight']);ex_text=src(ex)
ok('main actual preflight precedes execute',main_text.index('preflight(CHECKOUT')<main_text.index('execute(args.output'))
ok('flag absent returns only metadata',"if not args.execute_after_terminal:" in main_text and "SOURCE_METADATA_PREFLIGHT_ONLY" in main_text)
ok('CLI has all declared arguments',all(x in main_text for x in ('--runtime-policy','--output','--execute-after-terminal')))
first_import=next(i for i,n in enumerate(ex.body) if isinstance(n,ast.Import) and any(a.name=='numpy' for a in n.names))
prefix='\n'.join(src(n) for n in ex.body[:first_import])
ok('limits fresh process threads output predate scientific imports',all(s in prefix for s in ('sched_setaffinity','setrlimit','signal.alarm','fresh standalone process required','OPENBLAS_NUM_THREADS','not output.exists()','PREFLIGHT.json')))
ok('eight sources precede metadata parser and runtime policy',pre_text.index("requirements['installed_module_sha256']")<pre_text.index('spec_from_file_location')<pre_text.index('policy = json.loads'))
ok('runtime C/library/reference checked with existing parser',all(s in pre_text for s in ('module.freeze(policy)',"policy['source_path']","policy['library_path']",'module.runtime_metadata')))
ok('loaded module paths and bodies rejoined',"Path(module.__file__).resolve() == expected" in ex_text and 'read(expected, 65536, digest)' in ex_text)
# Reconstruct callable signatures from AST only, using opaque placeholder defaults.
def signature(path,name,cls=None):
 tr=ast.parse(body(path));nodes=tr.body
 if cls:nodes=next(n for n in nodes if isinstance(n,ast.ClassDef) and n.name==cls).body
 n=next(n for n in nodes if isinstance(n,ast.FunctionDef) and n.name==name);a=n.args;pos=list(a.posonlyargs)+list(a.args)
 defaults=[inspect.Parameter.empty]*(len(pos)-len(a.defaults))+[object()]*len(a.defaults);pars=[]
 for x,d in zip(pos,defaults):
  if cls and x.arg=='self':continue
  pars.append(inspect.Parameter(x.arg,inspect.Parameter.POSITIONAL_ONLY if x in a.posonlyargs else inspect.Parameter.POSITIONAL_OR_KEYWORD,default=d))
 if a.vararg:pars.append(inspect.Parameter(a.vararg.arg,inspect.Parameter.VAR_POSITIONAL))
 for x,d in zip(a.kwonlyargs,a.kw_defaults):pars.append(inspect.Parameter(x.arg,inspect.Parameter.KEYWORD_ONLY,default=inspect.Parameter.empty if d is None else object()))
 if a.kwarg:pars.append(inspect.Parameter(a.kwarg.arg,inspect.Parameter.VAR_KEYWORD))
 return inspect.Signature(pars)
allcalls=[n for n in ast.walk(ex) if isinstance(n,ast.Call)]
engine_keys={'max_state_bytes','normalization_chunk_entries','hardening_chunk_entries','hardening_buffer_bytes'}
api=[('engine.create',C/'matching_checkpoint.py','create',None),('engine.save',C/'matching_checkpoint.py','save',None),('engine.load',C/'matching_checkpoint.py','load',None),('engine.result',C/'matching_checkpoint.py','result',None),('engine.close',C/'matching_checkpoint.py','close',None),('sessions.ImmutablePairSession',C/'matching_immutable_session.py','__init__','ImmutablePairSession'),('numeric.NumericExecution',C/'batched_numeric_execution.py','__init__','NumericExecution'),('numeric.verify',C/'batched_numeric_execution.py','verify',None),('policy_module.open_backend',C/'compiled_normalization_policy.py','open_backend',None)]
for expression,path,name,cls in api:
 calls=[c for c in allcalls if src(c.func)==expression];ok('genuine API present '+expression,bool(calls));sig=signature(path,name,cls)
 for i,c in enumerate(calls):
  keys={k.arg for k in c.keywords if k.arg is not None}
  for k in c.keywords:
   if k.arg is None:
    assert src(k.value)=='engine_options';keys|=engine_keys
  sig.bind(*[object() for _ in c.args],**{k:object() for k in keys});ok('actual argument signature '+expression+str(i))
# The graph contract, rather than a fake normalizer, owns immutable byte buffers.
contracts=ast.parse(body(R/'tradingagents/research/onchain_replication/contracts.py'));graph=next(n for n in contracts.body if isinstance(n,ast.ClassDef) and n.name=='AttributedGraph')
ok('genuine graph freezes array buffers',"np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(array.shape)" in src(graph))
ok('selected and default direct sessions',"for selection in (None, selected):" in ex_text)
ok('selected and default full numeric route',"for label, selection in (('default', None), ('selected', selected)):" in ex_text)
ok('genuine callback and finish verification',all(s in ex_text for s in ('executor.finish()', 'numeric.verify(root, binding)', 'digest = checkpoint(state, cp /',"binding['computed'] == len(population)","binding['reused'] == len(population)")))
ok('no fabricated authority selection',all(s in ex_text for s in ('authority_poll=None','binding_timing=None','binding_owner=None')))
ok('no sourceguard mutation',not any(isinstance(n,(ast.Assign,ast.AnnAssign)) and any(isinstance(x,ast.Attribute) and isinstance(x.value,ast.Name) and x.value.id in {'engine','annealing','sessions','numeric','policy_module'} for x in ast.walk(n)) for n in ast.walk(ex)))
kernel=src(nested['kernel_backend']);closed=src(nested['closed_fd'])
ok('actual native FD body seal proof',all(s in kernel for s in ('inspect.getclosurevars',"closure['_fn'] is not None",'os.fstat(fd)','seals == 15','os.pread(fd, 65537, 0)','errno.EPERM','os.ftruncate')))
ok('actual post-close EBADF requirement','errno.EBADF' in closed and 'owned descriptor still open' in closed)
ok('strict primitive state assignment score checks',all(s in ex_text for s in ('actual.tobytes() == original.tobytes()','state_equal(*states)','used[0] == used[1]','left.assignment.tobytes() == right.assignment.tobytes()','left.soft_assignment.tobytes() == right.soft_assignment.tobytes()','score(left) == score(right)')) and not any(s in ex_text for s in ('allclose','isclose')))
ok('required checkpoint phases counted and loaded',"roundtrips == cases['max_direct_checkpoints_per_pair']" in ex_text and 'engine.load(' in ex_text and "states[0]['phase'] == 'hardening'" in ex_text and "states[0]['phase'] == 'done'" in ex_text)
ok('failure never converted to success',"record['status'] = 'FAILED_OR_UNAVAILABLE'" in ex_text and 'raise' in src(next(n for n in ex.body if isinstance(n,ast.Try)).handlers[0]) if any(isinstance(n,ast.Try) for n in ex.body) else False)
ok('finite declared population and controls',[(c['n'],c['m']) for c in cases['graph_cases']]==[(3,3),(2,4),(5,3),(2,2)] and len(cases['primitive_cases'])==4 and cases['max_advances_per_pair']==4096 and cases['max_direct_checkpoints_per_pair']==3 and cases['max_numeric_checkpoints_per_route']==32 and cases['numeric_repeats']==2 and cases['cpu_seconds']==120 and cases['wall_seconds']==180 and cases['address_space_bytes']==3*1024**3 and cases['per_file_bytes']==4*1024**2)
# Verify bounds of the actual literal matching policies, no array operations.
def literal_dict_assignment(name):
 n=next(n for n in ex.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets));return {k.arg:ast.literal_eval(k.value) for k in n.value.keywords}
pair=literal_dict_assignment('pair_policy');conf=json.loads(config)
for case in cases['graph_cases']:
 n,m=case['n'],case['m'];ok('actual engine policy bounds '+case['name'],pair['normalization_chunk_entries']>=max(m,n if m==1 else 2*n) and pair['max_state_bytes']>=32*n*m and pair['max_checkpoint_bytes']>=32*n*m+512+3*65536 and pair['max_score_buffer_bytes']>=80*min(n,m)+32*min(pair['chunk_edges'],m))
ok('post-terminal and admission remain explicit external preconditions',"Root admission and pilot terminal status remain external preconditions" in pre_text and cases['post_terminal_only'] is True)
ok('no prohibited package imported',not {'numpy','scipy','torch','ctypes','tradingagents'}&set(sys.modules))
result={'decision':'ACCEPT_SOURCE_ENTRY_ONLY_UNEXECUTED','check_count':len(checks),'checks':checks,'observations':observations,'evidence':evidence,'elapsed_ns':time.perf_counter_ns()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'affinity':sorted(os.sched_getaffinity(0)),'numerical_execute_called':False,'valid_runtime_policy_supplied':False,'actual_admission':False,'sourceguard_patched':False,'main_integration':False}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('decision','check_count','elapsed_ns','peak_rss_kib')}))
