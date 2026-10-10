"""Independent changed annotation seams only; ordinary FD, no package numerics."""
import ast,builtins,copy,hashlib,json,os,resource,signal,sys,time,types
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];C=F/'matching-compiled-normalization-connected04-2026-10-10';O=F/'matching-compiled-normalization-connected03-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(15,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(20);assert os.sched_getaffinity(0)=={3}
start=time.perf_counter_ns();checks=[];refs={};observations=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def body(p):
 b=p.read_bytes();refs[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)};return b
def ok(n,v=True):assert v,n;checks.append(n)
original_import=builtins.__import__
def guarded(name,*a,**kw):
 assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes','array'},name
 return original_import(name,*a,**kw)
builtins.__import__=guarded
m=body(C/'MANIFEST.json');ok('exact frozen04 manifest',sha(m)=='f05c45c44699ca434ec620ff81d714d02f1a994b88f8e0c8402fe05066bd96b4')
for section in ('files','review03'):
 for n,v in json.loads(m)[section].items():
  b=body((C/n).resolve());ok('manifest '+n,sha(b)==v['sha256'] and len(b)==v['bytes'])
oldm=body(O/'MANIFEST.json');ok('frozen03 manifest',sha(oldm)=='4070e2638527990cee09821bbe1820f42f4385cda857e411adfe20aefe60317b')
oldrefs=json.loads(oldm)['files']
for n in ('compiled_normalization_policy.py','compiled_small_lse.py','matching_immutable_session.py','matching_annealing.py','matching_checkpoint.py','batched_numeric_execution.py','batched_pair_executor.py','batched_numeric_reuse.py'):
 b=body(O/n);ok('exact frozen03 source '+n,sha(b)==oldrefs[n]['sha256'])
 if n not in ('batched_pair_executor.py','batched_numeric_reuse.py'):ok('reuse unchanged03 '+n,b==(C/n).read_bytes())
oldhash=sha((O/'batched_pair_executor.py').read_bytes());newhash=sha((C/'batched_pair_executor.py').read_bytes());new=(C/'batched_numeric_reuse.py').read_bytes();old=(O/'batched_numeric_reuse.py').read_bytes()
ok('single mandatory dependent pin',new.count(newhash.encode())==1 and old.count(oldhash.encode())==1 and new.replace(newhash.encode(),oldhash.encode())==old)
s=(C/'batched_pair_executor.py').read_text()
replacements=[("                    if primary is not None:primary.add_note('executor cleanup failed: '+repr(cleanup))","                    if primary is not None:\n                        try:BaseException.add_note(primary,'executor cleanup failed: '+repr(cleanup))\n                        except BaseException:pass"),("                    else:cleanup_error.add_note('additional executor cleanup failed: '+repr(cleanup))","                    else:\n                        try:BaseException.add_note(cleanup_error,'additional executor cleanup failed: '+repr(cleanup))\n                        except BaseException:pass")]
for before,after in replacements:ok('one exact annotation replacement '+before.strip(),s.count(after)==1);s=s.replace(after,before)
ok('whole byte inverse outside two statements',s==(O/'batched_pair_executor.py').read_text())
def apply(data,patch):
 if not patch:return data
 lines=data.decode().splitlines(True);p=patch.decode().splitlines(True);out=[];cursor=0;i=2
 while i<len(p):
  h=p[i];assert h.startswith('@@ ');pos=int(h.split()[1][1:].split(',')[0])-1;i+=1;assert cursor<=pos;out.extend(lines[cursor:pos]);cursor=pos
  while i<len(p) and not p[i].startswith('@@ '):
   q=p[i];i+=1
   if q[0] in ' -':assert lines[cursor]==q[1:];cursor+=1
   if q[0] in ' +':out.append(q[1:])
 out.extend(lines[cursor:]);return ''.join(out).encode()
for n in ('batched_pair_executor.py','batched_numeric_reuse.py'):
 ok('actual forward patch '+n,apply((O/n).read_bytes(),(C/(n+'.from03.patch')).read_bytes())==(C/n).read_bytes())
 ok('actual inverse patch '+n,apply((C/n).read_bytes(),(C/(n+'.to03.inverse.patch')).read_bytes())==(O/n).read_bytes())
