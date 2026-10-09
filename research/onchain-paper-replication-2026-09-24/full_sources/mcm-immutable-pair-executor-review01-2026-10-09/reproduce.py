"""Focused source seam failure injection, tiny synthetic graphs; no authority."""
import os,resource,signal,sys,importlib.util,json,hashlib
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent;sys.path.insert(0,str(R))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load('old_executor',F/'mcm-batched-execution03-2026-10-09/pair_executor.py');new=load('candidate',F/'mcm-immutable-pair-executor01-2026-10-09/pair_executor.py')
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
c=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=3,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal')
p=dict(max_state_bytes=65536,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=65536,max_score_buffer_bytes=65536,chunk_edges=8,max_checkpoint_bytes=262144,max_publications=100,total_checkpoint_bytes=1048576)
s=dict(max_checkpoints=1,calls_per_checkpoint=1,operations_per_call=1,max_total_checkpoints=1000,max_total_checkpoint_bytes=500000000)
a=AttributedGraph(node_ids=('a','b'),node_features=np.array([[0.],[1.]]),edge_index=np.array([[0,1],[1,0]],dtype=np.int64),edge_features=np.array([[.2],[.3]]),parent_hash='a'*64,center_id='a')
engine=new.engine;original_create=engine.create;original_close=engine.close;original_session_close=new.ImmutablePairSession.close
states=[];closed=[]
def create(*args,**kw):
 state=original_create(*args,**kw);states.append(state);return state
def close(state):closed.append(state);return original_close(state)
engine.create=create;engine.close=close
primary=RuntimeError('original checkpoint failure');cleanup=RuntimeError('session cleanup failure')
def broken_close(self):raise cleanup
def callback(*args):
 # Simulated failure of the newly added cleanup, injected at a real callback.
 new.ImmutablePairSession.close=broken_close
 raise primary
results=[]
try:
 for module in (old,new):
  states.clear();closed.clear();new.ImmutablePairSession.close=original_session_close
  ex=module.PairExecutor(c,p,s,callback)
  try:ex(a,a,'a'*64)
  except BaseException as error:
   results.append({'route':module.__name__,'primary_preserved':error is primary,'observed':str(error),'engine_close_calls':len(closed),'state_released':states[0]['annealing'] is None,'poisoned':ex.poisoned})
  else:raise AssertionError('missing callback failure')
  # Dispose synthetic state even where candidate skipped it.
  if states[0]['annealing'] is not None:original_close(states[0])
finally:
 engine.create=original_create;engine.close=original_close;new.ImmutablePairSession.close=original_session_close
assert results[0]['primary_preserved'] and results[0]['engine_close_calls']==1 and results[0]['state_released']
assert not results[1]['primary_preserved'] and results[1]['engine_close_calls']==0 and not results[1]['state_released']
out={'reproduced':True,'synthetic_failure_injection':True,'genuine_authority':False,'results':results,'affinity':sorted(os.sched_getaffinity(0))}
(H/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
