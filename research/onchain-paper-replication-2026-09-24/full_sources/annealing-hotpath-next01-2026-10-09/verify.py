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
assert C._reuse_runtime()
# Full-hit, initially partial cache, short scalar tail, and >1024 chunk cases.
for aa,bb,budgets in [(a,b,[100000]),(a,b,[123,100000]),(a,b,[73,128]),(graph(8),graph(6,.2),[100000]),(graph(8),graph(6,.2),[2000,100000])]:
 x=seed(aa,bb);y=copy.deepcopy(x);step=0
 while x['phase']!='done':
  limit=budgets[step%len(budgets)];step+=1
  assert B.advance(x,aa,bb,config,max_operations=limit)==C.advance(y,aa,bb,config,max_operations=limit);equal(x,y)
 rx=B.result(x,aa,bb,config);ry=C.result(y,aa,bb,config)
 assert rx.assignment.tobytes()==ry.assignment.tobytes() and rx.soft_assignment.tobytes()==ry.soft_assignment.tobytes() and rx.score.hex()==ry.score.hex()
# Inverse checkpoint directions at partial edge population.
x=seed();B.advance(x,a,b,config,max_operations=123)
for writer,reader,name in [(B,C,'b-to-c'),(C,B,'c-to-b')]:
 h=writer.save(x,P/name,a,b,config,max_checkpoint_bytes=100000)
 y=reader.load(P/name,a,b,config,expected_sha256=h,max_state_bytes=65536,max_chunk_entries=32)
 equal(x,y);z=copy.deepcopy(x)
 B.advance(z,a,b,config,max_operations=100000);reader.advance(y,a,b,config,max_operations=100000);equal(z,y)
# First population retains the exact failing scalar prefix.
bad=graph(4);features=bad.edge_features.copy();features[1,0]=1e308
bad=AttributedGraph(bad.node_ids,bad.node_features,bad.edge_index,features,bad.parent_hash,bad.center_id)
x=seed(bad,b);y=copy.deepcopy(x);errors=[]
for mod,state in ((B,x),(C,y)):
 try:mod.advance(state,bad,b,config,max_operations=100000)
 except OverflowError as error:errors.append((type(error).__name__,str(error)))
 else:raise AssertionError('missing error')
assert errors[0]==errors[1];equal(x,y)
# Unsupported mutable feature storage remains baseline behavior.
mutable=graph(4);object.__setattr__(mutable,'edge_features',mutable.edge_features.copy())
assert not C._immutable_edges(mutable)
x=seed(mutable,b);y=copy.deepcopy(x)
B.advance(x,mutable,b,config,max_operations=100000);C.advance(y,mutable,b,config,max_operations=100000);equal(x,y)
# Warm full-cache chunk copy preserves negative-zero and subnormal bit patterns.
for values in ([0.,-0.,float.fromhex('0x0.0000000000001p-1022')],[.5,.25,0.]):
 src=np.array(values,dtype=np.float64);dst=np.empty(len(src),dtype=np.float64)
 dst[:]=src[:];assert dst.tobytes()==src.tobytes()
timing={}
aa=graph(8);bb=graph(6,.2)
for name,mod in [('baseline',B),('candidate',C)]:
 samples=[]
 for _ in range(9):
  s=seed(aa,bb);t=time.perf_counter();mod._advance_checked(s,aa,bb,config,max_operations=100000);samples.append(time.perf_counter()-t)
 timing[name]=samples
receipt={'status':'PASS','bitwise_boundaries':checks,'checkpoint_inverse':True,'lazy_error_prefix':True,'timings_seconds':timing,'tiny_synthetic_median_speedup':statistics.median(timing['baseline'])/statistics.median(timing['candidate']),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'rlimit_as':resource.getrlimit(resource.RLIMIT_AS),'rlimit_fsize':resource.getrlimit(resource.RLIMIT_FSIZE)}
(P/'RESULT01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
