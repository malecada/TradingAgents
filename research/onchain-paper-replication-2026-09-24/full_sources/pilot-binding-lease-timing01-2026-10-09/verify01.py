import ast,contextlib,json,os,resource,signal,sys,time,types
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];SRC=ROOT/'tradingagents/research/onchain_replication/matching_owner.py'
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)]:resource.setrlimit(k,(v,v))
signal.alarm(30);start=time.monotonic_ns();(P/'LIMITER01.json').write_text(json.dumps({'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'alarm_seconds':30},indent=2)+'\n');assert os.sched_getaffinity(0)=={3}
def require(ok,msg):
 if not ok:raise ValueError(msg)
def lease(tree):return next(n for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='Binding' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='lease')
baseline=ast.parse(SRC.read_text());candidate=ast.parse((P/'matching_owner.py').read_text());old=lease(baseline);new=lease(candidate)
# Actual default statements literal AST match; instrumentation unwrapping matches them too.
assert ast.dump(ast.Module(body=new.body[1].body[:-1],type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=old.body[1:],type_ignores=[]),include_attributes=False)
unwrapped=[]
for n in new.body[3:]:unwrapped.extend(n.body if isinstance(n,ast.With) else [n])
assert ast.dump(ast.Module(body=unwrapped,type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=old.body[1:],type_ignores=[]),include_attributes=False)
class Clock:
 def __init__(self):self.calls=0;self.fail=None;self.error=RuntimeError('clock failure')
 def __call__(self):
  self.calls+=1
  if self.calls==self.fail:raise self.error
  return self.calls*10

def fixture(observed=True,failure=None,clock_failure=None,overflow=False,wrong_clock=False):
 trace=[];clock=Clock();clock.fail=clock_failure;primary=RuntimeError('original failure');guard_calls=[0]
 class FakePath:
  def __init__(self,name):self.name=name
  @property
  def parent(self):return self
  def iterdir(self):trace.append('journal.entries');return [self]
  def __truediv__(self,name):return FakePath(name)
  def exists(self):trace.append('journal.exists:'+self.name);return False
  def __eq__(self,other):return isinstance(other,FakePath) and self.name==other.name
 def metadata(path,root):
  trace.append('metadata:'+path)
  if failure=='snapshot':raise primary
  return {},'pin'
 ns={'require':require,'Path':FakePath,'metadata':metadata,'ancestry':types.SimpleNamespace(verify=lambda *a,**k:trace.append('ancestry')),'contextmanager':contextlib.contextmanager,'time':types.SimpleNamespace(monotonic_ns=clock)}
 nodes=[n for n in candidate.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id.startswith('_LEASE_TIMING_') for t in n.targets) or isinstance(n,ast.ClassDef) and n.name=='BindingLeaseTiming']
 binding=ast.ClassDef(name='Binding',bases=[],keywords=[],body=[new if observed else old],decorator_list=[]);nodes.append(binding);exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'actual-extracted-lease','exec'),ns)
 b=ns['Binding']();b._run=types.SimpleNamespace(_active=lambda:trace.append('active'),admission=types.SimpleNamespace(root='root'));b.record={'journal_directory':'journal'};b._ancestry_arguments=None;b._snapshots={'a':'pin','b':'pin'}
 def guard():
  guard_calls[0]+=1;trace.append('guard'+str(guard_calls[0]))
  if failure=='guard1' and guard_calls[0]==1:raise primary
 b._guard=guard;observer=ns['BindingLeaseTiming'](b) if observed else None
 if overflow:observer._totals=((2**63-1),0,0)+(0,)*9
 if wrong_clock:observer.clock=lambda:0
 error=None
 try:
  if observed:b.lease(observer=observer)
  else:b.lease()
 except BaseException as e:error=e
 return trace,observer,clock,error,primary,ns,b
checks=[]
x=fixture(False);y=fixture();assert x[0]==y[0] and x[3] is y[3] is None;assert y[2].calls==8
snapshot=y[1].snapshot();assert all(snapshot['binding_'+n+'_calls']==1 and snapshot['binding_'+n+'_ns']==10 and snapshot['binding_'+n+'_failures']==0 for n in ['first_guard','journal','snapshots','second_guard']);checks.append('same original order, four finite phases/eight sampled clock calls')
# None means no clock call/counter object even in candidate path.
trace,obs,clock,e,primary,ns,b=fixture();trace.clear();clock.calls=0;b.lease();assert clock.calls==0;checks.append('candidate observerNone direct route no timing calls')
for failure in ['guard1','snapshot']:
 a=fixture(False,failure);b=fixture(True,failure);assert a[0]==b[0] and a[3] is a[4] and b[3] is b[4];assert sum(b[1].snapshot()[k] for k in b[1].snapshot() if k.endswith('_failures'))==1
checks.append('primary validation exceptions and original failure order preserved')
f=fixture(True,'guard1',2);assert f[3] is f[4] and f[1].closed and f[0]==['active','guard1'] and len(f[3].__notes__)==1;checks.append('dual callback/timer failure retains original exact exception')
f=fixture(True,None,2);assert f[3] is f[2].error and f[1].closed and f[0]==['active','guard1'];checks.append('timer failure after successful callback terminal')
f=fixture(overflow=True);assert isinstance(f[3],ValueError) and f[1].closed and f[0]==['active','guard1'];checks.append('counter overflow terminal before later guard phases')
f=fixture(wrong_clock=True);assert isinstance(f[3],ValueError) and f[0]==['active'] and f[1].closed;checks.append('clock identity refusal before timed original guard')
f=fixture();f[1]._totals=(2**63-1,)*12;encoded=(json.dumps(f[1].snapshot(),sort_keys=True,separators=(',',':'))+'\n').encode();assert len(encoded)<8192;checks.append('13 fixed integer metrics max-width payload below unchanged8192 cap')
result={'status':'PASS_SYNTHETIC_ROUTING_ONLY','checks':checks,'max_width_metric_bytes':len(encoded),'elapsed_ns':time.monotonic_ns()-start,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'qualification':'Actual extracted lease/observer code, controlled synthetic Binding-shaped routing only; no genuine Owner/ResearchRun or durable summary integration'};(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
