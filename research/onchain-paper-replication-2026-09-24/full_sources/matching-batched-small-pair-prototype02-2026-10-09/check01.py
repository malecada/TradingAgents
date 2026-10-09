import os,resource,signal,sys,time,json,hashlib,statistics,struct
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3]
os.sched_setaffinity(0,{3});os.nice(10)
for key,val in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)]:resource.setrlimit(key,(val,val))
signal.setitimer(signal.ITIMER_REAL,30)
limits={'affinity':sorted(os.sched_getaffinity(0)),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'wall_remaining':signal.getitimer(signal.ITIMER_REAL)[0],'nice':os.getpriority(os.PRIO_PROCESS,0),'threads':{k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']}}
assert limits['affinity']==[3] and limits['FSIZE']==(4194304,)*2
(D/'LIMITER01.json').write_text(json.dumps(limits,indent=2)+'\n');started=time.perf_counter();sys.path.insert(0,str(R))
import numpy as np
import normalization_wave as wave
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from tradingagents.research.onchain_replication import compact_policy,matching_pair
engine=wave.engine;ann=engine.ann
F=R/'research/onchain-paper-replication-2026-09-24/full_sources'
c=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_bytes());p=json.loads((F/'real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json').read_bytes())['stage_policy']['pair'];c=compact_policy.effective_matching(c,p);p=compact_policy.pair_policy(p);policy={k:p[k] for k in matching_pair.ENGINE_FIELDS}
def graph(n,shift):
 e=np.array([(i,j) for i in range(n) for j in range(n) if i!=j and (i+j)%3],dtype=np.int64).T.copy()
 return AttributedGraph(tuple('n'+str(i) for i in range(n)),np.arange(n*2,dtype=np.float64).reshape(n,2)*.01+shift,e,np.arange(e.shape[1]*2,dtype=np.float64).reshape(-1,2)*.02+shift,'a'*64,'n0')
pairs=[(graph(4,k*.007),graph(5,k*.011)) for k in range(16)]
def create():return [engine.create(a,b,c,**policy) for a,b in pairs]
def sequential(states,budgets):return [engine.advance(s,a,b,c,max_operations=n) for s,(a,b),n in zip(states,pairs,budgets,strict=True)]
def equal(x,y):
 if isinstance(x,np.ndarray):assert x.dtype==y.dtype and x.shape==y.shape and x.flags.writeable==y.flags.writeable and x.tobytes()==y.tobytes()
 elif isinstance(x,dict):
  assert x.keys()==y.keys()
  for k in x:equal(x[k],y[k])
 elif isinstance(x,(list,tuple)):
  assert type(x)==type(y) and len(x)==len(y)
  for a,b in zip(x,y,strict=True):equal(a,b)
 else:assert x==y,(x,y)
old=create();new=create();comparisons=0;waves=0;peak=0;calls=[]
try:
 for budgets in [[20]*16,[114]*16,[1]*16,[1 if i<8 else 2 for i in range(16)],[7+i%4 for i in range(16)],[1]*16,[121-i%3 for i in range(16)],[1000000]*16,[1000000]*16,[1000000]*16]:
  a=sequential(old,budgets);b,diag=wave.advance_batch(new,pairs,c,budgets);assert a==b
  for x,y in zip(old,new,strict=True):equal(x,y);comparisons+=1
  waves+=diag['waves'];peak=max(peak,diag['max_scratch_charge_bytes']);calls.append({'budgets':budgets,'used':b,'diagnostic':diag,'phase':[(s['phase'],s['annealing']['phase'],s['annealing']['cursor']) for s in new]})
  if len(calls)==3:
   # Actual original composite checkpoint, taken immediately after a batch wave.
   dest=D/'checkpoint';digest=engine.save(new[0],dest,*pairs[0],c,max_checkpoint_bytes=p['max_checkpoint_bytes'],checkpoint_layout={'format':'sharded-npy-v1','chunk_entries':262144})
   loaded=engine.load(dest,*pairs[0],c,expected_sha256=digest,**policy,checkpoint_layout={'format':'sharded-npy-v1','chunk_entries':262144});equal(loaded,new[0]);engine.close(new[0]);new[0]=loaded;checkpoint={'sha256':digest,'files':{str(q.relative_to(dest)):hashlib.sha256(q.read_bytes()).hexdigest() for q in dest.rglob('*') if q.is_file()}}
 assert all(s['phase']=='done' for s in new)
 for x,y,(a,b) in zip(old,new,pairs,strict=True):
  xo=engine.result(x,a,b,c);yo=engine.result(y,a,b,c);assert xo.assignment.tobytes()==yo.assignment.tobytes() and struct.pack('>d',xo.score)==struct.pack('>d',yo.score) and xo.iterations==yo.iterations==48
finally:wave.close_all(old);wave.close_all(new)
# Resource refusal for batch workspace falls back original; no enlarged allocation.
assert wave.scratch_bound(32,16,16)>262144
# Real remaining closes attempted under injected cleanup-only and primary failures.
original_close=engine.close;seen=[];primary=RuntimeError('original primary');cleanup=OSError('cleanup')
def broken(s):
 seen.append(s)
 if s==1:raise cleanup
try:
 engine.close=broken;wave.close_all([0,1,2],primary);assert seen==[0,1,2] and any('cleanup' in n for n in primary.__notes__)
 seen.clear()
 try:wave.close_all([0,1,2])
 except OSError as error:assert error is cleanup and seen==[0,1,2]
 else:raise AssertionError('cleanup-only must refuse')
finally:engine.close=original_close
# Four fixed alternating repetitions: eligible row wave and ordinary full-budget route.
def prepare(kind):
 s=create()
 if kind=='row':sequential(s,[134]*16) # nodes20 + outer1 + edges112 +scale1
 return s
raw=[]
for kind in ['row','full']:
 for rep in range(4):
  row={'kind':kind,'rep':rep}
  for label in (['old','candidate'] if rep%2==0 else ['candidate','old']):
   t=time.perf_counter();s=prepare(kind);row[label+'_setup']=time.perf_counter()-t
   try:
    budgets=[1 if kind=='row' else 1000000]*16;t=time.perf_counter()
    if label=='old':sequential(s,budgets)
    else:_,diag=wave.advance_batch(s,pairs,c,budgets);row['waves']=diag['waves']
    row[label]=time.perf_counter()-t
   finally:wave.close_all(s)
  raw.append(row)
summary={k:{label:statistics.median(r[label] for r in raw if r['kind']==k) for label in ['old','candidate','old_setup','candidate_setup']} for k in ['row','full']}
for v in summary.values():v['ratio']=v['old']/v['candidate']
result={'status':'PASS_SYNTHETIC_ONLY','comparisons':comparisons,'waves':waves,'max_scratch_charge_bytes':peak,'checkpoint':checkpoint,'calls':calls,'cleanup_primary_preserved_all_attempted':True,'raw_timings':raw,'summary':summary,'elapsed_seconds':time.perf_counter()-started,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limits':limits,'configuration':c,'policy':policy}
(D/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'summary':summary,'waves':waves,'elapsed':result['elapsed_seconds']}))
