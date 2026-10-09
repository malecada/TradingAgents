import os,resource,signal,time,json,subprocess,sys,statistics,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT))
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,60),(resource.RLIMIT_FSIZE,4*1024**2)]:resource.setrlimit(k,(v,v))
signal.alarm(60);start=time.monotonic_ns()
receipt={'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'alarm_seconds':60}
(P/'LIMITER01.json').write_text(json.dumps(receipt,indent=2)+'\n');assert receipt['affinity']==[3]
cmd=['/usr/bin/cc','-std=c11','-O3','-fno-fast-math','-ffp-contract=off','-fPIC','-shared',str(P/'normalization.c'),'-lm','-o',str(P/'normalization.so')]
r=subprocess.run(cmd,capture_output=True,text=True);(P/'COMPILE01.json').write_text(json.dumps({'argv':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'compiler':subprocess.check_output(['/usr/bin/cc','--version'],text=True)},indent=2)+'\n');assert r.returncode==0
import numpy as np
from scipy.special import logsumexp
from tradingagents.research.onchain_replication import matching_annealing as ann,matching_reference as ref
from tradingagents.research.onchain_replication.contracts import AttributedGraph
import prototype
config=json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/config/matching.json').read_text())
def graph(n,offset,edges=True,tie=False):
 ids=tuple(f'n{i}' for i in range(n));features=np.zeros((n,2)) if tie else np.array([[.13*i+offset,.17*i-offset] for i in range(n)],dtype=np.float64)
 index=np.array([(i,(i+1)%n) for i in range(n)] if edges and n>1 else [],dtype=np.int64).reshape(-1,2).T.copy()
 return AttributedGraph(ids,features,index,np.array([[.11*i+offset] for i in range(index.shape[1])],dtype=np.float64).reshape(-1,1),'a'*64,ids[0])
cases=[]
for n,m,edges,tie in [(1,1,False,False),(1,4,False,False),(4,1,False,False),(2,3,True,False),(4,4,True,False),(3,3,False,True),(8,5,True,False)]:
 a,b=graph(n,.03,edges,tie),graph(m,.09,edges,tie)
 baseline=ref.match_reference(a,b,config);got=prototype.match(a,b,config)
 state=ann.create(a,b,config,max_state_bytes=1048576,max_chunk_entries=1024)
 while state['phase']!='done':ann.advance(state,a,b,config,max_operations=100000)
 installed=ann.result(state,a,b,config)
 row={'shape':[n,m],'edges':edges,'tie':tie,'iterations':got.iterations,'soft_max_abs':float(np.max(np.abs(got.soft_assignment-installed.soft_assignment))),'soft_bits_equal':got.soft_assignment.tobytes()==installed.soft_assignment.tobytes(),'score_abs':abs(got.score-installed.score),'assignment_equal':bool(np.array_equal(got.assignment,installed.assignment)),'reference_assignment_equal':bool(np.array_equal(got.assignment,baseline.assignment))}
 cases.append(row);(P/'CASES01.json').write_text(json.dumps(cases,indent=2)+'\n')
 assert row['assignment_equal'] and row['reference_assignment_equal'] and row['score_abs']<=1e-12 and row['soft_max_abs']<=1e-12
 assert got.iterations==baseline.iterations==installed.iterations and got.convergence==installed.convergence
# Only the finite supported input domain is offered; no automatic production fallback.
for q in [np.array([[-1.]]),np.array([[np.inf]]),np.zeros((33,1)),np.zeros((2,2),dtype=np.float32)]:
 try:prototype.normalize(q,1.)
 except ValueError:pass
 else:raise AssertionError('unsupported accepted')
a,b=graph(3,.03),graph(3,.09)
def bench(fn,count):
 times=[]
 for _ in range(5):
  t=time.perf_counter_ns()
  for _ in range(count):fn()
  times.append((time.perf_counter_ns()-t)/count)
 return {'ns_per_call_samples':times,'median_ns':statistics.median(times)}
base=bench(lambda:ref.match_reference(a,b,config),8);fast=bench(lambda:prototype.match(a,b,config),8)
q=np.array([[.1,.3,.5],[.7,.2,.4],[.6,.9,.8]])
def baseline_normalize():
 x=3.*q;x-=logsumexp(x,axis=1,keepdims=True);x-=logsumexp(x,axis=0,keepdims=True);return np.exp(x)
bn=bench(baseline_normalize,100);cn=bench(lambda:prototype.normalize(q,3.),100)
result={'status':'PASS_FINITE_PROTOTYPE_ONLY','cases':cases,'full_synthetic_match':{'baseline':base,'prototype':fast,'median_ratio':base['median_ns']/fast['median_ns']},'normalization':{'baseline':bn,'prototype':cn,'median_ratio':bn['median_ns']/cn['median_ns']},'elapsed_ns':time.monotonic_ns()-start,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'numpy_version':np.__version__}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