review02=F/'matching-compiled-normalization-connected-review02-2026-10-10/REVIEW01.json';ok('accepted02 reference',sha(body(review02))=='99138c00824f25bc6c6ac89abc2380bd1a9248fe15ecd8ac0616ad6bb890fc2d')
fixture=P/'ordinary-source.txt';fixture.write_bytes(b'independent04 lifecycle source\n')
p=types.ModuleType('policy');exec(compile((C/'compiled_normalization_policy.py').read_text(),'policy metadata','exec'),p.__dict__)
policy=dict(format=p.FORMAT,library_path='/fixture/library',library_sha256=p.LIBRARY_SHA256,source_path='/fixture/source',source_sha256=p.SOURCE_SHA256,runtime_path='/fixture/runtime',runtime_sha256='d'*64,runtime_bytes=100)
def extract(root,file,cls,ns,method=None):
 n=next(n for n in ast.parse((root/file).read_bytes()).body if isinstance(n,ast.ClassDef) and n.name==cls)
 if method:n=next(x for x in n.body if isinstance(x,ast.FunctionDef) and x.name==method)
 exec(compile(ast.Module(body=[copy.deepcopy(n)],type_ignores=[]),str(root/file),'exec'),ns);return ns[method or cls]
def noop(*a,**kw):return None
edge=types.SimpleNamespace(attach=noop,current=noop,options=lambda *a:{},join=noop)
def run(root,mode):
 events=[];fds=[];note_events=[];allocation=MemoryError('note assignment allocation fixture');reprfatal=SystemExit('repr fixture fatal')
 class Primary(KeyboardInterrupt):
  def add_note(self,note):
   note_events.append('overridden_add_note')
   if mode=='original_red':raise allocation
   return super().add_note(note)
  def __setattr__(self,name,value):
   if name=='__notes__' and mode in {'primary_note_alloc','first_cleanup_note_alloc','ambiguous_note_alloc'}:
    note_events.append('notes_assignment_failure');raise allocation
   return super().__setattr__(name,value)
 class Cleanup(OSError):
  def __repr__(self):
   if mode in {'primary_repr_fatal','first_cleanup_repr_fatal'}:
    note_events.append('repr_failure');raise reprfatal
   return super().__repr__()
 primary=Primary('advance fatal');first=Primary('first session cleanup fatal');engine_error=Cleanup('engine close error');backend_error=OSError('ambiguous backend close')
 no_primary=mode.startswith('first_cleanup')
 def load(*a):
  fd=os.open(fixture,os.O_RDONLY);fds.append(fd);events.append('open')
  def close():
   events.append('backend_close')
   if mode=='ambiguous_note_alloc':raise backend_error
   os.close(fd)
  return types.SimpleNamespace(lse=noop,close=close,current=lambda:True,loaded=lambda:True)
 Owner=extract(root,'compiled_normalization_policy.py','BackendOwner',dict(attach=p.attach,current=p.current,join=p.join,require=p.require,_backend_references=lambda o:(policy,types.SimpleNamespace(open_backend=load)),read_reference=noop))
 seam=types.SimpleNamespace(attach=p.attach,current=p.current,options=p.options,join=p.join,BackendOwner=Owner,open_backend=lambda *a:None)
 ann=types.SimpleNamespace(normalization_policy=noop,_check_state_identity=noop,_advance_checked=noop,validate_pair=noop,identity=lambda *a:{},np=object())
 def advance(state,*a,**kw):
  events.append('advance')
  if not no_primary:raise primary
  state['phase']='done'
 def engineclose(*a):events.append('engine_close');raise engine_error
 engine=types.SimpleNamespace(ann=ann,hard=types.SimpleNamespace(check=noop,create=noop,advance=noop),np=ann.np,policy=noop,_check_owned=noop,_advance_owned=advance,matrix_identity=noop,create=lambda *a,**kw:{'phase':'annealing'},close=engineclose,score_only=lambda *a,**kw:types.SimpleNamespace(score=.25,iterations=2,convergence='iteration_cap'))
 Base=extract(root,'matching_immutable_session.py','ImmutablePairSession',dict(require=p.require,adaptive_edge_policy=edge,compiled_normalization_policy=seam,config_pin=lambda c:(),graph_pin=lambda g:(),rejoin=noop,MappingProxyType=types.MappingProxyType))
 class Session(Base):
  def close(self):
   super().close();events.append('session_close')
   if no_primary:raise first
 Pair=extract(root,'batched_pair_executor.py','PairExecutor',dict(copy=copy,adaptive_edge_policy=edge,compiled_normalization_policy=seam,pair=types.SimpleNamespace(hash_string=noop,policy_check=noop,LIMIT=16,ENGINE_FIELDS=()),engine=engine,annealing=ann,ImmutablePairSession=Session,CheckpointStop=RuntimeError))
 obj=Pair({},dict(max_publications=1,max_checkpoint_bytes=100,max_score_buffer_bytes=100,chunk_edges=1),dict(max_checkpoints=1,calls_per_checkpoint=1,operations_per_call=2,max_total_checkpoints=1,max_total_checkpoint_bytes=200),noop,compiled_normalization_policy_value=policy)
 error=None
 try:obj('a','b','purpose')
 except BaseException as e:error=e
 def survivors():
  live=[]
  for fd in fds:
   try:os.fstat(fd);live.append(fd)
   except OSError:pass
  return live
 live=survivors();obs=dict(version='03' if root==O else '04',mode=mode,events_before_memo=list(events),note_events=list(note_events),error_type=type(error).__name__,primary_identity=error is primary,first_cleanup_identity=error is first,allocation_identity=error is allocation,closed=obj.closed,poisoned=obj.poisoned,fds_before_memo=len(live))
 if root==O:ok('original RED reproduced',error is allocation and len(live)==1 and not obj.closed and events.count('backend_close')==0)
 else:
  ok('original error identity '+mode,error is (first if no_primary else primary))
  ok('independent cleanup and poison '+mode,events.count('session_close')==events.count('engine_close')==events.count('backend_close')==1 and obj.closed and obj.poisoned)
  ok('ordinary FD accounting '+mode,len(live)==(1 if mode=='ambiguous_note_alloc' else 0))
  if 'alloc' in mode:ok('actual note assignment failure hit '+mode,'notes_assignment_failure' in note_events)
  if 'repr' in mode:ok('actual repr fatal hit '+mode,'repr_failure' in note_events)
  if mode=='original_red':ok('override bypassed',not note_events)
 memo=types.SimpleNamespace(_geometry=None,poisoned=False,_executor_pin=obj,active=True,_clear=noop,last_receipt=None,_executor_cleanup=obj.close)
 poison=extract(root,'batched_numeric_reuse.py','NumericReuseExecutor',dict(sys=sys),method='_poison')
 caught=None
 try:
  try:raise error
  except BaseException:poison(memo);raise
 except BaseException as e:caught=e
 ok('actual memo retains received exception '+root.name+mode,caught is error)
 repeat=[]
 for _ in range(2):
  try:obj.close();repeat.append(None)
  except BaseException as e:repeat.append(e)
 ok('no backend retry '+root.name+mode,events.count('backend_close')==1)
 if mode=='ambiguous_note_alloc':ok('ambiguous identity repeated',all(e is backend_error for e in repeat))
 left=survivors();obs.update(fds_after_memo=len(left),backend_close_attempts=events.count('backend_close'),harness_only_residual_closes=len(left));observations.append(obs)
 for fd in left:os.close(fd)
run(O,'original_red')
for mode in ('original_red','primary_note_alloc','primary_repr_fatal','first_cleanup_note_alloc','first_cleanup_repr_fatal','ambiguous_note_alloc','normal_primary'):run(C,mode)
ok('no prohibited imports',not {'numpy','scipy','torch','ctypes','array'}&set(sys.modules))
ok('frozen04 unchanged',body(C/'MANIFEST.json')==m)
r=dict(disposition='ACCEPT_SOURCE_ONLY_UNINSTALLED',checks=checks,check_count=len(checks),observations=observations,body_references=refs,native_or_numerical_execution=False,elapsed_ns=time.perf_counter_ns()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,limits=dict(cpu_seconds=15,alarm_seconds=20,external_seconds=25,address_space_bytes=512*1024**2,file_size_bytes=4*1024**2,cpu=3))
(P/'RESULT01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('disposition','check_count','elapsed_ns','peak_rss_kib')}))
