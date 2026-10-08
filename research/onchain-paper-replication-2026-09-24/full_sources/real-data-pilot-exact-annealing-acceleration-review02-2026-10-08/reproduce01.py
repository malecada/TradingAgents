import os,resource,sys,importlib.util,copy,json,math,warnings,hashlib
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(55,55))
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];sys.path.insert(0,str(R));A=P.parent/'real-data-pilot-exact-annealing-acceleration02-2026-10-08'
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph

def load(file,label):
 name='tradingagents.research.onchain_replication.'+label;sp=importlib.util.spec_from_file_location(name,A/file);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
B=load('baseline.py','review_base');C=load('matching_annealing.py','review_candidate')
config=dict(beta0=1.,beta_final=1.,beta_rate=.5,max_iterations=1,alpha=1.,max_pair_entries=100,normalization_iterations=1,solver='algorithm1_literal')
edges=np.array([[0,0,1],[0,1,0]],dtype=np.int64)
a=AttributedGraph(('a','b'),np.array([[0.],[math.sqrt(745.)]],dtype=np.float64),edges,np.zeros((3,1)), 'a'*64,'a')
b=AttributedGraph(('c','d'),np.zeros((2,1)),edges,np.zeros((3,1)), 'b'*64,'c')
seed=B.create(a,b,config,max_state_bytes=1024,max_chunk_entries=8);B.advance(seed,a,b,config,max_operations=5)
assert seed['phase']=='edges' and seed['cursor']==0 and seed['M'][1,0]>0
results={}
def fail(*args):raise RuntimeError('errstate callback')
for mode in ['warning_error','call_error','log_error','raise_fallback']:
 rows=[]
 for label,m in [('baseline',B),('candidate',C)]:
  x=copy.deepcopy(seed);previous=np.geterrcall()
  class Logger:
   def write(self,*args):raise RuntimeError('errstate logger')
  try:
   np.seterrcall(Logger() if mode=='log_error' else fail)
   with warnings.catch_warnings():
    warnings.simplefilter('error',RuntimeWarning)
    with np.errstate(under={'warning_error':'warn','call_error':'call','log_error':'log','raise_fallback':'raise'}[mode]):
     try:m.advance(x,a,b,config,max_operations=9);error=None
     except BaseException as e:error=type(e).__name__+': '+str(e)
  finally:np.seterrcall(previous)
  rows.append({'implementation':label,'error':error,'cursor':x['cursor'],'safe':x['safe'],'Q_bytes':x['Q'].tobytes().hex()})
 results[mode]=rows
 assert rows[0]['error'] is not None and rows[1]['error'] is not None
 assert rows[0]['cursor']==rows[1]['cursor'] and rows[0]['Q_bytes']==rows[1]['Q_bytes']
assert (A/'baseline.py').read_bytes()==(R/'tradingagents/research/onchain_replication/matching_annealing.py').read_bytes()
result={'status':'PASS_FIXED_COUNTEREXAMPLES','source_hashes':{x:hashlib.sha256((A/x).read_bytes()).hexdigest() for x in ['baseline.py','matching_annealing.py']},'numpy':np.__version__,'results':results,'scope':'finite synthetic valid AttributedGraph states reached through actual create/advance; no empirical data'}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
