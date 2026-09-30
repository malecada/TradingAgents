import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from tests.research.onchain_replication.test_matching_reference import graph,config
from tradingagents.research.onchain_replication.matching_reference import match_reference
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('combined',HERE/'combined.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
POLICY=dict(max_state_bytes=1024**2,normalization_chunk_entries=6,hardening_chunk_entries=2,hardening_buffer_bytes=10000)
class Tests(unittest.TestCase):
 def fixture(self):
  return graph([[0.],[.3],[1.]],[(0,1,.2),(2,1,.1)]),graph([[0.],[.1],[.4],[1.],[2.]],[(0,1,.3),(3,4,.1)])
 def finish(self,s,a,b,c):
  for _ in range(1000):
   if s['phase']=='done':return m.result(s,a,b,c)
   m.advance(s,a,b,c,max_operations=1)
  self.fail('matching did not finish')
 def test_complete_scalar_parity_with_restore_after_every_return(self):
  pairs=[self.fixture(),(graph([[0.],[0.]],[]),graph([[0.],[0.],[0.]],[])),(graph([[0.],[1.],[2.]],[]),graph([[.5]],[]))]
  phases=set()
  for a,b in pairs:
   c=config()|{'max_iterations':2};want=match_reference(a,b,c);s=m.create(a,b,c,**POLICY)
   with tempfile.TemporaryDirectory() as tmp:
    count=0
    while s['phase']!='done':
     m.advance(s,a,b,c,max_operations=1);count+=1;phases.add(s['phase'])
     if s['phase']=='hardening':
      self.assertFalse(s['annealing']['M'].flags.writeable)
      self.assertEqual(s['matrix_sha256'],hashlib.sha256(memoryview(s['annealing']['M']).cast('B')).hexdigest())
     path=Path(tmp)/str(count);digest=m.save(s,path,a,b,c,max_checkpoint_bytes=1024**2)
     s=m.load(path,a,b,c,expected_sha256=digest,**POLICY)
     self.assertLess(count,1000)
   with patch.object(m.ann,'harden',side_effect=AssertionError('atomic hardener used')):
    got=m.result(s,a,b,c)
   self.assertEqual(got.soft_assignment.tobytes(),want.soft_assignment.tobytes())
   np.testing.assert_array_equal(got.assignment,want.assignment)
   self.assertEqual((got.score,got.iterations,got.convergence),(want.score,want.iterations,want.convergence))
  self.assertEqual(phases,{'annealing','hardening','done'})
 def test_wrong_policy_and_tampered_hardening_rejected_before_arrays(self):
  a,b=self.fixture();c=config()|{'max_iterations':1};s=m.create(a,b,c,**POLICY)
  while s['phase']!='hardening':m.advance(s,a,b,c,max_operations=1)
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'checkpoint';digest=m.save(s,path,a,b,c,max_checkpoint_bytes=1024**2)
   with patch.object(m.ann.np,'load',side_effect=AssertionError('arrays opened before binding')):
    with self.assertRaises(ValueError):m.load(path,a,b,c,expected_sha256=digest,**(POLICY|{'hardening_chunk_entries':3}))
    p=path/'hardening.json';p.write_bytes(p.read_bytes()+b' ')
    with self.assertRaises(ValueError):m.load(path,a,b,c,expected_sha256=digest,**POLICY)
 def test_poisoned_hardening_retains_prior_valid_checkpoint(self):
  a,b=self.fixture();c=config()|{'max_iterations':1};s=m.create(a,b,c,**POLICY)
  while s['phase']!='hardening' or s['hardening']['phase']!='scan':m.advance(s,a,b,c,max_operations=1)
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'prior';digest=m.save(s,path,a,b,c,max_checkpoint_bytes=1024**2)
   with patch.object(m.hard.np,'argmax',side_effect=KeyboardInterrupt):
    with self.assertRaises(KeyboardInterrupt):m.advance(s,a,b,c,max_operations=1)
   self.assertFalse(s['safe'])
   with self.assertRaises(ValueError):m.save(s,Path(tmp)/'invalid',a,b,c,max_checkpoint_bytes=1024**2)
   got=self.finish(m.load(path,a,b,c,expected_sha256=digest,**POLICY),a,b,c)
   np.testing.assert_array_equal(got.assignment,match_reference(a,b,c).assignment)
 def test_restored_matrix_must_match_hardening_body_identity(self):
  import json
  a,b=self.fixture();c=config()|{'max_iterations':1};s=m.create(a,b,c,**POLICY)
  while s['phase']!='hardening':m.advance(s,a,b,c,max_operations=1)
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'checkpoint';m.save(s,path,a,b,c,max_checkpoint_bytes=1024**2)
   matrix_path=path/'annealing/M.npy';changed=np.load(matrix_path,allow_pickle=False);changed[0,0]+=.125
   with matrix_path.open('wb') as f:np.save(f,changed,allow_pickle=False)
   inner_path=path/'annealing/manifest.json';inner=json.loads(inner_path.read_bytes())
   inner['files']['M']={'sha256':m.ann.sha(matrix_path),'bytes':matrix_path.stat().st_size}
   inner_path.write_bytes(m.ann.body(inner))
   outer_path=path/'manifest.json';outer=json.loads(outer_path.read_bytes())
   outer['annealing_sha256']=m.ann.sha(inner_path);outer_path.write_bytes(m.ann.body(outer))
   with self.assertRaisesRegex(ValueError,'restored hardening matrix identity differs'):
    m.load(path,a,b,c,expected_sha256=m.ann.sha(outer_path),**POLICY)
 def test_capacity_and_exclusive_publication(self):
  a,b=self.fixture();c=config()
  with patch.object(m.ann.np,'zeros',side_effect=AssertionError('allocated before policy')):
   with self.assertRaises(ValueError):m.create(a,b,c,**(POLICY|{'hardening_buffer_bytes':1}))
  with self.assertRaises(ValueError):m.create(a,b,c|{'max_pair_entries':1},**POLICY)
  s=m.create(a,b,c,**POLICY)
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'checkpoint'
   with self.assertRaises(ValueError):m.save(s,path,a,b,c,max_checkpoint_bytes=1)
   self.assertFalse(path.exists())
   m.save(s,path,a,b,c,max_checkpoint_bytes=1024**2)
   with self.assertRaises(FileExistsError):m.save(s,path,a,b,c,max_checkpoint_bytes=1024**2)
if __name__=='__main__':unittest.main(verbosity=2)
