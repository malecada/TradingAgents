import os,resource,signal,json,sys,ast,importlib.util,struct
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];C=D.parent/'matching-adaptive-edge-cache01-2026-10-09'
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)]:resource.setrlimit(k,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
limits={'cpu':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'as':resource.getrlimit(resource.RLIMIT_AS),'file':resource.getrlimit(resource.RLIMIT_FSIZE),'seconds':resource.getrlimit(resource.RLIMIT_CPU),'threads':{k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}}
(D/'LIMITER02.json').write_text(json.dumps(limits,indent=2)+'\n');sys.path.insert(0,str(R))
import numpy as np
from tradingagents.research.onchain_replication import matching_annealing as old
from tradingagents.research.onchain_replication.contracts import AttributedGraph
spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.independent_adaptive',C/'matching_annealing.py');new=importlib.util.module_from_spec(spec);sys.modules[spec.name]=new;spec.loader.exec_module(new)
source=(C/'matching_annealing.py').read_text();inverse=source
for a,b in reversed(json.loads((C/'CHANGES01.json').read_text())):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
assert inverse==Path(old.__file__).read_text()
c=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_text());policy=dict(new.ADAPTIVE_EDGE_POLICY)
def graph(n,e,bad=False):
 edges=np.array([(i,j) for i in range(n) for j in range(n)][:e],dtype=np.int64).T.copy();features=np.arange(e,dtype=np.float64).reshape(-1,1)*.001
 if bad:features[5]=1e308
 return AttributedGraph(tuple(str(i) for i in range(n)),np.arange(n,dtype=np.float64).reshape(-1,1)*.015,edges,features,'b'*64,'0')
a,b=graph(9,70),graph(10,72);T=5040
assert new._reuse_runtime() and new._immutable_edges(a) and new._immutable_edges(b)
def create(mod,aa=a):return mod.create(aa,b,c,max_state_bytes=1048576,max_chunk_entries=256)
def same(x,y):
 assert x.keys()==y.keys()
 for k in x:
  if type(x[k]) is np.ndarray:assert (x[k].dtype,x[k].shape,x[k].tobytes())==(y[k].dtype,y[k].shape,y[k].tobytes()),k
  else:assert x[k]==y[k],k
x=create(old);y=create(new);u=old.advance(x,a,b,c,max_operations=1000000);v=new.advance(y,a,b,c,max_operations=1000000,edge_cache_policy=policy);same(x,y);assert u==v and y['phase']=='done'
xr=old.result(x,a,b,c);yr=new.result(y,a,b,c);assert xr.assignment.tobytes()==yr.assignment.tobytes() and struct.pack('d',xr.score)==struct.pack('d',yr.score)
pin=new.save(y,D/'checkpoint02',a,b,c,max_checkpoint_bytes=1048576,checkpoint_layout={'format':'sharded-npy-v1','chunk_entries':256});same(y,old.load(D/'checkpoint02',a,b,c,expected_sha256=pin,max_state_bytes=1048576,max_chunk_entries=256,checkpoint_layout={'format':'sharded-npy-v1','chunk_entries':256}))
# Nonstandard runtime at a budget exceeding T: extended selection must fall back.
with np.errstate(under='raise'):
 x=create(old);y=create(new);u2=old.advance(x,a,b,c,max_operations=6000);v2=new.advance(y,a,b,c,max_operations=6000,edge_cache_policy=policy);same(x,y);assert u2==v2
# Invalid explicit policy is refused with genuine eligible runtime and budget.
assert new._reuse_runtime()
p=dict(policy);p['chunk_entries']=512
try:new.advance(create(new),a,b,c,max_operations=1000000,edge_cache_policy=p)
except ValueError as e:assert str(e)=='explicit adaptive edge cache policy required'
else:raise AssertionError('invalid policy accepted')
af=graph(9,70,True);fail=[]
for mod,kw in [(old,{}),(new,{'edge_cache_policy':policy})]:
 s=create(mod,af)
 try:mod.advance(s,af,b,c,max_operations=1000000,**kw)
 except OverflowError as e:fail.append((s,type(e).__name__,str(e)))
 else:raise AssertionError('overflow absent')
same(fail[0][0],fail[1][0]);assert fail[0][1:]==fail[1][1:] and fail[0][0]['cursor']==360 and fail[0][0]['safe'] is False
out={'decision':'passed_finite_synthetic','limits':limits,'literal_inverse':True,'runtime_guard_unmodified_and_true':True,'shape':[9,10],'edges':[70,72],'edge_product':T,'full_used':u,'iterations':yr.iterations,'assignment_score_state_bitwise':True,'checkpoint_sha256':pin,'strict_mode_budget':6000,'strict_mode_used':u2,'strict_mode_state_equal':True,'invalid_policy_refused_eligible_budget':1000000,'overflow_cursor':360,'overflow_prefix_state_equal':True,'no_runtime_pins_modified':True}
(D/'RESULT02.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
