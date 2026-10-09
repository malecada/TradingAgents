import os,resource,signal,sys,ast,json,hashlib,importlib.util,warnings
from pathlib import Path
cpus=sorted(set(os.sched_getaffinity(0))-{0,1});assert cpus;os.sched_setaffinity(0,{cpus[0]});os.nice(10)
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(60)
R=Path(__file__).resolve().parent;ROOT=R.parents[3];C=R.parent/'matching-small-pair-kernel-acceleration01-2026-10-09';sys.path.insert(0,str(ROOT));h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((C/'MANIFEST01.json').read_bytes())
for p,v in m['baseline'].items():assert h(ROOT/p)==v
for p,v in m['runtime_dependencies'].items():assert h(ROOT/p)==v
for p,v in m['files'].items():assert h(C/p)==v['sha256'] and (C/p).stat().st_size==v['bytes']
build=ast.parse((C/'build.py').read_bytes());helper=ast.literal_eval(next(n.value for n in build.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helper' for t in n.targets)));oldpath=ROOT/next(iter(m['baseline']));newtext=(C/'matching_annealing.py').read_text();inverse=newtext.replace('\n'+helper+'def _immutable_edges(graph):','\ndef _immutable_edges(graph):').replace('block-=_matrix_logsumexp(','block-=logsumexp(');assert inverse==oldpath.read_text()
import numpy as np
from tradingagents.research.onchain_replication import matching_annealing as old
from tradingagents.research.onchain_replication.contracts import AttributedGraph
spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication._small_review',C/'matching_annealing.py');new=importlib.util.module_from_spec(spec);spec.loader.exec_module(new)
def result(fn,a,axis,keepdims,under):
 original=a.tobytes() if isinstance(a,np.ndarray) else None
 with warnings.catch_warnings(record=True) as ws:
  warnings.simplefilter('always')
  try:
   with np.errstate(under=under):v=fn(a,axis=axis,keepdims=keepdims)
   out=('ok',np.asarray(v).dtype.str,np.shape(v),np.asarray(v).tobytes())
  except Exception as e:out=(type(e).__name__,str(e))
 if original is not None:assert original==a.tobytes()
 return out,[(w.category.__name__,str(w.message)) for w in ws]
readonly=np.array([[np.nextafter(0.,1.),-0.],[0.,1.]]);readonly.flags.writeable=False
cases=[readonly,np.arange(15.,dtype=np.float64).reshape(3,5)[::-1,::-2],np.array([[np.inf],[-np.inf],[np.nan]]),np.array([[1.,2.],[3.,4.]],dtype=np.float32)]
comparisons=0
for a in cases:
 for axis in (0,1):
  for under in ('raise','warn'):assert result(old.logsumexp,a,axis,True,under)==result(new._matrix_logsumexp,a,axis,True,under);comparisons+=1
for a,axis,keepdims in [([],0,True),(np.zeros((0,2)),1,True),([[1,2],[3,4]],None,False),(np.array([[1+1j]]),0,True)]:assert result(old.logsumexp,a,axis,keepdims,'ignore')==result(new._matrix_logsumexp,a,axis,keepdims,'ignore');comparisons+=1
# Public and private callable substitutions trigger the declared fallback.
original=new.logsumexp;new.logsumexp=lambda *a,**k:'fallback';assert new._matrix_logsumexp(np.ones((2,2)),axis=1,keepdims=True)=='fallback';new.logsumexp=original
inner=original.__globals__['_logsumexp'];hits=[]
def replacement(*a,**k):hits.append(1);return inner(*a,**k)
try:
 original.__globals__['_logsumexp']=replacement
 a=np.array([[1.,2.]]);assert result(old.logsumexp,a,1,True,'ignore')==result(new._matrix_logsumexp,a,1,True,'ignore');assert len(hits)==2
finally:original.__globals__['_logsumexp']=inner
cfg=json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_bytes())
def graph(n):
 es=np.array([(i,(i+1)%n) for i in range(n) if n>1],dtype=np.int64).reshape(-1,2).T.copy();return AttributedGraph(tuple(map(str,range(n))),np.arange(n*2,dtype=np.float64).reshape(n,2)*.03125,es,np.arange(es.shape[1]*2,dtype=np.float64).reshape(-1,2)*.0625,'a'*64,'0')
def equal(a,b):
 assert a.keys()==b.keys()
 for k in a:
  if isinstance(a[k],np.ndarray):assert (a[k].dtype,a[k].shape,a[k].tobytes())==(b[k].dtype,b[k].shape,b[k].tobytes()),k
  else:assert a[k]==b[k],k
runs=[]
for n,m in ((1,2),(3,4)):
 a,b=graph(n),graph(m);x=old.create(a,b,cfg,max_state_bytes=1000000,max_chunk_entries=16);y=new.create(a,b,cfg,max_state_bytes=1000000,max_chunk_entries=16);count=0
 while x['phase']!='done':
  budget=(2,13,4096)[count%3];assert old.advance(x,a,b,cfg,max_operations=budget)==new.advance(y,a,b,cfg,max_operations=budget);equal(x,y);count+=1
 assert repr(old.result(x,a,b,cfg))==repr(new.result(y,a,b,cfg));runs.append({'shape':[n,m],'operation_boundaries':count})
report={'status':'PASS_SYNTHETIC_ONLY','affinity':sorted(os.sched_getaffinity(0)),'normalization_comparisons':comparisons,'runs':runs,'all_state_and_result_bytes_equal':True,'public_private_substitution_fallback':True,'literal_inverse':True,'runtime_dependency_hashes':json.loads((C/'MANIFEST01.json').read_bytes())['runtime_dependencies'],'qualification':'No timing benchmark. Exact pinned ordinary namespace domain only; private-library/public-dispatch changes outside guarded identities require new review; allocation/asynchronous/profiler trace equivalence unsupported.'};(R/'CHECK01.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
