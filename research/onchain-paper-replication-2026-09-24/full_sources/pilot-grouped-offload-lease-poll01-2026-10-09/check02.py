import os,resource,signal,json,ast,types,time,subprocess,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];S=R/'tradingagents/research/onchain_replication'
os.sched_setaffinity(0,{3});os.nice(10)
for r,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)]:resource.setrlimit(r,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
limits={'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'as':resource.getrlimit(resource.RLIMIT_AS),'fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'cpu':resource.getrlimit(resource.RLIMIT_CPU),'wall':signal.getitimer(signal.ITIMER_REAL)}
assert limits['affinity']==[3] and limits['nice']==10
(D/'LIMITER02.json').write_text(json.dumps(limits,indent=2)+'\n');started=time.perf_counter()
for name,edits in json.loads((D/'CHANGES01.json').read_text()).items():
 text=(D/name).read_text()
 for old,new in reversed(edits):assert text.count(new)==1;text=text.replace(new,old)
 assert text==(S/name).read_text();assert ast.dump(ast.parse(text))==ast.dump(ast.parse((S/name).read_text()))
checks=['five modules literal/AST inverse']
interval={};exec(compile((S/'imported_authority_interval.py').read_text(),'actual_interval','exec'),interval)
p={'schema_version':1,'kind':interval['KIND'],'live_interval_ms':100,'fingerprint_interval_ms':1000,'full_interval_ms':10000,'max_stale_ms':60000,'max_calls_between_full':65536,'assumption':interval['ASSUMPTION']}
def require(v,m):
 if not v:raise ValueError(m)
def method(path,cls,name,ns):
 c=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name==cls);f=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[f],type_ignores=[]),str(path),'exec'),ns);return ns[name]
poll=method(D/'typed_payload_operations.py','_Operation','_poll_target',{'require':require})
live=method(S/'archive_dispatch.py','Context','_live',{'require':require,'get_ident':lambda:1})
wait_options=method(D/'archive_dispatch.py','_Transport','_wait_options',{})
# Actual receive function, fake child/pipe/time; real tiny local diagnostic files.
def run(label,selected,fail=False,cleanup_fail=False):
 now=[0.];events=[];primary=RuntimeError('synthetic target revocation');cleanup=OSError('synthetic cleanup failure')
 sched=interval['Interval'](p,clock=lambda:now[0]);full=[]
 def target_lease():
  events.append(('target',now[0]))
  if fail and now[0]>=12:raise primary
  sched.validate(lambda:full.append(now[0]),lambda:None,lambda:None)
 target_lease()
 owner=object();held=types.SimpleNamespace(check=lambda owner:None);view=object();ledger=types.SimpleNamespace(owner=owner,selection=types.SimpleNamespace(_transport=view));cap={};context=types.SimpleNamespace(_outer=lambda **kw:None,_cap=cap)
 target=types.SimpleNamespace(owner=owner,execution=types.SimpleNamespace(_owner=owner),lease=target_lease)
 op=types.SimpleNamespace(_target=target if selected else None,_target_pin=target if selected else None,owner=owner,held=held,context=context,cap=cap)
 # Original typed/ledger authority callbacks stay represented; no real authority claim.
 def typed_lease():
  events.append(('typed',now[0]))
  if selected:poll(op)
 cap.update(thread=1,held=held,ledger=ledger,lease=typed_lease,view=view,typed_operation=op)
 callback=lambda:live(context)
 assert wait_options(types.SimpleNamespace(_dispatch_context=context))==({'poll_wait':True} if selected else {})
 class Pipe:
  def __init__(self,n):self.n=n
  def fileno(self):return self.n
  def close(self):events.append(('close',self.n))
 class Proc:
  pid=123;returncode=None
  def __init__(self):self.stdout=Pipe(100);self.stderr=Pipe(101)
  def wait(self,timeout):
   events.append(('wait',timeout))
   if self.returncode is not None:return self.returncode
   if now[0]+timeout<65:
    now[0]+=timeout;raise subprocess.TimeoutExpired('synthetic',timeout)
   now[0]=65.;self.returncode=0;return 0
 proc=Proc()
 def kill(*args):events.append(('kill',now[0]));proc.returncode=-9
 def cleanup_all(actions):
  for fn in actions:fn()
  if cleanup_fail:raise cleanup
 ns={'Path':Path,'os':types.SimpleNamespace(path=os.path,set_blocking=lambda *x:None,read=lambda *x:b'',killpg=kill,fsync=os.fsync),'time':types.SimpleNamespace(monotonic=lambda:now[0]),'subprocess':types.SimpleNamespace(Popen=lambda *a,**k:proc,TimeoutExpired=subprocess.TimeoutExpired),'select':types.SimpleNamespace(select=lambda watched,*a:(watched,[],[])),'signal':signal,'archive':types.SimpleNamespace(MAX_BYTES=4*1024**2,io=types.SimpleNamespace(_cleanup=cleanup_all)),'STDERR_TAIL_BYTES':16384,'_immutable':lambda path,record:path.write_text(json.dumps(record)),'_encode':lambda value:json.dumps(value).encode()}
 src=D/'archive_transport.py' if selected else S/'archive_transport.py';t=ast.parse(src.read_text());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('_positive_finite','receive_diagnostic')];ns['math']=__import__('math');exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'),ns)
 caught=None
 try:
  ns['receive_diagnostic'](['NO_PROCESS'],D/(label+'_02.bin'),expected_bytes=0,max_seconds=90,bytes_per_second=1,lease_callback=callback,**({'poll_wait':True} if selected else {}))
  target_lease() # Original post-group boundary equivalent.
 except BaseException as error:caught=error
 if not selected:
  print('RED_CAUGHT',repr(caught))
  assert isinstance(caught,ValueError) and 'stale interval cannot refresh' in str(caught)
 elif fail:
  assert caught is primary
  assert any(e[0]=='kill' for e in events) and sum(e[0]=='close' for e in events)==2
  if cleanup_fail:assert any('cleanup failed' in n for n in primary.__notes__)
 else:assert caught is None and len(full)>=6 and now[0]==65 and not sched.closed
 return {'label':label,'selected':selected,'synthetic_elapsed':now[0],'target_polls':sum(e[0]=='target' for e in events),'full_checks':full,'exception':None if caught is None else str(caught),'primary_identity_preserved':caught is primary if fail else None,'process_spawned':False,'max_success_wait':max(e[1] for e in events if e[0]=='wait'),'cleanup_closes':sum(e[0]=='close' for e in events)}
rows=[run('RED_original',False),run('GREEN_selected',True),run('poll_failure',True,True),run('poll_and_cleanup_failure',True,True,True)]
checks+=['original65s pipe-closed child wait leaves target stale RED','selected actual receive loop and dispatch target seam poll through65s wait GREEN','poll revocation kills/reaps/closes and preserves primary','poll plus cleanup failure retains primary with note']
(D/'RESULT02.json').write_text(json.dumps({'status':'PASS_SOURCE_METADATA_SIMULATION','checks':checks,'rows':rows,'limits':limits,'elapsed_seconds':time.perf_counter()-started,'qualification':'Actual interval, receive, dispatch _live/_wait_options and typed _poll_target functions; explicit synthetic clock/child/authority doubles. No physical process, SSH/SFTP, credentials or real authority.'},indent=2)+'\n');print(json.dumps(rows,indent=2))
