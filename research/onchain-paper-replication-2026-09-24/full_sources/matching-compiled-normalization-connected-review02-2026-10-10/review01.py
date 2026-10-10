"""Focused independent lifecycle regression only; no numeric dependencies."""
import ast,builtins,copy,difflib,hashlib,json,os,resource,signal,sys,time,types
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;C=F/'matching-compiled-normalization-connected02-2026-10-10';O=F/'matching-compiled-normalization-connected01-2026-10-10';R=P.parents[3]
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(20,20));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(25)
assert os.sched_getaffinity(0)=={3}
started=time.perf_counter_ns();checks=[];evidence={};observations=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def record(p):
 b=p.read_bytes();evidence[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)};return b
def ok(name,test=True):assert test,name;checks.append(name)
original_import=builtins.__import__
def guarded(name,*a,**kw):
 assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes'},name
 return original_import(name,*a,**kw)
builtins.__import__=guarded
manifest=record(C/'MANIFEST01.json');ok('frozen02 manifest',sha(manifest)=='d309ed04d988e7655628e4d42e6852d7ebc039cf08ef023a247b5dcdaa5dfc55')
for name,ref in json.loads(manifest)['artifacts'].items():
 b=record(C/name);ok('manifest '+name,sha(b)==ref['sha256'] and len(b)==ref['bytes'])
prior=F/'matching-compiled-normalization-connected-review01-2026-10-10';review=record(prior/'REVIEW01.json')
ok('prior WITHHOLD review preserved',sha(review)=='14b7da52e75035d20cdd13b1d99d35e18bbc5f49f400ce452e3bd5cfb7828ef5')
priorrefs=json.loads(review)['body_references']
for name in ('matching_annealing.py','matching_checkpoint.py','batched_pair_executor.py','batched_numeric_execution.py','compiled_normalization_policy.py','compiled_small_lse.py'):
 old=record(O/name);new=(C/name).read_bytes();key=str((O/name).relative_to(R))
 ok('reuse exact prior reviewed '+name,old==new and sha(old)==priorrefs[key]['sha256'])
oldsession=record(O/'matching_immutable_session.py');newsession=(C/'matching_immutable_session.py').read_bytes()
ok('fixed new session digest',sha(newsession)=='7f847b02d2c4ca4e17a0b0962a97c49498b0559268b1187aad682c446eec3460')
a=ast.parse(oldsession);b=ast.parse(newsession)
getclass=lambda t:next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='ImmutablePairSession')
oldmethods={n.name:n for n in getclass(a).body if isinstance(n,ast.FunctionDef)}
for i,n in enumerate(getclass(b).body):
 if isinstance(n,ast.FunctionDef) and n.name in {'__init__','close'}:getclass(b).body[i]=copy.deepcopy(oldmethods[n.name])
ok('exact whole AST inverse outside two methods',ast.dump(a)==ast.dump(b))
oldreuse=record(O/'batched_numeric_reuse.py');newreuse=(C/'batched_numeric_reuse.py').read_bytes();oldhash=sha(oldsession).encode();newhash=sha(newsession).encode()
ok('mandatory session source pin occurs once',newreuse.count(newhash)==1 and oldreuse.count(oldhash)==1)
ok('only source pin changed in reuse',newreuse.replace(newhash,oldhash)==oldreuse)
# Apply the actual unified inverse using independent strict context validation.
def apply(data,patch):
 if not patch:return data
 lines=data.decode().splitlines(True);p=patch.decode().splitlines(True);out=[];cursor=0;i=2
 while i<len(p):
  h=p[i];assert h.startswith('@@ ');pos=int(h.split()[1][1:].split(',')[0])-1;i+=1
  assert cursor<=pos;out.extend(lines[cursor:pos]);cursor=pos
  while i<len(p) and not p[i].startswith('@@ '):
   q=p[i];i+=1
   if q[0] in ' -':assert lines[cursor]==q[1:];cursor+=1
   if q[0] in ' +':out.append(q[1:])
 out.extend(lines[cursor:]);return ''.join(out).encode()
for name in ('matching_annealing.py','matching_checkpoint.py','matching_immutable_session.py','batched_pair_executor.py','batched_numeric_reuse.py','batched_numeric_execution.py'):
 body=(C/name).read_bytes();installed=record(R/'tradingagents/research/onchain_replication'/name)
 ok('installed inverse '+name,apply(body,(C/(name+'.inverse.patch')).read_bytes())==installed==(C/('baseline_'+name)).read_bytes())
 ok('withheld01 inverse '+name,apply(body,(C/(name+'.to01.inverse.patch')).read_bytes())==(O/name).read_bytes())
