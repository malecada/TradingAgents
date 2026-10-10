"""Focused independent source and ordinary-FD lifetime fixtures; no numerical execution."""
import ast,builtins,copy,hashlib,json,os,resource,signal,sys,time,types
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3]
C=F/'matching-compiled-normalization-connected03-2026-10-10';O=F/'matching-compiled-normalization-connected02-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(25,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30)
assert os.sched_getaffinity(0)=={3}
start=time.perf_counter_ns();checks=[];evidence={};observations=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def record(p):
 b=p.read_bytes();evidence[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)};return b
def ok(name,test=True):assert test,name;checks.append(name)
original_import=builtins.__import__
def guarded(name,*a,**k):
 assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes','array'},name
 return original_import(name,*a,**k)
builtins.__import__=guarded
manifest=record(C/'MANIFEST.json');ok('frozen manifest',sha(manifest)=='4070e2638527990cee09821bbe1820f42f4385cda857e411adfe20aefe60317b')
for n,v in json.loads(manifest)['files'].items():
 b=record(C/n);ok('manifest '+n,sha(b)==v['sha256'] and len(b)==v['bytes'])
for d,n,s in [(F/'matching-compiled-normalization-connected-review02-2026-10-10','REVIEW01.json','99138c00824f25bc6c6ac89abc2380bd1a9248fe15ecd8ac0616ad6bb890fc2d'),(F/'matching-compiled-library-mapping-lifetime-investigation01-2026-10-10','FINDINGS01.json','85d679a3914671bf8210b3c32f2491aa3977797a96b075912820f65fcb41ec2f')]:ok('accepted reference '+n,sha(record(d/n))==s)
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
modules=('compiled_normalization_policy.py','compiled_small_lse.py','matching_immutable_session.py','batched_pair_executor.py','batched_numeric_reuse.py','matching_annealing.py','matching_checkpoint.py','batched_numeric_execution.py')
for n in modules:
 old=record(O/n);new=(C/n).read_bytes()
 ok('forward exact '+n,apply(old,(C/(n+'.from02.patch')).read_bytes())==new)
 ok('inverse exact '+n,apply(new,(C/(n+'.to02.inverse.patch')).read_bytes())==old)
 if n not in modules[:2]:ok('composed installed inverse '+n,apply(old,(O/(n+'.inverse.patch')).read_bytes())==record(R/'tradingagents/research/onchain_replication'/n))
for n in modules[5:]:ok('unchanged02 '+n,(C/n).read_bytes()==(O/n).read_bytes())
helper=(C/'compiled_small_lse.py').read_text();old=(O/'compiled_small_lse.py').read_text()
a=helper[:helper.index('    def loaded():')]+helper[helper.index('    try:return SimpleNamespace(lse=lse,close=close,current=current,loaded=loaded)'):]
ok('helper exact inverse outside two readonly capabilities',a.replace('SimpleNamespace(lse=lse,close=close,current=current,loaded=loaded)','SimpleNamespace(lse=lse,close=close)')==old)
reuse=(C/'batched_numeric_reuse.py').read_text()
for n in ('compiled_normalization_policy.py','batched_pair_executor.py','matching_immutable_session.py'):
 ok('mandatory source pin once '+n,reuse.count(sha((C/n).read_bytes()))==1)
ok('helper literal pin once',(C/'compiled_normalization_policy.py').read_text().count(sha((C/'compiled_small_lse.py').read_bytes()))==1)
def extract(file,cls=None,method=None,ns=None):
 ns={} if ns is None else ns;t=ast.parse((C/file).read_bytes())
 node=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name==cls) if cls else t
 if method:node=next(n for n in node.body if isinstance(n,ast.FunctionDef) and n.name==method)
 exec(compile(ast.Module(body=[copy.deepcopy(node)],type_ignores=[]),str(C/file),'exec'),ns)
 return ns[method or cls]
