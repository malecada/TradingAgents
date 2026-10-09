import copy,hashlib,json,os,resource,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[3]));sys.path.insert(0,str(P))
assert resource.getrlimit(resource.RLIMIT_AS)==(268435456,268435456)
assert resource.getrlimit(resource.RLIMIT_FSIZE)==(4194304,4194304)
assert len(os.sched_getaffinity(0))==2 and os.getpriority(os.PRIO_PROCESS,0)==10
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from tradingagents.research.onchain_replication.matching_reference import match_reference
import pair_executor as pe
import batch_journal as bj
c=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=3,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal')
policy=dict(max_state_bytes=65536,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=65536,max_score_buffer_bytes=65536,chunk_edges=8,max_checkpoint_bytes=262144,max_publications=100,total_checkpoint_bytes=1048576)
schedule=dict(max_checkpoints=100,calls_per_checkpoint=2,operations_per_call=3,max_total_checkpoints=1000,max_total_checkpoint_bytes=500000000)
a=AttributedGraph(('a','b'),np.array([[0.],[1.]]),np.array([[0,1],[1,0]],dtype=np.int64),np.array([[.2],[.3]]),'a'*64,'a');b=a
key='a'*64
# Original numeric wrapper loop, independent of candidate implementation.
def oracle():
 s=pe.engine.create(a,b,c,**{k:policy[k] for k in pe.pair.ENGINE_FIELDS});trace=[]
 try:
  for ordinal in range(schedule['max_checkpoints']):
   for _ in range(schedule['calls_per_checkpoint']):
    trace.append(('advance',s['phase'],s['annealing']['phase'],s['annealing']['cursor']))
    pe.engine.advance(s,a,b,c,max_operations=schedule['operations_per_call'])
    if s['phase']=='done':break
   if s['phase']=='done':
    r=pe.engine.score_only(s,a,b,c,max_buffer_bytes=policy['max_score_buffer_bytes'],chunk_edges=policy['chunk_edges']);return (r.score,r.iterations,r.convergence),trace
   trace.append(('checkpoint',ordinal,s['phase'],s['annealing']['cursor']))
 finally:pe.engine.close(s)
expected,trace=oracle();seen=[];closed=[]
advance=pe.engine.advance;close=pe.engine.close

def advance_spy(s,*args,**kw):
 seen.append(('advance',s['phase'],s['annealing']['phase'],s['annealing']['cursor']));return advance(s,*args,**kw)
def close_spy(s):closed.append(s);return close(s)
def checkpoint(k,i,s,*rest):
 assert k==key;seen.append(('checkpoint',i,s['phase'],s['annealing']['cursor']))
pe.engine.advance=advance_spy;pe.engine.close=close_spy
try:answer=pe.PairExecutor(c,policy,schedule,checkpoint)(a,b,key)
finally:pe.engine.advance=advance;pe.engine.close=close
assert answer==expected and seen==trace and len(closed)==1 and closed[0]['annealing'] is None
assert abs(answer[0]-match_reference(a,b,c).score)<=1e-12
# Exhausted schedule and checkpoint callback failure close state and poison.
for label,checkpoint_cb in [('stop',lambda *x:None),('callback',lambda *x:(_ for _ in ()).throw(RuntimeError('checkpoint-fail')))]:
 executor=pe.PairExecutor(c,policy,{**schedule,'max_checkpoints':1,'calls_per_checkpoint':1},checkpoint_cb)
 closed.clear();pe.engine.close=close_spy
 try:
  try:executor(a,b,key)
  except (pe.CheckpointStop,RuntimeError):pass
  else:raise AssertionError('missing failure')
 finally:pe.engine.close=close
 assert executor.poisoned and len(closed)==1 and closed[0]['annealing'] is None
# Batches retain exact order/hash/f64 bits; one callback at each batch boundary.
bounds=dict(batch_cells=2,max_cells=4,max_bytes=131072,max_body_bytes=8192)
boundaries=[];j=bj.BatchJournal(P/'journal',boundary=lambda:boundaries.append(1),**bounds)
executor=pe.PairExecutor(c,policy,{**schedule,'operations_per_call':1000},lambda *args:None)
tasks=[({'ordinal':i,'center':0,'motif':i},a,b) for i in range(2)]
records=j.run_batch(tasks,executor)
assert len(boundaries)==2 and j.cells==2
for i,r in enumerate(records):
 assert r['ordinal']==i and r['purpose_sha256']==bj.digest(bj.body(tasks[i][0])) and r['score_f64_be']==struct.pack('>d',expected[0]).hex()
pending=json.loads((P/'journal/00000000.pending.json').read_text());complete=json.loads((P/'journal/00000000.complete.json').read_text())
assert complete['pending_sha256']==bj.digest(bj.body(pending)) and complete['records']==records
j.close()
try:bj.BatchJournal(P/'journal',boundary=lambda:None,**bounds)
except FileExistsError:pass
else:raise AssertionError('namespace overwrite')
# Failure on later cell: only pending, whole attempted range stays unknown.
j=bj.BatchJournal(P/'partial',boundary=lambda:None,**bounds);calls=[]
def fail(a,b,key):
 calls.append(key)
 if len(calls)==2:raise RuntimeError('primary-cell-failure')
 return expected
try:j.run_batch(tasks,fail)
except RuntimeError as e:assert str(e)=='primary-cell-failure'
else:raise AssertionError('missing failure')
assert j.poisoned and j.cells==0 and (P/'partial/00000000.pending.json').exists() and not (P/'partial/00000000.complete.json').exists();j.close()
# Readback corruption refuses publication; no later numeric call.
j=bj.BatchJournal(P/'corrupt',boundary=lambda:None,**bounds);read=bj.os.read
bj.os.read=lambda fd,n: b'!' if n else b''
try:
 try:j.run_batch(tasks,lambda *args:(_ for _ in ()).throw(AssertionError('numeric entered')))
 except ValueError as e:assert 'readback' in str(e)
 else:raise AssertionError('corruption accepted')
finally:bj.os.read=read;j.close()
assert j.poisoned and not (P/'corrupt/00000000.complete.json').exists()
# Bounds refuse before pending or numeric work; every failure poisons.
for label,limits,requests in [('cells',{**bounds,'max_cells':1},tasks),('bytes',{**bounds,'max_bytes':1},tasks),('ordinal',bounds,[({'ordinal':1},a,b)])]:
 j=bj.BatchJournal(P/label,boundary=lambda:None,**limits)
 try:j.run_batch(requests,lambda *args:(_ for _ in ()).throw(AssertionError('numeric entered')))
 except ValueError:pass
 else:raise AssertionError('bound accepted')
 assert j.poisoned and not list((P/label).glob('*.pending.json'));j.close()
result={'status':'PASS','same_numeric_loop_trace':True,'advance_calls':sum(x[0]=='advance' for x in trace),'checkpoint_callbacks':sum(x[0]=='checkpoint' for x in trace),'score_bits':struct.pack('>d',answer[0]).hex(),'reference_tolerance':1e-12,'batch_boundaries':len(boundaries),'pending_failure_unknown':True,'readback_corruption_refused':True,'namespace_and_bounds_refused':True,'cleanup_verified':True,'affinity':sorted(os.sched_getaffinity(0)),'as_bytes':resource.getrlimit(resource.RLIMIT_AS)[0],'file_bytes':resource.getrlimit(resource.RLIMIT_FSIZE)[0]}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
