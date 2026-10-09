"""One limited worker, actual instrumentation AST and summary emitter; synthetic callbacks only."""
import ast,types,time,json,hashlib,resource,os,signal,sys
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[3];S=ROOT/'tradingagents/research/onchain_replication'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(60);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:3]);os.nice(10)
receipt=dict(pid=os.getpid(),affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),rlimit_cpu=list(resource.getrlimit(resource.RLIMIT_CPU)),rlimit_fsize=list(resource.getrlimit(resource.RLIMIT_FSIZE)),wall_alarm_seconds=60,python=sys.version)
(H/'LIMITER01.json').write_text(json.dumps(receipt,indent=2)+'\n')
def require(ok,msg):
 if not ok:raise ValueError(msg)
text=(H/'batched_numeric_reuse.py').read_text();tree=ast.parse(text);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NumericReuseExecutor');init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__');guard=next(n for n in init.body if isinstance(n,ast.If) and ast.unparse(n.test)=='authority_poll is not None')
code=compile(ast.Module(body=[guard],type_ignores=[]),'<actual constructor instrumentation>','exec')
def make(callback):
 holder=types.SimpleNamespace(counters={});scope=dict(self=holder,authority_poll=callback,time=time,types=types,require=require);exec(code,scope);return holder,scope['authority_poll'],scope
checks=[]
h,cb,ns=make(None);assert cb is None and h.counters=={};checks.append('None adds no counters or timer samples')
trace=[];token=object()
def callback():trace.append('original');return token
h,cb,ns=make(callback);assert cb() is token and cb() is token and trace==['original','original'];assert h.counters['authority_poll_calls']==2 and h.counters['authority_poll_ns']>=0 and h.counters['authority_poll_failures']==0;checks.append('exact return identity and one original call per invocation')
primary=RuntimeError('callback primary')
def fails():raise primary
h,cb,ns=make(fails)
try:cb()
except RuntimeError as e:assert e is primary
else:raise AssertionError('exception')
assert h.counters['authority_poll_failures']==h.counters['authority_poll_calls']==1;checks.append('same original callback exception object, failure counted')
# Ambient exception must not hide successful-callback instrumentation failure.
original_clock=time.perf_counter_ns
try:
 try:raise KeyError('ambient')
 except KeyError:
  def changes_clock():time.perf_counter_ns=lambda:0
  h,cb,ns=make(changes_clock)
  try:cb()
  except ValueError as e:assert 'timer changed' in str(e)
  else:raise AssertionError('timer mutation')
finally:time.perf_counter_ns=original_clock
checks.append('timer replacement refuses even during ambient exception')
try:
 def both():time.perf_counter_ns=lambda:0;raise primary
 h,cb,ns=make(both)
 try:cb()
 except RuntimeError as e:assert e is primary and any('authority timing failed' in n for n in e.__notes__)
 else:raise AssertionError('primary preservation')
finally:time.perf_counter_ns=original_clock
checks.append('timing failure annotates and preserves callback primary')
h,cb,ns=make(callback);h.counters['authority_poll_calls']=True
try:cb()
except ValueError:pass
else:raise AssertionError('typed counters')
checks.append('counter mutation/type refusal')
h,cb,ns=make(callback);ns['totals'][0]=2**63-1;h.counters['authority_poll_calls']=2**63-1;before=len(trace)
try:cb()
except ValueError:pass
else:raise AssertionError('bound')
assert len(trace)==before;checks.append('signed63 count exhaustion refuses before callback')
# Unchanged actual counters and full summary emitter validate finite payload extent.
t=ast.parse((S/'batched_numeric_execution.py').read_text());counterfn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='counters');complete=next(n for c in t.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='_complete_batch');summary=next(n for n in complete.body if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='summary' for v in n.targets))
base={k:2**127-1 for k in ('source_guard_calls','source_hashed_bytes','key_hashed_bytes','lookup_probes','lru_link_updates','evictions','accounted_cache_bytes')};base.update({k:2**63-1 for k in ('authority_poll_calls','authority_poll_ns','authority_poll_failures')})
ns2=dict(require=require,FORMAT='numeric-reuse-origins-v1',hashlib=hashlib,start=0,self=types.SimpleNamespace(ordinal=2**60,batch=2**60,batch_computed=2**60,batch_reused=2**60,buffer=b'',receipts=hashlib.sha256(),memo=types.SimpleNamespace(counters=base),batch_elapsed=1.7976931348623157e308))
exec(compile(ast.Module(body=[counterfn,summary],type_ignores=[]),'<actual summary emitter>','exec'),ns2);body=(json.dumps(ns2['summary'],sort_keys=True,separators=(',',':'))+'\n').encode();assert len(body)<8192
# Existing publication guard is retained byte-for-byte; oversized payload still refuses.
assert "require(len(body)<=SUMMARY_LIMIT and self.summary_bytes+len(body)<=self.max_summary_bytes and 9*self.ordinal<=self.max_origin_bytes,'numeric retained byte cap')" in (S/'batched_numeric_execution.py').read_text()
checks.append('actual summary emitter maximum-width counters fit existing8192 limit')
change=json.loads((H/'CHANGE01.json').read_text());inverse=text.replace(change['insertion'],'',1).replace('import array,copy,ctypes,hashlib,json,math,struct,sys,types,time','import array,copy,ctypes,hashlib,json,math,struct,sys,types');assert inverse==(S/'batched_numeric_reuse.py').read_text()
(H/'RESULT01.json').write_text(json.dumps(dict(status='PASS_SYNTHETIC_CALLBACKS_ONLY',checks=checks,summary_bytes=len(body),limit=8192,default_None_no_fabricated_time=True,literal_inverse=True,limiter_sha256=hashlib.sha256((H/'LIMITER01.json').read_bytes()).hexdigest()),indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(checks),'summary_bytes':len(body),'affinity':receipt['affinity'],'rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
