"""Focused03 RED ->04 GREEN: actual extracted owner/session/executor; ordinary FD."""
import ast,builtins,copy,hashlib,json,os,resource,signal,sys,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'matching-compiled-normalization-connected03-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(20,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(25);assert os.sched_getaffinity(0)=={3}
start=time.perf_counter_ns();checks=[];observations=[]
def ok(name,value=True):assert value,name;checks.append(name)
original_import=builtins.__import__
def guarded(name,*a,**kw):
 assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes','array'},name
 return original_import(name,*a,**kw)
builtins.__import__=guarded
fixture=HERE/'ordinary-source.txt';fixture.write_text('ordinary cleanup descriptor\n')
p=types.ModuleType('policy');exec(compile((HERE/'compiled_normalization_policy.py').read_text(),'policy metadata','exec'),p.__dict__)
policy=dict(format=p.FORMAT,library_path='/fixture/library',library_sha256=p.LIBRARY_SHA256,source_path='/fixture/source',source_sha256=p.SOURCE_SHA256,runtime_path='/fixture/runtime',runtime_sha256='d'*64,runtime_bytes=100)
def extract(root,file,cls,ns,method=None):
 node=next(n for n in ast.parse((root/file).read_text()).body if isinstance(n,ast.ClassDef) and n.name==cls)
 if method:node=next(n for n in node.body if isinstance(n,ast.FunctionDef) and n.name==method)
 exec(compile(ast.Module(body=[copy.deepcopy(node)],type_ignores=[]),str(root/file),'exec'),ns);return ns[method or cls]
def noop(*a,**kw):pass
edge=types.SimpleNamespace(attach=noop,current=noop,options=lambda *a:{},join=noop)
def run(root,mode):
 events=[];fds=[];notes=[];allocation=MemoryError('injected annotation allocation')
 class Primary(KeyboardInterrupt):
  def add_note(self,text):
   notes.append('override')
   if mode=='review_red':raise allocation
   return super().add_note(text)
  def __getattribute__(self,name):
   if name=='__notes__' and mode=='builtin_note_failure':raise allocation
   return super().__getattribute__(name)
 class Cleanup(OSError):
  def __repr__(self):
   if mode in ('repr_primary','two_cleanup_repr','backend_repr'):raise allocation
   return super().__repr__()
 primary=Primary('actual advance primary');engine_error=Cleanup('engine cleanup');session_error=KeyboardInterrupt('session cleanup');backend_error=Cleanup('ambiguous backend cleanup')
 def load(*a):
  fd=os.open(fixture,os.O_RDONLY);fds.append(fd);events.append('open')
  def close():
   events.append('backend_close')
   if mode in ('backend_repr','two_cleanup_repr','backend_fatal'):raise backend_error
   os.close(fd)
  return types.SimpleNamespace(lse=noop,close=close,current=lambda:True,loaded=lambda:True)
 Owner=extract(root,'compiled_normalization_policy.py','BackendOwner',dict(attach=p.attach,current=p.current,join=p.join,require=p.require,_backend_references=lambda o:(policy,types.SimpleNamespace(open_backend=load)),read_reference=noop))
 seam=types.SimpleNamespace(attach=p.attach,current=p.current,options=p.options,join=p.join,BackendOwner=Owner,open_backend=lambda *a:None)
 ann=types.SimpleNamespace(normalization_policy=noop,_check_state_identity=noop,_advance_checked=noop,validate_pair=noop,identity=lambda *a:{},np=object())
 def advance(state,*a,**kw):
  events.append('advance')
  if mode not in ('success','two_cleanup_repr','backend_fatal'):raise primary
  state['phase']='done'
 def engineclose(*a):
  events.append('engine_close')
  if mode not in ('success','backend_fatal'):raise engine_error
 engine=types.SimpleNamespace(ann=ann,hard=types.SimpleNamespace(check=noop,create=noop,advance=noop),np=ann.np,policy=noop,_check_owned=noop,_advance_owned=advance,matrix_identity=noop,create=lambda *a,**kw:{'phase':'annealing'},close=engineclose,score_only=lambda *a,**kw:types.SimpleNamespace(score=.5,iterations=1,convergence='iteration_cap'))
 Session=extract(root,'matching_immutable_session.py','ImmutablePairSession',dict(require=p.require,adaptive_edge_policy=edge,compiled_normalization_policy=seam,config_pin=lambda c:(),graph_pin=lambda g:(),rejoin=noop,MappingProxyType=types.MappingProxyType))
 class SessionWithError(Session):
  def close(self):
   super().close();events.append('session_close')
   if mode in ('two_cleanup_repr','backend_fatal'):raise session_error
 Pair=extract(root,'batched_pair_executor.py','PairExecutor',dict(copy=copy,adaptive_edge_policy=edge,compiled_normalization_policy=seam,pair=types.SimpleNamespace(hash_string=noop,policy_check=noop,LIMIT=16,ENGINE_FIELDS=()),engine=engine,annealing=ann,ImmutablePairSession=SessionWithError,CheckpointStop=RuntimeError))
 obj=Pair({},dict(max_publications=1,max_checkpoint_bytes=100,max_score_buffer_bytes=100,chunk_edges=1),dict(max_checkpoints=1,calls_per_checkpoint=1,operations_per_call=3,max_total_checkpoints=1,max_total_checkpoint_bytes=200),noop,compiled_normalization_policy_value=policy)
 error=None
 try:obj('a','b','purpose')
 except BaseException as e:error=e
 live=[]
 for fd in fds:
  try:os.fstat(fd);live.append(fd)
  except OSError:pass
 obs=dict(version=root.name,mode=mode,events_before_memo=list(events),exception=None if error is None else type(error).__name__,primary_identity=error is primary,session_cleanup_identity=error is session_error,annotation_override_calls=len(notes),survivors_before_memo=len(live),closed=obj.closed)
 if root==OLD:
  ok('reviewer identical RED primary replaced',error is allocation and len(live)==1 and events.count('backend_close')==0 and not obj.closed)
 elif mode=='success':
  ok('normal successful session retains parent backend',error is None and len(live)==1 and events.count('backend_close')==0)
 elif mode in ('two_cleanup_repr','backend_fatal'):
  ok('first fatal cleanup preserved despite independent later failures '+mode,error is session_error and events.count('engine_close')==1 and events.count('backend_close')==1 and obj.closed and len(live)==1)
 else:
  ok('primary preserved and independent cleanup attempted '+mode,error is primary and events.count('engine_close')==1 and events.count('backend_close')==1 and obj.closed and len(live)==(1 if mode=='backend_repr' else 0))
 # Actual enclosing memo poison reaches retained executor close. On03 this
 # recovers the descriptor, but does not repair the already replaced primary.
 memo=types.SimpleNamespace(_geometry=None,poisoned=False,_executor_pin=obj,active=True,_clear=noop,last_receipt=None,_executor_cleanup=obj.close)
 poison=extract(root,'batched_numeric_reuse.py','NumericReuseExecutor',dict(sys=sys),method='_poison')
 if error is not None:
  try:raise error
  except BaseException:poison(memo)
 else:obj.close()
 ok('owner original cleanup attempted exactly once '+root.name+mode,events.count('backend_close')==1)
 remaining=[]
 for fd in fds:
  try:os.fstat(fd);remaining.append(fd)
  except OSError:pass
 ok('ambiguous closure is not claimed '+mode,len(remaining)==(1 if mode in ('two_cleanup_repr','backend_repr','backend_fatal') else 0))
 obs['survivors_after_memo']=len(remaining);obs['backend_close_attempts_after_memo']=events.count('backend_close');observations.append(obs)
 for fd in remaining:os.close(fd)