p=types.ModuleType('policy');exec(compile((C/'compiled_normalization_policy.py').read_text(),'policy-metadata','exec'),p.__dict__)
policy=dict(format=p.FORMAT,library_path='/fixture/library',library_sha256=p.LIBRARY_SHA256,source_path='/fixture/source',source_sha256=p.SOURCE_SHA256,runtime_path='/fixture/runtime',runtime_sha256='d'*64,runtime_bytes=100)
fixture=P/'ordinary-source.txt';fixture.write_bytes(b'independent ordinary descriptor only\n')
def noop(*a,**k):return None
edge=types.SimpleNamespace(attach=noop,current=noop,options=lambda *a:{},join=noop)
def harness(mode):
 events=[];fds=[];backends=[];reference_calls=[];reads=[];sessions=[];primary=KeyboardInterrupt('injected primary');cleanup=OSError('injected ambiguous cleanup');pinerror=MemoryError('injected post-acquisition pins');close_reads=0
 def loader(*a):
  events.append('open')
  if mode=='loader_fatal':raise primary
  fd=os.open(fixture,os.O_RDONLY);fds.append(fd)
  def close():
   events.append('backend_close')
   if mode in {'ambiguous','fatal_cleanup'}:raise cleanup
   os.close(fd)
  def lse(*a,**k):return 'fallback' if mode=='disabled' else 'fixture'
  class B:
   def __getattribute__(self,n):
    nonlocal close_reads
    if n=='close':
     close_reads+=1
     if mode=='close_lookup_once' and close_reads==1:raise pinerror
    return object.__getattribute__(self,n)
  b=B();b.close=close;b.lse=lse;b.loaded=lambda:mode!='disabled';b.current=lambda:True;backends.append(b);return b
 def references(owner):
  reference_calls.append(len(reference_calls))
  if mode=='later_refs' and len(reference_calls)==2:raise primary
  return policy,types.SimpleNamespace(open_backend=loader)
 def read(*a,**k):
  reads.append((a,k))
  if mode=='later_body' and len(reads)==2:raise ValueError('changed body')
 def pin_tuple(it):
  if mode=='backend_pin_failure' and backends:raise pinerror
  return tuple(it)
 ns=dict(attach=p.attach,current=p.current,join=p.join,require=p.require,_backend_references=references,read_reference=read,tuple=pin_tuple)
 Owner=extract('compiled_normalization_policy.py','BackendOwner',ns=ns)
 owner=Owner(policy);original_close=owner.close;client=types.SimpleNamespace();p.attach(client,policy)
 error=None
 try:
  if mode=='loader_fatal':owner.borrow(client)
  else:
   lease=owner.borrow(client)
   if mode=='double_borrow':owner.borrow(client)
   elif mode=='owner_method':owner.current=noop;lease.current()
   elif mode=='lease_method':lease.lse=noop;lease.current()
   elif mode=='backend_method':backends[0].close=noop;lease.current()
   elif mode=='client_redirect':p.attach(client,None);lease.current()
   elif mode=='parent_closed':original_close();lease.current()
   elif mode=='fatal_cleanup':raise primary
   else:
    lease.close()
    for _ in range(2):
     next_lease=owner.borrow(client);ok('new lease object '+mode,next_lease is not lease);next_lease.current();next_lease.close()
 except BaseException as e:error=e
 # Simulate owning executor's terminal cleanup, using its original capability.
 for _ in range(3):
  try:original_close()
  except BaseException as e:
   if error is None:error=e
   elif e is not error:
    try:BaseException.add_note(error,repr(e))
    except BaseException:pass
 live=[]
 for fd in fds:
  try:os.fstat(fd);live.append(fd)
  except OSError:pass
 obs=dict(mode=mode,events=events,reference_calls=len(reference_calls),library_reads=len(reads),error_type=type(error).__name__ if error else None,primary_identity=error is primary,pinerror_identity=error is pinerror,cleanup_identity=error is cleanup,survivors=len(live))
 observations.append(obs)
 ok('one load maximum '+mode,events.count('open')==1)
 ok('original cleanup once '+mode,events.count('backend_close')==(0 if mode=='loader_fatal' else 1))
 ok('fd accounting '+mode,len(live)==(1 if mode in {'ambiguous','fatal_cleanup'} else 0))
 if mode in {'success','disabled'}:ok('fresh refs every lease '+mode,error is None and len(reference_calls)==3 and len(reads)==(0 if mode=='disabled' else 3))
 else:ok('explicit refusal '+mode,error is not None)
 if mode in {'backend_pin_failure','close_lookup_once'}:ok('constructor primary retained '+mode,error is pinerror)
 if mode in {'loader_fatal','later_refs','fatal_cleanup'}:ok('fatal primary retained '+mode,error is primary)
 for fd in live:os.close(fd)
 obs['harness_only_residual_closes']=len(live)
