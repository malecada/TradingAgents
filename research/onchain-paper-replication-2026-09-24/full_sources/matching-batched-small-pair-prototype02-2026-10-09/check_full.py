import os,resource,signal,sys,time,json,hashlib,statistics,struct
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3]
os.sched_setaffinity(0,{3});os.nice(10)
for key,val in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,25),(resource.RLIMIT_FSIZE,4*1024**2)]:resource.setrlimit(key,(val,val))
signal.setitimer(signal.ITIMER_REAL,25)
limits={'affinity':sorted(os.sched_getaffinity(0)),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'wall_remaining':signal.getitimer(signal.ITIMER_REAL)[0],'nice':os.getpriority(os.PRIO_PROCESS,0),'threads':{k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']}}
assert limits['affinity']==[3] and limits['FSIZE']==(4194304,)*2
(D/'LIMITER_FULL01.json').write_text(json.dumps(limits,indent=2)+'\n');started=time.perf_counter();sys.path.insert(0,str(R))
import numpy as np
import full_advance as fast
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from tradingagents.research.onchain_replication import compact_policy,matching_pair
engine=fast.engine;ann=engine.ann
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
checks=[];all_groups=[];checkpoint=None;count=0
for case,budgets in [('current_1m',[1000000]*16),('exact_completion_boundary',[5636]*16),('mixed_partial',[1,20,21,30,134,135,136,137,5635,5636,5637,1000000,1000000,1000000,1000000,1000000])]:
 old=create();new=create()
 try:
  expected=sequential(old,budgets);actual,diag=fast.advance_batch(new,pairs,c,budgets);assert expected==actual
  for x,y in zip(old,new,strict=True):equal(x,y);count+=1
  all_groups.append({'case':case,'budgets':budgets,'used':actual,'diagnostic':diag,'phases':[(s['phase'],s['annealing']['phase'],s['annealing']['cursor']) for s in new]})
  if case=='current_1m':
   assert diag['fast_groups'] and actual==[5636]*16 and all(s['phase']=='hardening' for s in new)
   dest=D/'checkpoint_full';digest=engine.save(new[0],dest,*pairs[0],c,max_checkpoint_bytes=p['max_checkpoint_bytes'],checkpoint_layout={'format':'sharded-npy-v1','chunk_entries':262144})
   restored=engine.load(dest,*pairs[0],c,expected_sha256=digest,**policy,checkpoint_layout={'format':'sharded-npy-v1','chunk_entries':262144});equal(restored,new[0]);engine.close(new[0]);new[0]=restored
   checkpoint={'sha256':digest,'files':{str(q.relative_to(dest)):hashlib.sha256(q.read_bytes()).hexdigest() for q in dest.rglob('*') if q.is_file()}}
  for _ in range(3):
   expected=sequential(old,[1000000]*16);actual,diag=fast.advance_batch(new,pairs,c,[1000000]*16);assert expected==actual
   for x,y in zip(old,new,strict=True):equal(x,y);count+=1
  for x,y,(a,b) in zip(old,new,pairs,strict=True):
   assert x['phase']==y['phase']=='done';xo=engine.result(x,a,b,c);yo=engine.result(y,a,b,c);assert xo.assignment.tobytes()==yo.assignment.tobytes() and struct.pack('>d',xo.score)==struct.pack('>d',yo.score) and xo.iterations==yo.iterations==48
  checks.append(case)
 finally:fast.close_all(old);fast.close_all(new)
# Each actual admitted group respects exact fixed ceiling; impossible 2-item scratch domain falls back.
assert fast.scratch_bound(2,16,16,1024)>262144
assert all(g['scratch_charge_bytes']<=262144 for row in all_groups for g in row['diagnostic']['fast_groups'])
# Actual ownership cleanup on an invalid second budget; all original arrays released.
s=create();primary=None
try:fast.advance_batch(s,pairs,c,[1,0]+[1]*14)
except ValueError as error:primary=error;assert str(error)=='positive operation allowance required'
else:raise AssertionError('invalid budget passed')
assert all(not v['safe'] and v['annealing'] is None for v in s);checks.append('invalid budget primary and actual all-state close')
original_close=engine.close;seen=[];cleanup=OSError('cleanup')
def broken(state):
 seen.append(state)
 if state==1:raise cleanup
try:
 engine.close=broken;fast.close_all([0,1,2],primary);assert seen==[0,1,2] and any('cleanup' in n for n in primary.__notes__)
 seen.clear()
 try:fast.close_all([0,1,2])
 except OSError as error:assert error is cleanup and seen==[0,1,2]
 else:raise AssertionError('cleanup-only silently accepted')
finally:engine.close=original_close
checks.append('cleanup errors preserve primary and attempt all closes')
raw=[]
for rep in range(4):
 row={'rep':rep}
 for label in (['old','candidate'] if rep%2==0 else ['candidate','old']):
  t=time.perf_counter();s=create();row[label+'_setup']=time.perf_counter()-t
  try:
   t=time.perf_counter()
   if label=='old':sequential(s,[1000000]*16)
   else:_,diag=fast.advance_batch(s,pairs,c,[1000000]*16);row['groups']=diag['fast_groups']
   row[label]=time.perf_counter()-t
  finally:fast.close_all(s)
 raw.append(row)
med={label:statistics.median(r[label] for r in raw) for label in ['old','candidate','old_setup','candidate_setup']};med['ratio']=med['old']/med['candidate']
result={'status':'PASS_SYNTHETIC_ONLY','checks':checks,'full_state_comparisons':count,'groups':all_groups,'checkpoint':checkpoint,'raw_timings':raw,'medians':med,'elapsed_seconds':time.perf_counter()-started,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limits':limits,'configuration':c,'policy':policy}
(D/'RESULT_FULL01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'medians':med,'comparisons':count,'elapsed':result['elapsed_seconds']}))
