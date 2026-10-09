import importlib.util,json,sys,hashlib,copy
from pathlib import Path
import numpy as np
from tradingagents.research.onchain_replication import matching_checkpoint as original
from tradingagents.research.onchain_replication.contracts import AttributedGraph
P=Path(__file__).resolve().parent
PACKAGE='tradingagents.research.onchain_replication.'
def load(name,file):
 spec=importlib.util.spec_from_file_location(PACKAGE+name,P/file);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
ann=load('_immutable_session_ann','matching_annealing.py');engine=load('_immutable_session_engine','matching_checkpoint.py');engine.ann=ann
session=load('_immutable_session_adapter','immutable_pair.py')
public=Path('research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-final23-2026-10-09/inputs02/execution_job.json')
config=json.loads(public.read_text())['payload']['representation_jobs']['original32']['descriptor']['configs']['matching']
a=AttributedGraph('a'*64,'a0',('a0','a1','a2'),np.array([[.1,.5],[.2,.7],[.3,.9]]),np.array([[0,1,2],[1,2,0]],dtype=np.int64),np.array([[.2],[.5],[.8]]))
b=AttributedGraph('b'*64,'b0',('b0','b1'),np.array([[.4,.6],[.2,.8]]),np.array([[0,1],[1,0]],dtype=np.int64),np.array([[.3],[.7]]))
policy={'max_state_bytes':1048576,'normalization_chunk_entries':8,'hardening_chunk_entries':8,'hardening_buffer_bytes':1048576}
checks=[];traces=[]
def agree(x,y):
 assert x['phase']==y['phase'] and x['safe']==y['safe'] and x['policy']==y['policy'] and x['matrix_sha256']==y['matrix_sha256']
 for k in ('phase','cursor','iterations','beta','shape','safe','identity','max_chunk_entries'):assert x['annealing'][k]==y['annealing'][k]
 for k in ('V','M','Q'):assert np.array_equal(x['annealing'][k],y['annealing'][k]) and x['annealing'][k].tobytes()==y['annealing'][k].tobytes()
 if x['hardening'] is not None:
  for k in x['hardening']:
   if isinstance(x['hardening'][k],np.ndarray):assert np.array_equal(x['hardening'][k],y['hardening'][k])
   else:assert x['hardening'][k]==y['hardening'][k],k
for budget in (11,4096):
 c=copy.deepcopy(config);left=original.create(a,b,c,**policy);right=engine.create(a,b,c,**policy);s=session.ImmutablePairSession(a,b,c,engine=engine,annealing=ann);calls=0
 try:
  while left['phase']!='done':
   assert original.advance(left,a,b,c,max_operations=budget)==s.advance(right,max_operations=budget);agree(left,right);calls+=1;assert calls<5000
  assert original.score_only(left,a,b,c,max_buffer_bytes=1048576)==engine.score_only(right,a,b,c,max_buffer_bytes=1048576)
  traces.append({'budget':budget,'advances':calls,'iterations':left['annealing']['iterations'],'all_state_bits_equal':True})
 finally:original.close(left);engine.close(right);s.close()
checks.append('two_original48iteration_state_and_operation_traces_bitwise_equal')
# Initial validation followed by zero repeated graph-validator calls in session.
c=copy.deepcopy(config);count=[0];validator=ann.validate_pair
def tracked(*args):count[0]+=1;return validator(*args)
ann.validate_pair=tracked
s=session.ImmutablePairSession(a,b,c,engine=engine,annealing=ann);state=engine.create(a,b,c,**policy);before=count[0];s.advance(state,max_operations=11);assert count[0]==before
engine.close(state);s.close();ann.validate_pair=validator;checks.append('no_repeated_graph_validation_with_state_checks_retained')
for mode in ('array_shape','array_replace','identity','config_type','state_nonfinite','function_code','closed'):
 c=copy.deepcopy(config);aa=AttributedGraph(a.parent_hash,a.center_id,a.node_ids,a.node_features,a.edge_index,a.edge_features);s=session.ImmutablePairSession(aa,b,c,engine=engine,annealing=ann);state=engine.create(aa,b,c,**policy);restore=None
 try:
  if mode=='array_shape':aa.node_features.shape=(1,6)
  elif mode=='array_replace':object.__setattr__(aa,'node_features',np.array(aa.node_features))
  elif mode=='identity':object.__setattr__(aa,'center_id','a1')
  elif mode=='config_type':c['alpha']=True
  elif mode=='state_nonfinite':state['annealing']['M'][0,0]=float('nan')
  elif mode=='function_code':restore=engine._advance_owned;engine._advance_owned=lambda *a,**k:None
  elif mode=='closed':s.close()
  try:s.advance(state,max_operations=11)
  except ValueError:checks.append('refused_'+mode)
  else:raise AssertionError('mutation accepted '+mode)
 finally:
  if restore is not None:engine._advance_owned=restore
  engine.close(state);s.close()
# Writable inputs cannot enter the shortcut, and public route still validates.
aa=AttributedGraph(a.parent_hash,a.center_id,a.node_ids,a.node_features,a.edge_index,a.edge_features);object.__setattr__(aa,'node_features',np.array(aa.node_features))
try:session.ImmutablePairSession(aa,b,config,engine=engine,annealing=ann)
except ValueError:checks.append('writable_inputs_refused')
else:raise AssertionError('writable accepted')
x={'status':'PASS','checks':checks,'traces':traces,'scope':'tiny synthetic source check only; no empirical arrays, benchmark, source installation or authority'}
(P/'RESULT01.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
