import resource,signal,os,time,json,hashlib,sys,struct,statistics
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3]
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)]:resource.setrlimit(k,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
limits={'affinity':sorted(os.sched_getaffinity(0)),'as':resource.getrlimit(resource.RLIMIT_AS),'cpu':resource.getrlimit(resource.RLIMIT_CPU),'fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'wall_timer_remaining':signal.getitimer(signal.ITIMER_REAL)[0],'nice':os.getpriority(os.PRIO_PROCESS,0)}
assert limits['affinity']==[3] and limits['fsize']==(4194304,4194304)
(D/'LIMITER02.json').write_text(json.dumps(limits,indent=2)+'\n');start=time.perf_counter();sys.path.insert(0,str(R));import numpy as np
import batched_small as candidate
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from tradingagents.research.onchain_replication import compact_policy
F=R/'research/onchain-paper-replication-2026-09-24/full_sources'
c=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_bytes());pc=json.loads((F/'real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json').read_bytes())['stage_policy']['pair'];c=compact_policy.effective_matching(c,pc);p=compact_policy.pair_policy(pc);policy={k:p[k] for k in candidate.engine.ann.NAMES} if False else {k:p[k] for k in __import__('tradingagents.research.onchain_replication.matching_pair',fromlist=['ENGINE_FIELDS']).ENGINE_FIELDS}
def graph(n,shift):
 e=np.array([(i,j) for i in range(n) for j in range(n) if i!=j and (i+j)%3],dtype=np.int64).T.copy()
 return AttributedGraph(tuple('n'+str(i) for i in range(n)),np.arange(n*2,dtype=np.float64).reshape(n,2)*.01+shift,e,np.arange(e.shape[1]*2,dtype=np.float64).reshape(-1,2)*.02+shift,'a'*64,'n0')
t=time.perf_counter();pairs=[(graph(4,k*.007),graph(5,k*.011)) for k in range(16)];setup=time.perf_counter()-t
old,ot,om=candidate.sequential(pairs,c,policy,True);new,nt,nm=candidate.match_batch(pairs,c,policy,True)
state_mismatches=[];max_abs=0.;assignment_equal=True;score_bits_equal=True
for index,(a,b) in enumerate(zip(old,new,strict=True)):
 assert a.iterations==b.iterations==48 and a.convergence==b.convergence
 assignment_equal &= a.assignment.tobytes()==b.assignment.tobytes();score_bits_equal &= struct.pack('>d',a.score)==struct.pack('>d',b.score)
 assert len(ot[index])==len(nt[index])==48
 for iteration,(x,y) in enumerate(zip(ot[index],nt[index],strict=True),1):
  assert x[2:]==y[2:]
  for name,v,w in [('M',x[0],y[0]),('Q',x[1],y[1])]:
   max_abs=max(max_abs,float(np.max(np.abs(v-w))))
   if v.tobytes()!=w.tobytes():state_mismatches.append({'pair':index,'iteration':iteration,'state':name})
# Persist numerical comparison before any assertion so disagreements remain evidence.
proof={'pairs':16,'shapes':[4,5],'edges':[pairs[0][0].edge_index.shape[1],pairs[0][1].edge_index.shape[1]],'iterations':48,'state_comparisons':16*48*2,'state_mismatches':state_mismatches,'max_absolute_difference':max_abs,'assignment_equal':assignment_equal,'score_bits_equal':score_bits_equal,'prototype':nm,'graph_setup_seconds':setup}
(D/'EQUIVALENCE02.json').write_text(json.dumps(proof,indent=2)+'\n')
assert not state_mismatches and assignment_equal and score_bits_equal
# Fixed four alternating repetitions, after exactly one warmup each. No trace copies.
for fn in [candidate.sequential,candidate.match_batch]:fn(pairs,c,policy)
raw=[]
for rep in range(4):
 row={'rep':rep}
 for label,fn in ([('sequential',candidate.sequential),('batched',candidate.match_batch)] if rep%2==0 else [('batched',candidate.match_batch),('sequential',candidate.sequential)]):
  t=time.perf_counter();fn(pairs,c,policy);row[label]=time.perf_counter()-t
 raw.append(row)
assert candidate.match_batch([],c,policy)[2]['route']=='original_sequential'
med={k:statistics.median(x[k] for x in raw) for k in ['sequential','batched']}
result={'status':'PASS_SYNTHETIC_ONLY','limits':limits,'equivalence':proof,'timings':raw,'medians':med,'ratio':med['sequential']/med['batched'],'pairs_per_second':{k:16/v for k,v in med.items()},'elapsed_seconds':time.perf_counter()-start,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'config':c,'policy':policy,'runtime':{'python':sys.version,'numpy':np.__version__},'fallback_empty_list':True}
(D/'RESULT02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'ratio':result['ratio'],'medians':med,'elapsed':result['elapsed_seconds']}))
