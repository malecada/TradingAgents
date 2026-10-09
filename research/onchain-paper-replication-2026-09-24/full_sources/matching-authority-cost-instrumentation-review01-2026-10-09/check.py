import os,resource,signal,json,ast,types,time,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];C=D.parent/'matching-authority-cost-instrumentation01-2026-10-09';S=R/'tradingagents/research/onchain_replication'
os.sched_setaffinity(0,{3});os.nice(10)
for r,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)]:resource.setrlimit(r,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
limits={'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'as':resource.getrlimit(resource.RLIMIT_AS),'fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'cpu':resource.getrlimit(resource.RLIMIT_CPU),'wall_timer_remaining':signal.getitimer(signal.ITIMER_REAL)[0]}
assert limits['affinity']==[3] and limits['as']==(536870912,)*2 and limits['fsize']==(4194304,)*2 and 0<limits['wall_timer_remaining']<=30
(D/'LIMITER01.json').write_text(json.dumps(limits,indent=2)+'\n')
def require(v,m):
 if not v:raise ValueError(m)
src=(C/'batched_numeric_reuse.py').read_text();change=json.loads((C/'CHANGE01.json').read_text());inverse=src.replace(change['insertion'],'',1).replace('import array,copy,ctypes,hashlib,json,math,struct,sys,types,time','import array,copy,ctypes,hashlib,json,math,struct,sys,types');assert inverse==(S/'batched_numeric_reuse.py').read_text()
tree=ast.parse(src);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='NumericReuseExecutor');init=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='__init__');node=next(x for x in init.body if isinstance(x,ast.If) and ast.unparse(x.test)=='authority_poll is not None');code=compile(ast.Module(body=[node],type_ignores=[]),'actual_constructor_seam','exec')
def build(cb):
 obj=types.SimpleNamespace(counters={});ns={'self':obj,'authority_poll':cb,'time':time,'types':types,'require':require};exec(code,ns);return obj,ns['authority_poll'],ns
checks=[]
obj,f,ns=build(None);assert f is None and not obj.counters;checks.append('None exact no instrumentation')
trace=[];sentinel=object()
def cb(*args,**kwargs):trace.append((args,kwargs));return sentinel
obj,f,ns=build(cb);assert f() is sentinel and f() is sentinel and trace==[((),{}),((),{})];assert obj.counters['authority_poll_calls']==2 and obj.counters['authority_poll_failures']==0;checks.append('two invocations exact zero arguments order return identity')
primary=KeyboardInterrupt('primary')
def bad():raise primary
obj,f,ns=build(bad)
try:f()
except BaseException as error:assert error is primary
else:raise AssertionError('missing exception')
assert obj.counters['authority_poll_calls']==obj.counters['authority_poll_failures']==1;checks.append('BaseException identity and failure accounting')
for kind in ['callback_identity','bool_counter','count_exhaustion','ns_exhaustion']:
 obj,f,ns=build(cb);before=len(trace)
 if kind=='callback_identity':obj._authority_poll_original=lambda:None
 if kind=='bool_counter':obj.counters['authority_poll_ns']=True
 if kind=='count_exhaustion':ns['totals'][0]=obj.counters['authority_poll_calls']=2**63-1
 if kind=='ns_exhaustion':ns['totals'][1]=obj.counters['authority_poll_ns']=2**63-1
 try:f()
 except ValueError:pass
 else:raise AssertionError(kind)
 assert len(trace)==before+(kind=='ns_exhaustion');checks.append(kind+' refusal and callback count')
clock=time.perf_counter_ns
try:
 def mutate():time.perf_counter_ns=lambda:0;return sentinel
 obj,f,ns=build(mutate)
 try:raise RuntimeError('ambient')
 except RuntimeError:
  try:f()
  except ValueError:pass
  else:raise AssertionError('ambient swallowed failure')
finally:time.perf_counter_ns=clock
checks.append('postcallback timer identity mutation refuses under ambient exception')
try:
 def double_failure():time.perf_counter_ns=lambda:0;raise primary
 obj,f,ns=build(double_failure)
 try:f()
 except BaseException as error:assert error is primary and any('authority timing failed' in n for n in error.__notes__)
 else:raise AssertionError('missing primary')
finally:time.perf_counter_ns=clock
checks.append('callback primary survives secondary timer failure')
# Extract unchanged actual summary builder; no imports of numerical modules.
t=ast.parse((S/'batched_numeric_execution.py').read_text());functions=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ['raw','counters']];complete=next(n for cl in t.body if isinstance(cl,ast.ClassDef) for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='_complete_batch');assign=next(n for n in complete.body if isinstance(n,ast.Assign) and any(isinstance(q,ast.Name) and q.id=='summary' for q in n.targets))
base={k:2**127-1 for k in ('source_guard_calls','source_hashed_bytes','key_hashed_bytes','lookup_probes','lru_link_updates','evictions','accounted_cache_bytes')};base.update({k:2**63-1 for k in ('authority_poll_calls','authority_poll_ns','authority_poll_failures')})
def summary(start,batch,stop,computed,reused,elapsed):
 holder=types.SimpleNamespace(batch=batch,ordinal=stop,batch_computed=computed,batch_reused=reused,batch_elapsed=elapsed,buffer=b'',receipts=hashlib.sha256(),memo=types.SimpleNamespace(counters=base));ns=dict(self=holder,start=start,FORMAT='numeric-reuse-origins-v1',json=json,hashlib=hashlib,require=require);exec(compile(ast.Module(body=functions+[assign],type_ignores=[]),'actual_summary','exec'),ns);return len(ns['raw'](ns['summary']))
fixture=summary(0,2**60,2**60,2**60,2**60,1.7976931348623157e308);assert fixture==1027
# Deliberately overbound real counters: start/stop/batch <=19 digits; counts <=4096 (4digits).
# Nonnegative finite Python binary64 repr is at most24 characters; use a 24-char representative.
flo=1.2345678901234567e-100;assert len(json.dumps(flo))==23
upper=summary(2**63-1,2**63-1,2**63-1,4096,4096,flo)+1
assert upper<=1027<8192
checks.append('actual summary original1027 fixture and conservative legal-width upper bound')
(D/'RESULT01.json').write_text(json.dumps({'status':'PASS_STDLIB_ONLY','checks':checks,'inverse':True,'author_fixture_bytes':fixture,'conservative_actual_schema_upper_bytes':upper,'source_summary_limit':8192,'author_resource_deviation':'actual author affinity[0,1,2], not requested[3]; reviewer run does not repair author history','limits':limits},indent=2)+'\n');print(json.dumps({'checks':len(checks),'summary_upper':upper,'affinity':limits['affinity']}))
