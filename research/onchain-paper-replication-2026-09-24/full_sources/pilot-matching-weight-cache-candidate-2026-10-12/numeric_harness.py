"""ROOT-EXECUTION ONLY: finite synthetic numerical fixtures, never empirical data.
No Run/Owner/admit/start or network. Importing this file imports NumPy/solver.
"""
from pathlib import Path
import importlib.util,sys,json,hashlib,time,math,resource,tempfile
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT))
import tradingagents.research.onchain_replication
PACKAGE='tradingagents.research.onchain_replication'
def install(name):
 spec=importlib.util.spec_from_file_location(PACKAGE+'.'+name,P/(name+'.py'))
 module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
 setattr(sys.modules[PACKAGE],name,module);spec.loader.exec_module(module);return module
phase=install('phase_timing')
from tradingagents.research.onchain_replication import matching_checkpoint as engine,matching_annealing as ann
policy=install('matching_numeric_policy');session_module=install('matching_immutable_session')
Session=session_module.ImmutablePairSession
from tradingagents.research.onchain_replication.contracts import AttributedGraph
import numpy as np

def config(path,expected):
 raw=Path(path).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('explicit original config hash required')
 c=json.loads(raw)
 for k,v in {'alpha':1.,'beta0':1.,'beta_final':30.,'beta_rate':.075,'max_iterations':50,'normalization_iterations':1,'solver':'algorithm1_literal'}.items():
  if c.get(k)!=v:raise ValueError('original48-temperature scientific config required: '+k)
 beta=c['beta0'];count=0
 while beta<=c['beta_final'] and count<c['max_iterations']:beta*=1+c['beta_rate'];count+=1
 if count!=48:raise ValueError('original48 temperatures required')
 return c

def graph(edges,offset=0.):
 n=max(2,math.ceil(math.sqrt(edges)))
 positions=np.arange(edges,dtype=np.int64)
 index=np.asarray((positions//n,positions%n),dtype=np.int64).reshape(2,edges)
 nodes=(np.arange(n*4,dtype=np.float64).reshape(n,4)%29)*.017+offset
 features=(np.arange(edges*2,dtype=np.float64).reshape(edges,2)%97)*.013+offset
 return AttributedGraph(tuple(str(i) for i in range(n)),nodes,index,features,'a'*64,'0')

def frozen(array,dtype=np.float64):
 array=np.asarray(array,dtype=dtype);return np.frombuffer(array.tobytes(),dtype=dtype).reshape(array.shape)

def solve(a,b,c,version,*,checkpoint=None,budget=1024):
 if type(budget) is not int or budget<=0:raise ValueError('positive original operation budget required')
 selected=dict(policy.CACHE_POLICY if version==2 else policy.POLICY)
 progress=[];counts=[];reloaded=False;totals=phase.PhaseTotals()
 state=session=None;start=time.perf_counter()
 try:
  with phase.activate(totals):
   state=engine.create(a,b,c,max_state_bytes=16*1024**2,hardening_buffer_bytes=4*1024**2)
   session=Session(a,b,c,engine=engine,annealing=ann,numeric_kernel_policy=selected,
       edge_cache_policy=dict(ann.ADAPTIVE_EDGE_POLICY))
   while state['phase']!='done':
    used=session.advance(state,max_operations=budget);inner=state['annealing']
    progress.append((used,state['phase'],inner['phase'],inner['cursor'],inner['iterations']))
    if checkpoint is not None and not reloaded and inner['iterations']>=2:
     pin=engine.save(state,checkpoint,a,b,c,max_checkpoint_bytes=16*1024**2)
     session.close();counts.append(session._numeric_adapter.snapshot());engine.close(state)
     state=engine.load(checkpoint,a,b,c,expected_sha256=pin,max_state_bytes=16*1024**2,hardening_buffer_bytes=4*1024**2)
     session=Session(a,b,c,engine=engine,annealing=ann,numeric_kernel_policy=selected,
         edge_cache_policy=dict(ann.ADAPTIVE_EDGE_POLICY));reloaded=True
   score=engine.score_only(state,a,b,c,max_buffer_bytes=4*1024**2)
   # Diagnostic copies only; no dense all-edge-product score computation.
   assignment=np.zeros(state['annealing']['M'].shape,dtype=np.int8)
   for u,i in state['hardening']['pairs']:assignment[u,i]=1
   result=ann.MatchResult(assignment,score.score,score.convergence,score.iterations,state['annealing']['M'].copy())
   session.close();counts.append(session._numeric_adapter.snapshot());session=None
   engine.close(state);state=None
  elapsed=time.perf_counter()-start
  return result,progress,{'adapter_lifetimes':counts,'phases':totals.snapshot(),'wall_seconds':elapsed,
      'timing_interval':'cold create + session + advances/hardening + production score_only + diagnostic copies + session/state cleanup',
      'operation_budget':budget,'checkpoint_reloaded':reloaded}
 finally:
  primary=sys.exception()
  for closer in ((session.close if session is not None else lambda:None),
                  (lambda:engine.close(state)) if state is not None else lambda:None):
   try:closer()
   except BaseException as error:
    if primary is None:primary=error
    else:
     try:BaseException.add_note(primary,'fixture cleanup failed: '+repr(error))
     except BaseException:pass
  if primary is not None and sys.exception() is None:raise primary

def compare(left,right):
 a,ap,_=left;b,bp,_=right
 if ap!=bp:raise AssertionError('ordered operation/cursor history differs')
 np.testing.assert_allclose(a.soft_assignment,b.soft_assignment,atol=1e-8,rtol=1e-6)
 np.testing.assert_array_equal(a.assignment,b.assignment)
 if not math.isclose(a.score,b.score,abs_tol=1e-8,rel_tol=1e-6):raise AssertionError('C05 score differs')
 if a.iterations!=48 or b.iterations!=48:raise AssertionError('original48-temperature run incomplete')
 return {'steps':len(ap),'used_operations':sum(r[0] for r in ap),'iterations':48,
  'cursor_sha256':hashlib.sha256(json.dumps(ap,separators=(',',':')).encode()).hexdigest(),
  'v1_soft_sha256':hashlib.sha256(a.soft_assignment.tobytes()).hexdigest(),
  'v2_soft_sha256':hashlib.sha256(b.soft_assignment.tobytes()).hexdigest(),
  'assignment_sha256':hashlib.sha256(a.assignment.tobytes()).hexdigest(),'v1_score':a.score,'v2_score':b.score}
