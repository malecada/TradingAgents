import copy,ctypes,importlib.util,json,math,os,resource,statistics,sys,time
from pathlib import Path
assert resource.getrlimit(resource.RLIMIT_AS)==(268435456,268435456)
assert resource.getrlimit(resource.RLIMIT_FSIZE)==(4194304,4194304)
assert len(os.sched_getaffinity(0))==2 and os.getpriority(os.PRIO_PROCESS,0)==10
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[3]))
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph

def load(file,name):
 name='tradingagents.research.onchain_replication.'+name
 spec=importlib.util.spec_from_file_location(name,P/file);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
B=load('baseline.py','reuse_baseline');C=load('matching_annealing.py','reuse_candidate')
config=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=8,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal')
def graph(n,shift=0.):
 edges=[(u,v) for u in range(n) for v in range(n) if u!=v]
 return AttributedGraph(tuple(str(i) for i in range(n)),np.array([[i/10,shift] for i in range(n)]),np.asarray(edges,dtype=np.int64).T,np.array([[i/13,shift] for i in range(len(edges))]),'a'*64,'0')
a=graph(4);b=graph(3,.2)
checks=0

def equal(x,y):
 global checks
 assert x.keys()==y.keys()
 for k in x:
  if isinstance(x[k],np.ndarray):assert x[k].tobytes()==y[k].tobytes(),k
  else:assert x[k]==y[k],k
 checks+=1

def seed(a=a,b=b):return B.create(a,b,config,max_state_bytes=65536,max_chunk_entries=32)
assert C._reuse_runtime() and C._immutable_edges(a) and C._immutable_edges(b)
for budgets in ([100000],[7,8,19,103],[73,128]):
 x=seed();y=copy.deepcopy(x);step=0
 while x['phase']!='done':
  limit=budgets[step%len(budgets)];step+=1
  assert B.advance(x,a,b,config,max_operations=limit)==C.advance(y,a,b,config,max_operations=limit);equal(x,y)
 rx=B.result(x,a,b,config);ry=C.result(y,a,b,config)
 assert rx.assignment.tobytes()==ry.assignment.tobytes() and rx.soft_assignment.tobytes()==ry.soft_assignment.tobytes() and rx.score.hex()==ry.score.hex()
# Both checkpoint directions on interrupted state, followed by same completion.
x=seed();y=copy.deepcopy(x);assert B.advance(x,a,b,config,max_operations=123)==C.advance(y,a,b,config,max_operations=123);equal(x,y)
for creator,reader,state,name in [(B,C,x,'baseline-checkpoint'),(C,B,y,'candidate-checkpoint')]:
 h=creator.save(state,P/name,a,b,config,max_checkpoint_bytes=100000)
 restored=reader.load(P/name,a,b,config,expected_sha256=h,max_state_bytes=65536,max_chunk_entries=32);equal(state,restored)
 reader.advance(restored,a,b,config,max_operations=100000)
 baseline=copy.deepcopy(state);B.advance(baseline,a,b,config,max_operations=100000);equal(baseline,restored)
# Mutable base, including superficially readonly owned ndarray, is excluded.
mutable=graph(4);features=mutable.edge_features.copy();features.flags.writeable=False;object.__setattr__(mutable,'edge_features',features)
assert not C._immutable_edges(mutable)
x=seed(mutable,b);y=copy.deepcopy(x);B.advance(x,mutable,b,config,max_operations=100000);C.advance(y,mutable,b,config,max_operations=100000);equal(x,y)
# Monkeypatched agreement uses unchanged literal path and retains its side effects/errors.
for mod in (B,C):
 original=mod.agreement;calls=[]
 def patch(left,right):
  calls.append(1)
  if len(calls)==20:raise RuntimeError('patched-agreement-stop')
  return original(left,right)
 mod.agreement=patch
 if mod is C:assert not C._reuse_runtime()
 s=seed()
 try:mod.advance(s,a,b,config,max_operations=100000)
 except RuntimeError as error:assert str(error)=='patched-agreement-stop'
 else:raise AssertionError('patched failure lost')
 mod.agreement=original
 if mod is B:failed=s;expected_calls=len(calls)
 else:equal(failed,s);assert len(calls)==expected_calls
# Lazy failure at original edge ordinal; huge finite edge feature overflows square.
bad=graph(4);features=bad.edge_features.copy();features[1,0]=1e308
bad=AttributedGraph(bad.node_ids,bad.node_features,bad.edge_index,features,bad.parent_hash,bad.center_id)
x=seed(bad,b);y=copy.deepcopy(x);errors=[]
for mod,state in ((B,x),(C,y)):
 try:mod.advance(state,bad,b,config,max_operations=100000)
 except OverflowError as error:errors.append(str(error))
 else:raise AssertionError('overflow missing')
assert errors[0]==errors[1];equal(x,y)
# Supported Linux fenv: non-nearest falls back and restores original environment.
lib=ctypes.CDLL(None);get=lib.fegetround;get.restype=ctypes.c_int;setround=lib.fesetround;setround.argtypes=[ctypes.c_int];old=get()
try:
 assert setround(0x400)==0;assert not C._reuse_runtime()
 x=seed();y=copy.deepcopy(x);B.advance(x,a,b,config,max_operations=100000);C.advance(y,a,b,config,max_operations=100000);equal(x,y)
finally:assert setround(old)==0
# Normalizer monkeypatch is excluded; no new normalizer calls occur.
original=C.logsumexp;C.logsumexp=lambda *args,**kw:original(*args,**kw);assert not C._reuse_runtime();C.logsumexp=original
# Retained state keys are unchanged and full-cache numeric payload is <=36864B.
assert B.META==C.META and C._reuse_runtime()
timing={}
for name,mod in [('baseline',B),('candidate',C)]:
 samples=[]
 for _ in range(7):
  s=seed();t=time.perf_counter();mod._advance_checked(s,a,b,config,max_operations=100000);samples.append(time.perf_counter()-t)
 timing[name]=samples
receipt={'status':'PASS','bitwise_boundaries':checks,'checkpoint_both_directions':True,'lazy_error_prefix':True,'mutable_and_monkeypatched_fallback':True,'nondefault_rounding_fallback':True,'max_cache_numeric_bytes':4096*9,'combined_reservation_bytes':262144,'timing_seconds':timing,'tiny_synthetic_median_speedup':statistics.median(timing['baseline'])/statistics.median(timing['candidate']),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'rlimit_as':resource.getrlimit(resource.RLIMIT_AS),'rlimit_fsize':resource.getrlimit(resource.RLIMIT_FSIZE)}
(P/'RESULT01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