run(OLD,'review_red')
for mode in ('success','normal_primary','review_red','builtin_note_failure','repr_primary','two_cleanup_repr','backend_repr','backend_fatal'):run(HERE,mode)
# Exact source restriction: six bodies reused, reuse only one digest literal,
# PairExecutor only the two originally unsafe annotation statements guarded.
for name in ('compiled_normalization_policy.py','compiled_small_lse.py','matching_immutable_session.py','matching_annealing.py','matching_checkpoint.py','batched_numeric_execution.py'):
 ok('unchanged03 '+name,(HERE/name).read_bytes()==(OLD/name).read_bytes())
oldhash=hashlib.sha256((OLD/'batched_pair_executor.py').read_bytes()).hexdigest();newhash=hashlib.sha256((HERE/'batched_pair_executor.py').read_bytes()).hexdigest()
ok('only mandatory pair source pin',(HERE/'batched_numeric_reuse.py').read_text().replace(newhash,oldhash)==(OLD/'batched_numeric_reuse.py').read_text())
a=ast.parse((HERE/'batched_pair_executor.py').read_text());b=ast.parse((OLD/'batched_pair_executor.py').read_text())
for tree in (a,b):
 cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PairExecutor');fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__call__');fn.body[-1].finalbody=[]
ok('exact AST outside responsible finalization',ast.dump(a)==ast.dump(b))
s=(HERE/'batched_pair_executor.py').read_text()
for old,new in (("                    if primary is not None:primary.add_note('executor cleanup failed: '+repr(cleanup))","                    if primary is not None:\n                        try:BaseException.add_note(primary,'executor cleanup failed: '+repr(cleanup))\n                        except BaseException:pass"),("                    else:cleanup_error.add_note('additional executor cleanup failed: '+repr(cleanup))","                    else:\n                        try:BaseException.add_note(cleanup_error,'additional executor cleanup failed: '+repr(cleanup))\n                        except BaseException:pass")):
 assert s.count(new)==1;s=s.replace(new,old)
ok('exact text inverse outside two annotations',s==(OLD/'batched_pair_executor.py').read_text())
ok('scientific/native modules absent',not {'numpy','scipy','torch','ctypes','array'}&set(sys.modules))
result=dict(status='PASS_FOCUSED_ANNOTATION_CLEANUP',checks=checks,count=len(checks),observations=observations,elapsed_ns=time.perf_counter_ns()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,affinity=[3],native_numerical_execution=False)
(HERE/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','count','elapsed_ns','peak_rss_kib')}))