for mode in ('success','disabled','double_borrow','owner_method','lease_method','backend_method','client_redirect','parent_closed','ambiguous','backend_pin_failure','close_lookup_once','later_refs','later_body','loader_fatal','fatal_cleanup'):harness(mode)
# Changed whole executor seam: real owner + real session classes and ordinary FD;
# fake metadata/engine only. Inherited annotation failure is before NEW cleanup.
def executor_case(annotation_failure):
 events=[];fds=[]
 class Primary(KeyboardInterrupt):
  def add_note(self,text):
   if annotation_failure:raise MemoryError('injected note allocation failure')
   return super().add_note(text)
 primary=Primary('actual advance primary')
 def load(*a):
  fd=os.open(fixture,os.O_RDONLY);fds.append(fd);events.append('open')
  def close():events.append('backend_close');os.close(fd)
  return types.SimpleNamespace(lse=noop,close=close,current=lambda:True,loaded=lambda:True)
 Owner=extract('compiled_normalization_policy.py','BackendOwner',ns=dict(attach=p.attach,current=p.current,join=p.join,require=p.require,_backend_references=lambda o:(policy,types.SimpleNamespace(open_backend=load)),read_reference=noop))
 seam=types.SimpleNamespace(attach=p.attach,current=p.current,options=p.options,join=p.join,BackendOwner=Owner,open_backend=lambda *a:None)
 ann=types.SimpleNamespace(normalization_policy=noop,_check_state_identity=noop,_advance_checked=noop,validate_pair=noop,identity=lambda *a:{},np=object())
 def advance(*a,**k):events.append('advance');raise primary
 def engineclose(*a):events.append('engine_close');raise OSError('injected engine cleanup error')
 engine=types.SimpleNamespace(ann=ann,hard=types.SimpleNamespace(check=noop,create=noop,advance=noop),np=ann.np,policy=noop,_check_owned=noop,_advance_owned=advance,matrix_identity=noop,create=lambda *a,**k:{'phase':'annealing'},close=engineclose)
 Session=extract('matching_immutable_session.py','ImmutablePairSession',ns=dict(require=p.require,adaptive_edge_policy=edge,compiled_normalization_policy=seam,config_pin=lambda c:(),graph_pin=lambda g:(),rejoin=noop,MappingProxyType=types.MappingProxyType))
 Pair=extract('batched_pair_executor.py','PairExecutor',ns=dict(copy=copy,adaptive_edge_policy=edge,compiled_normalization_policy=seam,pair=types.SimpleNamespace(hash_string=noop,policy_check=noop,LIMIT=16,ENGINE_FIELDS=()),engine=engine,annealing=ann,ImmutablePairSession=Session,CheckpointStop=RuntimeError))
 obj=Pair({},dict(max_publications=1,max_checkpoint_bytes=100),dict(max_checkpoints=1,calls_per_checkpoint=1,operations_per_call=3,max_total_checkpoints=1,max_total_checkpoint_bytes=200),noop,compiled_normalization_policy_value=policy)
 error=None
 try:obj('a','b','purpose')
 except BaseException as e:error=e
 live=[]
 for fd in fds:
  try:os.fstat(fd);live.append(fd)
  except OSError:pass
 obs=dict(mode='executor_note_failure' if annotation_failure else 'executor_normal_notes',events=list(events),error_type=type(error).__name__,primary_identity=error is primary,survivors_before_enclosing_memo=len(live),closed=obj.closed,poisoned=obj.poisoned)
 if annotation_failure:ok('RED annotation replaces primary/skips owner cleanup',isinstance(error,MemoryError) and error is not primary and len(live)==1 and events.count('backend_close')==0 and not obj.closed)
 else:ok('normal cleanup preserves primary/releases owner',error is primary and not live and events.count('backend_close')==1 and obj.closed)
 # The actual enclosing memo poison independently recovers owner FD, but cannot
 # recover the already replaced primary exception. No cache/science execution.
 memo=types.SimpleNamespace(_geometry=None,poisoned=False,_executor_pin=obj,active=True,_clear=noop,last_receipt=None,_executor_cleanup=obj.close)
 poison=extract('batched_numeric_reuse.py','NumericReuseExecutor','_poison',dict(sys=sys))
 try:
  raise error
 except BaseException:poison(memo)
 ok('enclosing memo still reaches backend '+str(annotation_failure),events.count('backend_close')==1 and obj.closed)
 obs['enclosing_memo_backend_close_count']=events.count('backend_close');observations.append(obs)
executor_case(False);executor_case(True)
ok('no scientific imports',not {'numpy','scipy','torch','ctypes','array'}&set(sys.modules))
ok('frozen manifest unchanged',record(C/'MANIFEST.json')==manifest)
result=dict(disposition='WITHHOLD_SOURCE_ONLY_UNINSTALLED',checks=checks,check_count=len(checks),observations=observations,body_references=evidence,elapsed_ns=time.perf_counter_ns()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,limits=dict(cpu_seconds=25,wall_alarm_seconds=30,address_space_bytes=512*1024**2,file_size_bytes=4*1024**2,affinity=[3]),native_or_numerical_execution=False,actual_admission=False)
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('disposition','check_count','elapsed_ns','peak_rss_kib')}))
