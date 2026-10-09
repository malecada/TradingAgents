import sys,json,time,hashlib,os,importlib.util,statistics
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];sys.path.insert(0,str(R))
import numpy as np
from tradingagents.research.onchain_replication import matching_annealing as old
from tradingagents.research.onchain_replication.contracts import AttributedGraph
spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication._candidate',D/'matching_annealing.py');new=importlib.util.module_from_spec(spec);spec.loader.exec_module(new)
c=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_bytes())
def graph(n):
 e=np.array([(i,j) for i in range(n) for j in range(n) if i!=j and (i+j)%3],dtype=np.int64).reshape(-1,2).T.copy()
 return AttributedGraph(tuple('n'+str(i) for i in range(n)),np.arange(n*2,dtype=np.float64).reshape(n,2)*.01,e,np.arange(e.shape[1]*2,dtype=np.float64).reshape(-1,2)*.02,'a'*64,'n0')
def equal(a,b):
 assert a.keys()==b.keys()
 for k in a:
  if isinstance(a[k],np.ndarray):assert a[k].dtype==b[k].dtype and a[k].shape==b[k].shape and a[k].tobytes()==b[k].tobytes(),k
  else:assert a[k]==b[k],k
checks=[]
for shape in [(1,1),(2,3),(4,5),(8,7)]:
 a,b=map(graph,shape)
 for chunk in [3,65536]:
  x=old.create(a,b,c,max_state_bytes=1000000,max_chunk_entries=chunk);y=new.create(a,b,c,max_state_bytes=1000000,max_chunk_entries=chunk)
  count=0
  while x['phase']!='done':
   budget=[1,7,127,1000000][count%4]
   assert old.advance(x,a,b,c,max_operations=budget)==new.advance(y,a,b,c,max_operations=budget)
   equal(x,y);count+=1
  assert repr(old.result(x,a,b,c))==repr(new.result(y,a,b,c))
  checks.append({'shape':shape,'chunk':chunk,'boundaries':count})
# Exact wrapper bits including infinities/ties/strides and policy-dependent errors.
for v in [np.array([[0.,-0.],[1.,1.]]),np.array([[np.inf,-np.inf],[np.nan,0.]]),np.array([[745.,-745.],[1.,-1000.]]),np.arange(12.).reshape(3,4)[:,::2]]:
 for axis in (0,1):
  for under in ('ignore','raise'):
   vals=[]
   for f in (old.logsumexp,new._matrix_logsumexp):
    try:
     with np.errstate(under=under): vals.append(('ok',f(v,axis=axis,keepdims=True).tobytes()))
    except Exception as e:vals.append((type(e).__name__,str(e)))
   assert vals[0]==vals[1],vals
# Monkeypatched public wrapper follows original fallback.
original=new.logsumexp
new.logsumexp=lambda *a,**kw:'fallback'
assert new._matrix_logsumexp(np.ones((2,2)),axis=0,keepdims=True)=='fallback';new.logsumexp=original
raw=[]
for shape in [(4,5),(8,7)]:
 a,b=map(graph,shape)
 for mod in (old,new):mod._advance_checked(mod.create(a,b,c,max_state_bytes=1000000),a,b,c,max_operations=1000000)
 for rep in range(12):
  row={'shape':shape,'rep':rep}
  for label,mod in ([('old',old),('new',new)] if rep%2==0 else [('new',new),('old',old)]):
   state=mod.create(a,b,c,max_state_bytes=1000000);t=time.perf_counter();mod._advance_checked(state,a,b,c,max_operations=1000000);row[label]=time.perf_counter()-t
  raw.append(row)
out={'checks':checks,'normalization_edge_checks':32,'fallback':True,'affinity':sorted(os.sched_getaffinity(0)),'numpy':np.__version__,'python':sys.version,'timings':raw,'ratios':{str(s):statistics.median(x['old'] for x in raw if x['shape']==s)/statistics.median(x['new'] for x in raw if x['shape']==s) for s in [(4,5),(8,7)]}}
(D/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['ratios']))
