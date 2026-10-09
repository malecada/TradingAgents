import sys,json,time,hashlib,os,statistics,struct
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];sys.path.insert(0,str(R));started=time.perf_counter()
import numpy as np
from tradingagents.research.onchain_replication import batched_pair_executor as pe,batched_numeric_reuse as memo
from tradingagents.research.onchain_replication.contracts import AttributedGraph
refs={}
def load(p):
 raw=p.read_bytes();refs[str(p.relative_to(R))]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
c=load(R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json')
fixture=load(R/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json')['stage_policy'];p=fixture['pair'];s=fixture['schedule']
def graph(n):
 e=np.array([(i,j) for i in range(n) for j in range(n) if i!=j and (i+j)%3],dtype=np.int64).T.copy()
 return AttributedGraph(tuple('n'+str(i) for i in range(n)),np.arange(n*2,dtype=np.float64).reshape(n,2)*.01,e,np.arange(e.shape[1]*2,dtype=np.float64).reshape(-1,2)*.02,'a'*64,'n0')
def no_checkpoint(*args):raise AssertionError('unexpected synthetic checkpoint')
def measure(fn):
 t=time.perf_counter();v=fn();return v,time.perf_counter()-t
purpose_counter=0
def purpose():
 global purpose_counter
 purpose_counter+=1;return hashlib.sha256(str(purpose_counter).encode()).hexdigest()
def bits(v):return struct.pack('>d',v[0]).hex(),v[1],v[2]
rows=[];staged=[];components=[]
for shape in [(4,5),(8,7)]:
 a,b=map(graph,shape)
 for rep in range(6):
  row={'shape':shape,'edges':[a.edge_index.shape[1],b.edge_index.shape[1]],'rep':rep}
  direct=pe.PairExecutor(c,p,s,no_checkpoint,authority_poll=None)
  v,row['pair_executor']=measure(lambda:direct(a,b,purpose()))
  m,row['memo_constructor']=measure(lambda:memo.NumericReuseExecutor(c,p,s,no_checkpoint,max_entries=8,max_retained_bytes=65536,max_key_bytes=32768,authority_poll=None))
  try:
   _,row['memo_begin']=measure(m.begin_batch)
   miss,row['memo_miss']=measure(lambda:m(a,b,purpose()));assert m.last_receipt['mode']=='computed'
   hit_times=[]
   for j in range(4):
    hit,dt=measure(lambda:m(a,b,purpose()));assert m.last_receipt['mode']=='reused';assert bits(hit)==bits(miss)==bits(v);hit_times.append(dt)
   row['memo_hits']=hit_times
   _,row['memo_end']=measure(m.end_batch);row['memo_counters']=dict(m.counters)
   # Separate ordinary method/function timing; no hook/wrapper/trace installed.
   part={'shape':shape,'rep':rep}
   for key,fn in [('memo_current',m._current),('validate_pair',lambda:memo.reference.validate_pair(a,b,c)),('policy_check',lambda:pe.pair.policy_check(a,b,c,p,allow_checkpoint_layout=True)),('numeric_key',lambda:memo.numeric_key(a,b,m.configuration,m.max_key_bytes))]:
    _,part[key]=measure(fn)
   components.append(part)
  finally:m.close()
  # Mirror exact executor numerical sequence, timing around calls only. No authority injected.
  timing={'shape':shape,'rep':rep};state=None;session=None
  try:
   _,timing['policy_check']=measure(lambda:pe.pair.policy_check(a,b,c,p,allow_checkpoint_layout=True))
   state,timing['create']=measure(lambda:pe.engine.create(a,b,c,**{k:p[k] for k in pe.pair.ENGINE_FIELDS}))
   session,timing['session_constructor']=measure(lambda:pe.ImmutablePairSession(a,b,c,engine=pe.engine,annealing=pe.annealing))
   advance_times=[]
   for _ in range(s['calls_per_checkpoint']):
    _,dt=measure(lambda:session.advance(state,max_operations=s['operations_per_call']));advance_times.append(dt)
    if state['phase']=='done':break
   assert state['phase']=='done'
   timing['advance']=advance_times
   result,timing['score']=measure(lambda:pe.engine.score_only(state,a,b,c,max_buffer_bytes=p['max_score_buffer_bytes'],chunk_edges=p['chunk_edges']))
   assert bits((float(result.score),result.iterations,result.convergence))==bits(v)
  finally:
   if session is not None:_,timing['session_close']=measure(session.close)
   if state is not None:_,timing['state_close']=measure(lambda:pe.engine.close(state))
  bare=pe.annealing.create(a,b,c,max_state_bytes=p['max_state_bytes'],max_chunk_entries=p['normalization_chunk_entries'])
  _,timing['bare_annealing_advance']=measure(lambda:pe.annealing._advance_checked(bare,a,b,c,max_operations=s['operations_per_call']))
  assert bare['phase']=='done';staged.append(timing);rows.append(row)
summary={}
for shape in [(4,5),(8,7)]:
 rr=[r for r in rows if r['shape']==shape];ss=[r for r in staged if r['shape']==shape];cc=[r for r in components if r['shape']==shape]
 summary[str(shape)]={'route_medians':{k:statistics.median(r[k] for r in rr) for k in ['pair_executor','memo_constructor','memo_begin','memo_miss','memo_end']},'memo_hit_median':statistics.median(t for r in rr for t in r['memo_hits']),'staged_medians':{k:statistics.median(sum(r[k]) if k=='advance' else r[k] for r in ss) for k in ['policy_check','create','session_constructor','advance','score','session_close','state_close','bare_annealing_advance']},'independent_component_medians':{k:statistics.median(r[k] for r in cc) for k in ['memo_current','validate_pair','policy_check','numeric_key']}}
for module in [pe,memo,*memo.MODULES]:
 path=Path(module.__file__);refs[str(path.relative_to(R))]=hashlib.sha256(path.read_bytes()).hexdigest()
out={'status':'SYNTHETIC_NO_AUTHORITY','authority_poll':None,'affinity':sorted(os.sched_getaffinity(0)),'numpy':np.__version__,'python':sys.version,'runtime_seconds':time.perf_counter()-started,'config':c,'policy':p,'schedule':s,'raw_route':rows,'raw_staged':staged,'raw_components':components,'summary':summary,'source_refs':refs,'checkpoint_calls':0,'all_result_bits_equal':True,'method':'No profiling hooks or source mutation. Repeated actual PairExecutor/memo calls; separate staged numerical sequence timed around original call boundaries. Staged timing is attribution experiment, not instrumented original route. All six repetitions retained without trimming.'}
(D/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(summary,indent=2));print('runtime_seconds',out['runtime_seconds'])
