import ast,hashlib,json,os,resource,signal,time,types,subprocess,select,math,sys
from pathlib import Path
D=Path(__file__).resolve().parent;P=D.parent/'pilot-grouped-offload-lease-poll01-2026-10-09';S=D.parents[3]/'tradingagents/research/onchain_replication'
os.sched_setaffinity(0,{3});os.nice(10)
for r,v in ((resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)):resource.setrlimit(r,(v,v))
signal.alarm(30);start=time.monotonic_ns();(D/'LIMITER01.json').write_text(json.dumps({'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'wall':30},indent=2)+'\n')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(P/'MANIFEST01.json')=='1a6eddd7eee9848f356f21ac96b1252c455f72c3ca66cdb4aad9344e7de4e12a'
assert h(P/'SOURCE_MAP01.json')=='6941dfd6941ab584855f160f7ee60c1b669fe33f29142a146fece63d3093ee93'
for name,edits in json.loads((P/'CHANGES01.json').read_text()).items():
 text=(P/name).read_text()
 for a,b in reversed(edits):assert text.count(b)==1;text=text.replace(b,a)
 assert text==(S/name).read_text();assert ast.dump(ast.parse(text))==ast.dump(ast.parse((S/name).read_text()))
def require(v,m):
 if not v:raise ValueError(m)
def method(file,cls,name,ns):
 t=ast.parse(file.read_text());c=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name==cls);f=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[f],type_ignores=[]),str(file),'exec'),ns);return ns[name]
poll=method(P/'typed_payload_operations.py','_Operation','_poll_target',{'require':require});options=method(P/'archive_dispatch.py','_Transport','_wait_options',{});live=method(P/'archive_dispatch.py','Context','_live',{'require':require,'get_ident':lambda:1})
def cleanup(actions):
 errors=[]
 for f in actions:
  try:f()
  except BaseException as e:errors.append(e)
 if errors:raise errors[0]
ns=dict(Path=Path,os=os,time=time,subprocess=subprocess,select=select,signal=signal,math=math,archive=types.SimpleNamespace(MAX_BYTES=1024,io=types.SimpleNamespace(_cleanup=cleanup)),STDERR_TAIL_BYTES=16384,_immutable=lambda p,v:p.write_text(json.dumps(v)),_encode=lambda v:json.dumps(v).encode())
t=ast.parse((P/'archive_transport.py').read_text());exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('receive_diagnostic','_positive_finite')],type_ignores=[]),'actual_transport','exec'),ns)
rows=[]
for selected,fail in ((False,False),(True,False),(True,True)):
 owner=object();cap={};events=[];primary=RuntimeError('review target revoked');context=types.SimpleNamespace(_cap=cap,_outer=lambda **kw:None);held=types.SimpleNamespace(check=lambda x:require(x is owner,'owner changed'));view=object();ledger=types.SimpleNamespace(owner=owner,selection=types.SimpleNamespace(_transport=view));began=time.monotonic()
 def targetlease():
  events.append(time.monotonic()-began)
  if fail and events[-1]>.16:raise primary
 target=types.SimpleNamespace(owner=owner,execution=types.SimpleNamespace(_owner=owner),lease=targetlease);op=types.SimpleNamespace(_target=target if selected else None,_target_pin=target if selected else None,owner=owner,context=context,cap=cap,held=held)
 cap.update(thread=1,held=held,ledger=ledger,view=view,typed_operation=op,lease=lambda:poll(op));kw=options(types.SimpleNamespace(_dispatch_context=context));assert kw==({'poll_wait':True} if selected else {})
 dest=D/f'{selected}-{fail}.bin';caught=None
 try:ns['receive_diagnostic']([sys.executable,'-c','import os,time;os.close(1);os.close(2);time.sleep(.4)'],dest,expected_bytes=0,max_seconds=2,bytes_per_second=1,lease_callback=lambda:live(context),**kw)
 except BaseException as e:caught=e
 rec=json.loads(Path(str(dest)+'.transport.json').read_text());pid=rec['pid'];assert not Path('/proc',str(pid)).exists()
 try:os.waitpid(pid,os.WNOHANG)
 except ChildProcessError:pass
 else:raise AssertionError('direct child unreaped')
 if fail:assert caught is primary and rec['returncode']==-signal.SIGKILL and rec['status']=='failed'
 else:assert caught is None and rec['returncode']==0
 if selected:assert len(events)>=3
 else:assert events==[]
 rows.append({'selected':selected,'revoked':fail,'poll_count':len(events),'direct_child_reaped':True,'returncode':rec['returncode'],'primary_identity':caught is primary if fail else None})
# Identity mutation must fail before forwarding. Metadata doubles only.
op._target=object()
try:poll(op)
except ValueError:pass
else:raise AssertionError('replaced target accepted')
(D/'RESULT01.json').write_text(json.dumps({'status':'PASS_SOURCE_SYNTHETIC_LOCAL_CHILD','rows':rows,'literal_ast_inverse':True,'target_replacement_refuses':True,'elapsed_ns':time.monotonic_ns()-start,'qualification':'Real local Python children and direct reaping; extracted actual forwarding/transport methods with metadata-only authority doubles. No genuine Target/Owner/Run or network.'},indent=2)+'\n');print('PASS')
