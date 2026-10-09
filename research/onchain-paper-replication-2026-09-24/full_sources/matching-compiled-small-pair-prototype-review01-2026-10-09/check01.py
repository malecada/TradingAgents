import os,resource,signal,sys,json,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parent;P=R.parent/'matching-compiled-small-pair-prototype01-2026-10-09';ROOT=Path.cwd()
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in ((resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)):resource.setrlimit(k,(v,v))
signal.alarm(30)
limits={'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'threads':{k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}}
(R/'LIMITS01.json').write_text(json.dumps(limits,indent=2)+'\n')
sys.path[:0]=[str(ROOT),str(P)]
import numpy as np
from scipy.special import logsumexp
import prototype
rng=np.random.default_rng(84731);rows=[]
for n,m in ((2,31),(31,2),(17,32),(32,17),(32,32)):
 for scale in (1e-12,1.,1000.):
  q=np.ascontiguousarray(rng.random((n,m))*scale);q[:,::3]=q[:,0:1] # repeated maxima candidates / reduction width
  x=q*1.37;x-=logsumexp(x,axis=1,keepdims=True);x-=logsumexp(x,axis=0,keepdims=True);expected=np.exp(x)
  got=prototype.normalize(q,1.37);error=float(np.max(np.abs(got-expected)))
  rows.append({'shape':[n,m],'scale':scale,'max_abs':error,'bits_equal':got.tobytes()==expected.tobytes()});assert error<=1e-12
# Explicit unsupported warning/error equivalence is observable even in finite accepted domain.
q=np.array([[0.,1000.],[1000.,0.]])
with np.errstate(under='raise'):
 try:
  x=q.copy();x-=logsumexp(x,axis=1,keepdims=True);x-=logsumexp(x,axis=0,keepdims=True);np.exp(x)
 except FloatingPointError as e:baseline_error=type(e).__name__
 else:baseline_error=None
 got=prototype.normalize(q,1.);c_returned=bool(np.isfinite(got).all())
assert baseline_error=='FloatingPointError' and c_returned
v={'checks':rows,'nonbitwise_cases':sum(not x['bits_equal'] for x in rows),'max_abs':max(x['max_abs'] for x in rows),'error_mode_counterexample':{'input':[[0,1000],[1000,0]],'numpy_errstate_under':'raise','original':baseline_error,'prototype_returns_finite':c_returned},'qualification':'Distinct normalization-only synthetic cases; no new whole-match/checkpoint proof or timing benchmark.'}
(R/'RESULT01.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
