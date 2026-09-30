import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from tradingagents.research.onchain_replication.matching_reference import harden
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ranked',HERE/'ranked.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Tests(unittest.TestCase):
 def test_exact_reference_ties_cast_rectangles_and_views(self):
  rng=np.random.default_rng(14)
  cases=[np.zeros((4,3)),np.array([[0.,-0.,-1.],[-0.,0.,2.]]),np.array([[2**60,2**60+1],[1,2]],dtype=np.int64),np.arange(20.).reshape(5,4)[:,::-1],np.empty((0,3)),np.empty((3,0))]
  cases += [rng.integers(-3,4,size=(n,k)) for n in range(1,12) for k in range(1,9)]
  cases += [rng.normal(size=(17,11)),rng.normal(size=(11,17))]
  for x in cases:
   before=x.copy();pairs=m.harden_pairs(x,max_pair_entries=4_000_000,max_explicit_bytes=1_000_000)
   out=np.zeros(x.shape,dtype=np.int8)
   for u,i in pairs:out[u,i]=1
   np.testing.assert_array_equal(out,harden(x));np.testing.assert_array_equal(x,before)
   self.assertEqual(len(pairs),min(x.shape))
 def test_pair_order_and_tie_order(self):
  x=np.array([[8.,9.,7.],[9.,2.,1.]])
  self.assertEqual(m.harden_pairs(x,max_pair_entries=6,max_explicit_bytes=10000).tolist(),[[0,1],[1,0]])
  self.assertEqual(m.harden_pairs(np.ones((3,4)),max_pair_entries=12,max_explicit_bytes=10000).tolist(),[[0,0],[1,1],[2,2]])
 def test_limits_before_sort_and_domain_refusal(self):
  with patch.object(m.np,'argsort',side_effect=AssertionError('sort reached')):
   for kw in ({'max_pair_entries':5,'max_explicit_bytes':10000},{'max_pair_entries':6,'max_explicit_bytes':1}):
    with self.assertRaises(ValueError):m.harden_pairs(np.ones((3,2)),**kw)
   for x in (np.array([[np.nan]]),np.array([[np.inf]]),np.array([1.]),np.array([[1+2j]]),np.array([['a']])):
    with self.assertRaises(ValueError):m.harden_pairs(x,max_pair_entries=100,max_explicit_bytes=10000)
 def test_explicit_accounting_exact_boundary(self):
  # key float64, index permutation intp, finite bool, used axes bool, pairs int64.
  n,k=3,5;need=17*n*k+n+k+16*min(n,k)
  self.assertEqual(m.explicit_bytes(n,k),need)
  with self.assertRaises(ValueError):m.harden_pairs(np.zeros((n,k)),max_pair_entries=15,max_explicit_bytes=need-1)
  self.assertEqual(len(m.harden_pairs(np.zeros((n,k)),max_pair_entries=15,max_explicit_bytes=need)),3)
if __name__=='__main__':unittest.main(verbosity=2)
