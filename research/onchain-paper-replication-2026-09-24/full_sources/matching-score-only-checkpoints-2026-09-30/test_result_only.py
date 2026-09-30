import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from tests.research.onchain_replication.test_matching_reference import graph,config
from tradingagents.research.onchain_replication.matching_reference import match_reference
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('result_only',HERE/'result_only.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Tests(unittest.TestCase):
 def api(self):
  self.assertTrue(callable(getattr(m,'score_only',None)),'score_only adapter is not implemented')
 def finish(self,a,b,c):
  s=m.combined.create(a,b,c,max_state_bytes=1024**2,normalization_chunk_entries=32,hardening_chunk_entries=3,hardening_buffer_bytes=10000)
  while s['phase']!='done':m.combined.advance(s,a,b,c,max_operations=10)
  return s
 def test_reference_results_without_dense_result_path(self):
  self.api()
  pairs=[(graph([[0.],[.4]],[(0,1,.2),(1,0,.7)]),graph([[.1],[.7],[.9]],[(0,1,.5),(1,0,.8),(1,1,.2)])),
         (graph([[0.],[0.]],[]),graph([[0.],[0.],[0.]],[])),
         (graph([[0.],[1.],[2.]],[]),graph([[.5]],[]))]
  for a,b in pairs:
   c=config()|{'max_iterations':2};expected=match_reference(a,b,c);s=self.finish(a,b,c)
   before=s['annealing']['M'].tobytes()
   with patch.object(m.combined,'result',side_effect=AssertionError('dense result path')),        patch.object(m.combined.ann,'score_assignment',side_effect=AssertionError('dense scoring path')),        patch.object(m.np,'zeros',side_effect=AssertionError('dense assignment allocation')):
    result=m.score_only(s,a,b,c,max_buffer_bytes=10000,chunk_edges=2)
   self.assertEqual((result.score,result.iterations,result.convergence),(expected.score,expected.iterations,expected.convergence))
   self.assertFalse(hasattr(result,'assignment'));self.assertFalse(hasattr(result,'soft_assignment'))
   self.assertEqual(s['annealing']['M'].tobytes(),before);self.assertFalse(s['annealing']['M'].flags.writeable)
 def test_incomplete_and_insufficient_budget_reject_before_pair_allocation(self):
  self.api();a=graph([[0.],[1.]],[]);c=config()|{'max_iterations':1}
  s=m.combined.create(a,a,c,max_state_bytes=1024**2)
  with self.assertRaisesRegex(ValueError,'incomplete'):m.score_only(s,a,a,c,max_buffer_bytes=10000)
  s=self.finish(a,a,c)
  with patch.object(m.np,'asarray',side_effect=AssertionError('pairs allocated before budget')):
   with self.assertRaisesRegex(ValueError,'allowance'):m.score_only(s,a,a,c,max_buffer_bytes=1)
 def test_domain_and_capacity_are_not_silently_relaxed(self):
  self.api();a=graph([[0.],[1.]],[]);c=config()|{'max_iterations':1};s=self.finish(a,a,c)
  with self.assertRaisesRegex(ValueError,'capacity'):m.score_only(s,a,a,c|{'max_pair_entries':1},max_buffer_bytes=10000)
  # The adapter must propagate the accepted sparse component domain refusal.
  with patch.object(m.sparse,'score_indices',side_effect=ValueError('agreement arithmetic domain exceeds representable envelope')):
   with self.assertRaisesRegex(ValueError,'agreement arithmetic domain'):m.score_only(s,a,a,c,max_buffer_bytes=10000)
  self.assertTrue(s['safe']);self.assertEqual(s['phase'],'done')
if __name__=='__main__':unittest.main(verbosity=2)
