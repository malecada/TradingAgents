"""Focused synthetic executor integration proof; no Run/Owner/financial claims."""
import hashlib,importlib.util,json,os,resource,signal,struct,sys
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2)
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2)
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]));os.nice(10);signal.alarm(60)
R=Path.cwd();H=Path(__file__).resolve().parent;sys.path.insert(0,str(R));checks=[]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load('old_executor',H.parent/'mcm-batched-execution03-2026-10-09/pair_executor.py');new=load('new_executor',H/'pair_executor.py')
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
c=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=3,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal')
p=dict(max_state_bytes=65536,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=65536,max_score_buffer_bytes=65536,chunk_edges=8,max_checkpoint_bytes=262144,max_publications=100,total_checkpoint_bytes=1048576)
s=dict(max_checkpoints=100,calls_per_checkpoint=2,operations_per_call=3,max_total_checkpoints=1000,max_total_checkpoint_bytes=500000000)
a=AttributedGraph(node_ids=('a','b'),node_features=np.array([[0.],[1.]]),edge_index=np.array([[0,1],[1,0]],dtype=np.int64),edge_features=np.array([[.2],[.3]]),parent_hash='a'*64,center_id='a')
eng=new.engine;ann=new.annealing;advance=eng._advance_owned;close=eng.close;validate=ann.validate_pair;traces=[];closed=[];counts=[];in_step=False
calls={'advance_validations':0,'all_validations':0}
def spy(state,*args,**kw):
 global in_step
 traces.append(('advance',state['phase'],state['annealing']['phase'],state['annealing']['cursor']))
 return advance(state,*args,**kw)
def checked(*args):
 calls['all_validations']+=1
 if in_step:calls['advance_validations']+=1
 return validate(*args)
def closing(state):closed.append(state);return close(state)
eng._advance_owned=spy;eng.close=closing;ann.validate_pair=checked
original_public=eng.advance;original_session=new.ImmutablePairSession.advance
# Count validation spanning each chosen route, keeping the numeric body unchanged.
def public_step(*args,**kw):
 global in_step
 in_step=True
 try:return original_public(*args,**kw)
 finally:in_step=False
def session_step(self,*args,**kw):
 global in_step
 in_step=True
 try:return original_session(self,*args,**kw)
 finally:in_step=False
eng.advance=public_step;new.ImmutablePairSession.advance=session_step
answers=[];runs=[]
def checkpoint(key,ordinal,state,*args):
 traces.append(('checkpoint',ordinal,state['phase'],state['annealing']['cursor']))
 assert key=='a'*64
for route in (old,new):
 traces.clear();closed.clear();calls.update(advance_validations=0,all_validations=0)
 ex=route.PairExecutor(c,p,s,checkpoint);answers.append(ex(a,a,'a'*64));runs.append({'trace':list(traces),'validations':dict(calls),'checkpoints':ex.checkpoints,'reserved_bytes':ex.reserved_bytes})
 assert len(closed)==1 and closed[0]['annealing'] is None
 checks.append('success_cleanup_'+route.__name__)
assert struct.pack('>d',answers[0][0])==struct.pack('>d',answers[1][0]) and answers[0][1:]==answers[1][1:];checks.append('score_iteration_convergence_identical')
assert runs[0]['trace']==runs[1]['trace'] and runs[0]['checkpoints']==runs[1]['checkpoints'] and runs[0]['reserved_bytes']==runs[1]['reserved_bytes'];checks.append('advance_checkpoint_order_and_charges_identical')
assert runs[0]['validations']['advance_validations']>0 and runs[1]['validations']['advance_validations']==0;checks.append('repeated_graph_validation_removed_from_advances')
for case in ['callback','exhaustion','cumulative','config_mutation']:
 closed.clear();primary=RuntimeError('checkpoint primary');schedule={**s,'max_checkpoints':1,'calls_per_checkpoint':1}
 def cb(*args):
  if case=='callback':raise primary
  if case=='config_mutation':args[5]['alpha']=.8
 if case=='config_mutation':schedule={**s,'calls_per_checkpoint':1}
 if case=='cumulative':schedule['max_total_checkpoint_bytes']=1
 ex=new.PairExecutor(c,p,schedule,cb)
 try:ex(a,a,'b'*64)
 except (RuntimeError,ValueError) as error:
  if case=='callback':assert error is primary
 else:raise AssertionError('missing refusal '+case)
 assert ex.poisoned and (not closed if case=='cumulative' else len(closed)==1 and closed[0]['annealing'] is None)
 checks.append('poison_cleanup_'+case)
 try:ex(a,a,'c'*64)
 except ValueError:checks.append('closed_executor_refuses_'+case)
 else:raise AssertionError('poison ignored')
eng._advance_owned=advance;eng.close=close;ann.validate_pair=validate;eng.advance=original_public;new.ImmutablePairSession.advance=original_session
out={'decision':'PASS','checks':checks,'runs':runs,'answers':answers,'real_data':False,'benchmark':False,'genuine_authority':False}
(H/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'decision':'PASS','checks':len(checks),'validation_counts':[r['validations'] for r in runs]}))
