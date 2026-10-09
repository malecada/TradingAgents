import importlib.util,json,os,resource,signal,sys
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]));os.nice(10);signal.alarm(60)
R=Path.cwd();H=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load('withheld_executor',H.parent/'mcm-immutable-pair-executor01-2026-10-09/pair_executor.py');new=load('corrected_executor',H/'pair_executor.py')
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
c=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=3,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal')
p=dict(max_state_bytes=65536,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=65536,max_score_buffer_bytes=65536,chunk_edges=8,max_checkpoint_bytes=262144,max_publications=100,total_checkpoint_bytes=1048576)
s=dict(max_checkpoints=100,calls_per_checkpoint=2,operations_per_call=3,max_total_checkpoints=1000,max_total_checkpoint_bytes=500000000)
a=AttributedGraph(node_ids=('a','b'),node_features=np.array([[0.],[1.]]),edge_index=np.array([[0,1],[1,0]],dtype=np.int64),edge_features=np.array([[.2],[.3]]),parent_hash='a'*64,center_id='a')
cls=new.ImmutablePairSession;session_close=cls.close;engine_close=new.engine.close;checks=[]
for route,case in [(old,'primary'),(new,'primary'),(new,'success_cleanup_failure'),(new,'both_cleanup_fail')]:
 primary=RuntimeError('checkpoint primary');cleanup=RuntimeError('session cleanup');secondary=RuntimeError('engine cleanup');states=[];engine_calls=[];session_calls=[]
 def bad_close(session):
  session_calls.append(1);session_close(session);raise cleanup
 def close_state(state):
  engine_calls.append(state);engine_close(state)
  if case=='both_cleanup_fail':raise secondary
 def callback(*args):
  states.append(args[2]);cls.close=bad_close
  if case in ('primary','both_cleanup_fail'):raise primary
 cls.close=session_close;new.engine.close=close_state
 if case=='success_cleanup_failure':cls.close=bad_close
 ex=route.PairExecutor(c,p,s,callback)
 try:ex(a,a,'a'*64)
 except RuntimeError as error:
  if route is old:
   assert error is cleanup and not engine_calls and states[0]['annealing'] is not None
   engine_close(states[0]);checks.append('actual_withheld_red_reproduced')
  else:
   assert ex.poisoned and len(engine_calls)==1 and engine_calls[0]['annealing'] is None and len(session_calls)==1
   assert error is (cleanup if case=='success_cleanup_failure' else primary)
   if case=='both_cleanup_fail':assert len(primary.__notes__)==2
   checks.append('corrected_cleanup_'+case)
 else:raise AssertionError('missing cleanup failure')
 finally:cls.close=session_close;new.engine.close=engine_close
(H/'RESULT01.json').write_text(json.dumps({'decision':'PASS','checks':checks,'original_numeric_evidence_reused':True,'empirical_execution':False},indent=2)+'\n');print(json.dumps({'decision':'PASS','checks':len(checks)}))
