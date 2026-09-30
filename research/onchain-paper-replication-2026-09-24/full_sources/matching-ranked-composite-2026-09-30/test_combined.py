import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from tests.research.onchain_replication.test_matching_reference import graph,config
from tradingagents.research.onchain_replication.matching_reference import match_reference
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('combined_ranked',HERE/'combined.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
POLICY=dict(max_state_bytes=1024**2,normalization_chunk_entries=6,hardening_chunk_entries=2,hardening_buffer_bytes=10000)
class Tests(unittest.TestCase):
 def fixture(self):return graph([[0.],[.3],[1.]],[(0,1,.2),(2,1,.1)]),graph([[0.],[.1],[.4],[1.],[2.]],[(0,1,.3),(3,4,.1)])
 def finish(self,s,a,b,c):
  for _ in range(1000):
   if s['phase']=='done':return m.result(s,a,b,c)
   m.advance(s,a,b,c,max_operations=2)
  self.fail('did not finish')
 def test_reference_parity_every_restore_and_explicit_close(self):
  phases=set()
  for a,b in [self.fixture(),(graph([[0.],[0.]],[]),graph([[0.],[0.],[0.]],[])),(graph([[0.],[1.],[2.]],[]),graph([[.5]],[]))]:
   c=config()|{'max_iterations':2};expected=match_reference(a,b,c);s=m.create(a,b,c,**POLICY)
   try:
    with tempfile.TemporaryDirectory() as tmp:
     for step in range(1000):
      if s['phase']=='done':break
      m.advance(s,a,b,c,max_operations=1);phases.add(s['phase'])
      path=Path(tmp)/str(step);h=m.save(s,path,a,b,c,max_checkpoint_bytes=1024**2)
      mapping=getattr(s['hardening']['order'],'_mmap',None) if s['hardening'] else None
      m.close(s)
      if mapping is not None:self.assertTrue(mapping.closed)
      s=m.load(path,a,b,c,expected_sha256=h,**POLICY)
     else:self.fail('did not finish')
     actual=m.result(s,a,b,c)
     self.assertEqual(actual.soft_assignment.tobytes(),expected.soft_assignment.tobytes());np.testing.assert_array_equal(actual.assignment,expected.assignment)
     self.assertEqual((actual.score,actual.convergence,actual.iterations),(expected.score,expected.convergence,expected.iterations))
     with patch.object(m,'result',side_effect=AssertionError('dense result')),patch.object(m.ann,'score_assignment',side_effect=AssertionError('dense score')):
      score=m.score_only(s,a,b,c,max_buffer_bytes=10000,chunk_edges=2)
     self.assertEqual((score.score,score.convergence,score.iterations),(expected.score,expected.convergence,expected.iterations))
   finally:m.close(s)
  self.assertEqual(phases,{'annealing','hardening','done'})
 def test_total_state_and_scratch_admitted_before_allocation(self):
  a,b=self.fixture();c=config();entries=len(a.node_ids)*len(b.node_ids)
  with patch.object(m.ann,'create',side_effect=AssertionError('allocated before policy')):
   for limits in ({'max_state_bytes':32*entries-1},{'hardening_buffer_bytes':1}):
    with self.assertRaises(ValueError):m.create(a,b,c,**(POLICY|limits))
  s=m.create(a,b,c,**POLICY)
  try:
   with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'s'
    with self.assertRaises(ValueError):m.save(s,path,a,b,c,max_checkpoint_bytes=1)
    self.assertFalse(path.exists())
  finally:m.close(s)
 def test_interrupted_ranked_scan_poison_and_prior_recovery(self):
  a,b=self.fixture();c=config()|{'max_iterations':1};s=m.create(a,b,c,**POLICY)
  while s['phase']!='hardening':m.advance(s,a,b,c,max_operations=1)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'prior';h=m.save(s,p,a,b,c,max_checkpoint_bytes=1024**2)
   with patch.object(m.hard,'_accept',side_effect=KeyboardInterrupt):
    with self.assertRaises(KeyboardInterrupt):m.advance(s,a,b,c,max_operations=1)
   self.assertFalse(s['safe']);m.close(s)
   s=m.load(p,a,b,c,expected_sha256=h,**POLICY)
   try:np.testing.assert_array_equal(self.finish(s,a,b,c).assignment,match_reference(a,b,c).assignment)
   finally:m.close(s)
 def test_failure_after_rank_restore_closes_actual_mapping(self):
  a,b=self.fixture();c=config()|{'max_iterations':1};s=m.create(a,b,c,**POLICY)
  while s['phase']!='hardening':m.advance(s,a,b,c,max_operations=1)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'s';h=m.save(s,p,a,b,c,max_checkpoint_bytes=1024**2);m.close(s)
   opened=[];real=m.hard.load
   def capture(*args,**kwargs):
    state=real(*args,**kwargs);opened.append(state['order']._mmap);return state
   error=KeyboardInterrupt()
   with patch.object(m.hard,'load',side_effect=capture),patch.object(m.ann,'load',side_effect=error):
    with self.assertRaises(KeyboardInterrupt) as caught:m.load(p,a,b,c,expected_sha256=h,**POLICY)
    self.assertIs(caught.exception,error);self.assertTrue(opened[-1].closed)
 def test_wrong_policy_and_order_tamper_refused(self):
  a,b=self.fixture();c=config()|{'max_iterations':1};s=m.create(a,b,c,**POLICY)
  while s['phase']!='hardening':m.advance(s,a,b,c,max_operations=1)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'s';h=m.save(s,p,a,b,c,max_checkpoint_bytes=1024**2);m.close(s)
   with patch.object(m.ann,'load',side_effect=AssertionError('annealing opened before refusal')):
    with self.assertRaises(ValueError):m.load(p,a,b,c,expected_sha256=h,**(POLICY|{'hardening_chunk_entries':3}))
    q=p/'hardening/order.npy';q.write_bytes(q.read_bytes()+b'x')
    with self.assertRaises(ValueError):m.load(p,a,b,c,expected_sha256=h,**POLICY)
 def test_restored_matrix_identity_checked_with_rank_mapping_cleanup(self):
  a,b=self.fixture();c=config()|{'max_iterations':1};s=m.create(a,b,c,**POLICY)
  while s['phase']!='hardening':m.advance(s,a,b,c,max_operations=1)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'s';m.save(s,p,a,b,c,max_checkpoint_bytes=1024**2);m.close(s)
   matrix=p/'annealing/M.npy';x=np.load(matrix,allow_pickle=False);x[0,0]+=.125
   with matrix.open('wb') as f:np.save(f,x,allow_pickle=False)
   inner=p/'annealing/manifest.json';d=json.loads(inner.read_bytes());d['files']['M']={'sha256':m.ann.sha(matrix),'bytes':matrix.stat().st_size};inner.write_bytes(m.ann.body(d))
   outer=p/'manifest.json';d=json.loads(outer.read_bytes());d['annealing_sha256']=m.ann.sha(inner);outer.write_bytes(m.ann.body(d))
   maps=[];real=m.hard.load
   def capture(*args,**kwargs):
    state=real(*args,**kwargs);maps.append(state['order']._mmap);return state
   with patch.object(m.hard,'load',side_effect=capture):
    with self.assertRaisesRegex(ValueError,'restored ranked matrix identity differs'):m.load(p,a,b,c,expected_sha256=m.ann.sha(outer),**POLICY)
   self.assertTrue(maps[-1].closed)
 def test_atomic_sort_interruption_recovers_preceding_checkpoint(self):
  a,b=self.fixture();c=config()|{'max_iterations':1};s=m.create(a,b,c,**POLICY)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'prior';h=m.save(s,p,a,b,c,max_checkpoint_bytes=1024**2)
   with patch.object(m.hard,'create',side_effect=KeyboardInterrupt):
    with self.assertRaises(KeyboardInterrupt):
     while s['phase']=='annealing':m.advance(s,a,b,c,max_operations=100)
   self.assertFalse(s['safe']);m.close(s);s=m.load(p,a,b,c,expected_sha256=h,**POLICY)
   try:np.testing.assert_array_equal(self.finish(s,a,b,c).assignment,match_reference(a,b,c).assignment)
   finally:m.close(s)
 def test_score_only_limits_incomplete_and_domain_refusal(self):
  a,b=self.fixture();c=config()|{'max_iterations':1};s=m.create(a,b,c,**POLICY)
  try:
   with self.assertRaisesRegex(ValueError,'incomplete'):m.score_only(s,a,b,c,max_buffer_bytes=10000)
   self.finish(s,a,b,c)
   with patch.object(m.np,'asarray',side_effect=AssertionError('pairs before capacity')):
    with self.assertRaisesRegex(ValueError,'allowance'):m.score_only(s,a,b,c,max_buffer_bytes=1)
   with patch.object(m.sparse,'score_indices',side_effect=ValueError('agreement domain refused')):
    with self.assertRaisesRegex(ValueError,'agreement domain'):m.score_only(s,a,b,c,max_buffer_bytes=10000)
  finally:m.close(s)
if __name__=='__main__':unittest.main(verbosity=2)
