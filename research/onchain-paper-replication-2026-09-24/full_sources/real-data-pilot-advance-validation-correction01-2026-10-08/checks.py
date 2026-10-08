"""Synthetic changed-seam checks; no empirical inputs or authority claims."""
import copy, hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from tests.research.onchain_replication.test_matching_reference import graph, config
ROOT=Path(__file__).resolve().parent
PREFIX='tradingagents.research.onchain_replication.'
def module(name,file):
 s=importlib.util.spec_from_file_location(PREFIX+name,ROOT/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
oldann=module('_baseline_ann','original_matching_annealing.py');ann=module('_candidate_ann','matching_annealing.py')
old=module('_baseline_composite','original_matching_checkpoint.py');old.ann=oldann
new=module('_candidate_composite','matching_checkpoint.py');new.ann=ann
OPTIONS=dict(max_state_bytes=1048576,normalization_chunk_entries=16,hardening_chunk_entries=2,hardening_buffer_bytes=10000)
def fixture(n=3,m=2,edges=True):
 def g(k):return graph([[i*.17] for i in range(k)],[(i,i+1,.2+i*.1) for i in range(k-1)] if edges else [])
 return g(n),g(m),config()|{'max_iterations':3}
def equal(a,b):
 if isinstance(a,np.ndarray):
  assert isinstance(b,np.ndarray) and a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes() and a.flags.writeable==b.flags.writeable
 elif isinstance(a,dict):
  assert a.keys()==b.keys()
  for k in a:equal(a[k],b[k])
 else:assert a==b,(a,b)
def clone(s):
 t=copy.deepcopy(s)
 if s['hardening'] is not None:
  t['hardening']['order'].flags.writeable=False;t['annealing']['M'].flags.writeable=False
 return t
class Checks(unittest.TestCase):
 def test_trajectory_and_serialization(self):
  count=0
  for n,m,edges in ((3,2,True),(2,3,True),(1,3,False),(3,1,False),(2,2,False)):
   for budget in (1,3,100):
    a,b,c=fixture(n,m,edges);x=old.create(a,b,c,**OPTIONS);y=new.create(a,b,c,**OPTIONS);phases=set()
    for step in range(1000):
     equal(x,y);phases.add(x['phase']);count+=1
     self.assertEqual(old.advance(x,a,b,c,max_operations=budget),new.advance(y,a,b,c,max_operations=budget));equal(x,y)
     if x['phase']=='done':break
    else:self.fail('trajectory did not finish')
    self.assertIn('hardening',phases)
    ro=old.result(x,a,b,c);rn=new.result(y,a,b,c)
    self.assertEqual(ro.score.hex(),rn.score.hex());equal(ro.assignment,rn.assignment);equal(ro.soft_assignment,rn.soft_assignment)
    self.assertEqual(old.score_only(x,a,b,c,max_buffer_bytes=10000),new.score_only(y,a,b,c,max_buffer_bytes=10000))
    with tempfile.TemporaryDirectory() as d:
     p=Path(d);oh=old.save(x,p/'old',a,b,c,max_checkpoint_bytes=1048576);nh=new.save(y,p/'new',a,b,c,max_checkpoint_bytes=1048576)
     self.assertEqual(oh,nh)
     for f in (p/'old').rglob('*'):
      if f.is_file():self.assertEqual(f.read_bytes(),(p/'new'/f.relative_to(p/'old')).read_bytes())
     z=new.load(p/'new',a,b,c,expected_sha256=nh,**OPTIONS);equal(y,z);new.close(z)
    old.close(x);new.close(y)
  print('trajectory_state_comparisons',count)
 def test_invalid_state_and_budget_order(self):
  a,b,c=fixture();base=old.create(a,b,c,**OPTIONS)
  def identity(s):s['annealing']['identity']['left']='0'*64
  def nonfinite(s):s['annealing']['M'][0,0]=np.nan
  def cursor(s):s['annealing']['cursor']=-1
  def poison(s):s['safe']=False
  for mutate in (identity,nonfinite,cursor,poison,lambda s:None):
   for budget in (0,-1,True,1.5,1):
    outputs=[]
    for engine in (old,new):
     s=clone(base);mutate(s)
     try:result=engine.advance(s,a,b,c,max_operations=budget);outputs.append(('ok',result,s['safe']))
     except Exception as e:outputs.append((type(e).__name__,str(e),s['safe'],s['annealing']['safe']))
    self.assertEqual(*outputs)
 def test_public_boundary_and_duplicate_spy(self):
  a,b,c=fixture()
  for engine,inner,want in ((old,oldann,2),(new,ann,1)):
   s=engine.create(a,b,c,**OPTIONS)
   with patch.object(inner,'check',wraps=inner.check) as spy:engine.advance(s,a,b,c,max_operations=1);self.assertEqual(spy.call_count,want)
  for inner in (oldann,ann):
   s=inner.create(a,b,c,max_state_bytes=1048576)
   with patch.object(inner,'check',wraps=inner.check) as spy:inner.advance(s,a,b,c,max_operations=1);self.assertEqual(spy.call_count,1)
   s['identity']['left']='0'*64
   with self.assertRaisesRegex(ValueError,'positive operation budget'):inner.advance(s,a,b,c,max_operations=0)
   with self.assertRaisesRegex(ValueError,'identity differs'):inner.advance(s,a,b,c,max_operations=1)
 def test_atomic_error_poisoning(self):
  a,b,c=fixture()
  outcomes=[]
  for engine,inner in ((old,oldann),(new,ann)):
   s=engine.create(a,b,c,**OPTIONS)
   with patch.object(inner,'agreement',side_effect=RuntimeError('injected arithmetic failure')):
    with self.assertRaisesRegex(RuntimeError,'injected arithmetic failure'):engine.advance(s,a,b,c,max_operations=1)
   outcomes.append((s['safe'],s['annealing']['safe'],s['annealing']['cursor']))
  self.assertEqual(outcomes,[(False,False,0)]*2)
if __name__=='__main__':unittest.main(verbosity=2)
