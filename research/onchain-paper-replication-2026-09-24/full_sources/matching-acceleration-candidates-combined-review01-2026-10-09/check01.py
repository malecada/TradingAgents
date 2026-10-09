import os,resource,signal,sys,json,importlib.util,hashlib,errno,struct
from pathlib import Path
R=Path(__file__).resolve().parent;F=R.parent;P=F/'matching-compiled-small-pair-prototype03-2026-10-09';B=F/'matching-batched-small-pair-prototype01-2026-10-09';ROOT=Path.cwd()
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in ((resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)):resource.setrlimit(k,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
(R/'LIMITS01.json').write_text(json.dumps({'affinity':list(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'wall_remaining':signal.getitimer(signal.ITIMER_REAL)[0],'threads':{k:os.environ[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}})+'\n');sys.path.insert(0,str(ROOT))
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
h=load('sealed03_review',P/'compiled_small_lse.py');assert h._fn is not None and h._live();fd=h._fd
body=os.pread(fd,65537,0);assert hashlib.sha256(body).hexdigest()==h._EXPECTED and h.fcntl.fcntl(fd,h._F_GET_SEALS)==15
for action in (lambda:os.pwrite(fd,b'x',0),lambda:os.ftruncate(fd,0),lambda:os.ftruncate(fd,len(body)+1)):
 try:action()
 except OSError as e:assert e.errno==errno.EPERM
 else:raise AssertionError('seal failed')
import numpy as np
q=np.array([[.2,.7],[-.8,.9]])
expected=h.lse(q,axis=1,keepdims=True,fallback=h._original);h._PATH=R/'absent.so'
assert h.lse(q,axis=1,keepdims=True,fallback=h._original).tobytes()==expected.tobytes() and h._load_sealed() is None
h.close();h.close();assert not h._live() and h._fd is None and h._fn is None
try:os.fstat(fd)
except OSError as e:assert e.errno==errno.EBADF
else:raise AssertionError('fd retained')
assert h.lse(q,axis=1,keepdims=True,fallback=h._original).tobytes()==h._original(q,axis=1,keepdims=True).tobytes()
b=load('batch_review',B/'batched_small.py')
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from tradingagents.research.onchain_replication import compact_policy,matching_pair
c=json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_bytes());pc=json.loads((F/'real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json').read_bytes())['stage_policy']['pair'];c=compact_policy.effective_matching(c,pc);p=compact_policy.pair_policy(pc);policy={k:p[k] for k in matching_pair.ENGINE_FIELDS}
def graph(n,shift):
 ids=tuple('s'+str(i) for i in range(n));edges=np.array([(i,(i+1)%n) for i in range(n)],dtype=np.int64).T.copy();return AttributedGraph(ids,np.array([[shift+.07*i,shift-.02*i] for i in range(n)]),edges,np.array([[shift+.03*i] for i in range(n)]),'c'*64,ids[0])
pairs=[(graph(2,.02+k*.013),graph(3,.04+k*.017)) for k in range(2)]
x,_,_=b.sequential(pairs,c,policy);y,_,meta=b.match_batch(pairs,c,policy);assert meta['route']=='batched_prototype'
results=[]
for a,z in zip(x,y,strict=True):
 row={'iterations':z.iterations,'convergence_equal':a.convergence==z.convergence,'assignment_equal':a.assignment.tobytes()==z.assignment.tobytes(),'score_bits_equal':struct.pack('d',a.score)==struct.pack('d',z.score)};results.append(row);assert all(row[k] for k in ('convergence_equal','assignment_equal','score_bits_equal')) and a.iterations==z.iterations==48
(R/'RESULT01.json').write_text(json.dumps({'sealed_body_bytes':len(body),'seal_mask':15,'kernel_three_mutations_refused':True,'missing_path_existing_lifetime_unchanged':True,'new_missing_load_fallback':True,'double_close_disabled_and_fd_reaped':True,'batch_shape':[2,3],'pairs':2,'results':results,'batch_metadata':meta,'qualification':'One fresh combined fixture; no timing or prior matrix replay; final-result equivalence only for new batch fixture.'},indent=2)+'\n')