# Execute actual session class and unchanged actual executor call with fake graph
# metadata functions. Backend owns one ordinary descriptor, no memfd/dlopen.
p=types.ModuleType('policy');exec(compile((C/'compiled_normalization_policy.py').read_text(),'policy','exec'),p.__dict__)
policy=dict(format=p.FORMAT,library_path='/synthetic/lib',library_sha256=p.LIBRARY_SHA256,source_path='/synthetic/source',source_sha256=p.SOURCE_SHA256,runtime_path='/synthetic/runtime',runtime_sha256='d'*64,runtime_bytes=100)
fixture=P/'ordinary-source.txt';fixture.write_bytes(b'lifecycle ordinary descriptor\n')
def run(root,mode):
 events=[];fds=[];sessions=[];acquired=False;mutated=False;once=False;getclose=0
 primary=MemoryError('injected construction or invalidation fatal') if mode.startswith(('constructor','attribute','invalidate')) else KeyboardInterrupt('injected original advance fatal')
 cleanup_error=OSError('ambiguous backend close')
 def noop(*a,**k):return None
 hard=types.SimpleNamespace(check=noop,create=noop,advance=noop)
 ann=types.SimpleNamespace(normalization_policy=noop,_check_state_identity=noop,_advance_checked=noop,validate_pair=noop,identity=lambda *a:{},np=object())
 def advance(state,*a,**kw):
  events.append('advance')
  if mode=='fatal_both_cleanup_errors':raise primary
  state['phase']='done'
 def engine_close(state):
  events.append('engine_close')
  if mode=='fatal_both_cleanup_errors':raise OSError('engine cleanup failed')
 engine=types.SimpleNamespace(ann=ann,hard=hard,np=ann.np,policy=noop,_check_owned=noop,_advance_owned=advance,matrix_identity=noop,create=lambda *a,**kw:{'phase':'annealing'},score_only=lambda *a,**kw:types.SimpleNamespace(score=.25,iterations=2,convergence='iteration_cap'),close=engine_close)
 def open_backend(owner):
  nonlocal acquired,getclose
  if mode=='unselected':events.append('no_backend');return None
  fd=os.open(fixture,os.O_RDONLY);fds.append(fd);events.append('acquire');acquired=True
  def close():
   events.append('owned_close')
   if mode in {'ambiguous_close','fatal_both_cleanup_errors','constructor_primary_close_failure','invalidate_primary_close_failure'}:raise cleanup_error
   os.close(fd)
  class Backend:
   lse=staticmethod(noop)
   def __getattribute__(self,name):
    nonlocal getclose
    if name=='close':
     getclose+=1
     if mode=='constructor_close_lookup_once' and getclose==1:raise primary
     return close
    return object.__getattribute__(self,name)
  return Backend() if mode=='constructor_close_lookup_once' else types.SimpleNamespace(lse=noop,close=close)
 seam=types.SimpleNamespace(attach=p.attach,current=p.current,options=p.options,join=p.join,open_backend=open_backend)
 edge=types.SimpleNamespace(attach=noop,current=noop,options=lambda *a:{},join=noop)
 def tuple_fault(value=()):
  if acquired and mode in {'constructor_memoryerror','constructor_primary_close_failure'}:raise primary
  return tuple(value)
 ns=dict(require=p.require,adaptive_edge_policy=edge,compiled_normalization_policy=seam,config_pin=lambda c:(),graph_pin=lambda g:(),rejoin=noop,MappingProxyType=types.MappingProxyType,tuple=tuple_fault)
 cls=getclass(ast.parse((root/'matching_immutable_session.py').read_bytes()));exec(compile(ast.Module(body=[copy.deepcopy(cls)],type_ignores=[]),'actual-session','exec'),ns)
 Base=ns['ImmutablePairSession']
 class Session(Base):
  def __setattr__(self,key,value):
   nonlocal once
   target={'attribute_normalizer':'_normalizer','attribute_pin':'_normalizer_pin','attribute_functions':'_normalizer_functions','invalidate_primary_close_failure':'closed'}.get(mode)
   if acquired and key==target and not once:once=True;raise primary
   return super().__setattr__(key,value)
 def create_session(*a,**kw):
  s=Session(*a,**kw);sessions.append(s);return s
 def poll():
  nonlocal mutated
  events.append('poll')
  if sessions and not mutated:
   if mode=='normalizer_replaced':sessions[0]._normalizer=None
   if mode=='close_replaced':sessions[0]._normalizer.close=lambda:events.append('wrong_close')
   mutated=True
 pair=types.SimpleNamespace(hash_string=noop,policy_check=noop,LIMIT=16,ENGINE_FIELDS=())
 t=ast.parse((root/'batched_pair_executor.py').read_bytes());cl=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='PairExecutor');call=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='__call__')
 env=dict(adaptive_edge_policy=edge,compiled_normalization_policy=seam,pair=pair,engine=engine,annealing=ann,ImmutablePairSession=create_session,CheckpointStop=RuntimeError)
 exec(compile(ast.Module(body=[copy.deepcopy(call)],type_ignores=[]),'actual-executor','exec'),env)
 obj=types.SimpleNamespace(poisoned=False,authority_poll=poll,config={},policy={'max_checkpoint_bytes':100,'max_score_buffer_bytes':100,'chunk_edges':1},schedule={'max_checkpoints':1,'calls_per_checkpoint':1,'operations_per_call':3,'max_total_checkpoints':1,'max_total_checkpoint_bytes':200},checkpoints=0,reserved_bytes=0,checkpoint=noop)
 p.attach(obj,None if mode=='unselected' else policy)
 error=None
 try:env['__call__'](obj,'a','b','purpose')
 except BaseException as e:error=e
 repeat_errors=[]
 if root==C and sessions:
  # Exercise the actual retained terminal capability three more times.
  for _ in range(3):
   try:sessions[0].close();repeat_errors.append(None)
   except BaseException as e:repeat_errors.append(e)
 live=[]
 for fd in fds:
  try:os.fstat(fd);live.append(fd)
  except OSError:pass
 obs={'version':'01' if root==O else '02','mode':mode,'events':events,'error':None if error is None else {'type':type(error).__name__,'message':str(error),'notes':getattr(error,'__notes__',[])},'primary_identity':error is primary,'cleanup_identity':error is cleanup_error,'executor_poisoned':obj.poisoned,'owned_close_count':events.count('owned_close'),'engine_close_count':events.count('engine_close'),'fds_open_after_candidate':len(live),'repeat_close_error_types':[None if e is None else type(e).__name__ for e in repeat_errors]}
 if root==O:ok('original RED '+mode,error is not None and len(live)==1 and events.count('owned_close')==0 and events.count('engine_close')==1 and obj.poisoned)
 elif mode in {'success','unselected'}:ok('positive '+mode,error is None and not live and events.count('owned_close')==(0 if mode=='unselected' else 1) and events.count('engine_close')==1 and not obj.poisoned and all(e is None for e in repeat_errors))
 elif mode in {'normalizer_replaced','close_replaced'}:ok('successor GREEN '+mode,isinstance(error,ValueError) and not live and events.count('owned_close')==1 and 'wrong_close' not in events and events.count('engine_close')==1 and obj.poisoned)
 elif mode=='ambiguous_close':ok('ambiguous close identity/no retry',error is cleanup_error and len(live)==1 and events.count('owned_close')==1 and events.count('engine_close')==1 and all(e is cleanup_error for e in repeat_errors))
 elif mode in {'fatal_both_cleanup_errors','constructor_primary_close_failure','invalidate_primary_close_failure'}:
  ok('primary and cleanup '+mode,error is primary and len(live)==1 and events.count('owned_close')==1 and events.count('engine_close')==1 and obj.poisoned and len(getattr(error,'__notes__',[]))==(2 if mode=='fatal_both_cleanup_errors' else 1))
  if repeat_errors:ok('retained ambiguous close no retry '+mode,all(e is cleanup_error for e in repeat_errors))
 else:ok('constructor ownership '+mode,error is primary and not live and events.count('owned_close')==1 and events.count('engine_close')==1 and obj.poisoned)
 # Harness-only closure of original01 and deliberately ambiguous fake descriptors.
 for fd in live:os.close(fd)
 obs['harness_residual_closes']=len(live);observations.append(obs)
 (P/(obs['version']+'-'+mode+'.json')).write_text(json.dumps(obs,indent=2)+'\n')
for mode in ('normalizer_replaced','close_replaced','constructor_memoryerror'):run(O,mode)
for mode in ('normalizer_replaced','close_replaced','constructor_memoryerror','attribute_normalizer','attribute_pin','attribute_functions','constructor_close_lookup_once','constructor_primary_close_failure','fatal_both_cleanup_errors','ambiguous_close','invalidate_primary_close_failure','success','unselected'):run(C,mode)
ok('no prohibited imports',not {'numpy','scipy','torch','ctypes'}&set(sys.modules))
ok('frozen02 remains unchanged',record(C/'MANIFEST01.json')==manifest)
result={'decision':'ACCEPT_SOURCE_ONLY_UNINSTALLED','check_count':len(checks),'checks':checks,'lifecycle_cases':len(observations),'observations':observations,'evidence':evidence,'elapsed_ns':time.perf_counter_ns()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'affinity':sorted(os.sched_getaffinity(0)),'ordinary_fd_only':True,'numerical_imports':False,'real_memfd':False,'actual_admission':False,'production_acceptance':False}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('decision','check_count','lifecycle_cases','elapsed_ns','peak_rss_kib')}))
