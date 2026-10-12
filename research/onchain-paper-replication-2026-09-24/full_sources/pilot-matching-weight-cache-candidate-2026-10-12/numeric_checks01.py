"""ROOT-EXECUTION ONLY. Focused synthetic cache controls; unexecuted by author."""
import argparse,tempfile,json,unittest,sys
from pathlib import Path
from unittest.mock import patch
from numeric_harness import *
CONFIG=None
class NumericChecks(unittest.TestCase):
 def arrays(self):
  a=frozen(np.arange(260,dtype=np.float64).reshape(130,2)*.01);b=frozen(a+.03)
  pos=np.arange(1024,dtype=np.int64);return a,b,pos//130,pos%130
 def adapter(self):return policy.NumericAgreementAdapter(dict(policy.CACHE_POLICY))
 def test_mixed_hits_exact_half_before_mutable_M(self):
  a,b,li,ri=self.arrays();v1=policy.NumericAgreementAdapter(policy.POLICY);v2=self.adapter();old=np.empty(1024);new=np.empty(1024)
  self.assertTrue(v1.fill(old,a,b,li,ri,1024,ann.agreement,[0]));self.assertTrue(v2.fill(new,a,b,li,ri,1024,ann.agreement,[0]));np.testing.assert_array_equal(old,new)
  new*=.2
  pos=np.arange(512,1536,dtype=np.int64);l=pos//130;r=pos%130
  self.assertTrue(v1.fill(old,a,b,l,r,1024,ann.agreement,[0]));self.assertTrue(v2.fill(new,a,b,l,r,1024,ann.agreement,[0]));np.testing.assert_array_equal(old,new)
  counts=v2.snapshot();self.assertEqual(counts['cache_hit_entries'],512);self.assertEqual(counts['numpy_entries'],1536)
  self.assertLessEqual(counts['cache_reserved_bytes'],32*1024**2);policy._cache_release(v2);self.assertEqual(v2.snapshot()['cache_reserved_bytes'],0)
 def test_zero_partial_oversize_and_policy(self):
  a,b,li,ri=self.arrays();v2=self.adapter();out=np.full(1024,-1.)
  self.assertFalse(v2.fill(out,a,b,li,ri,255,ann.agreement,[0]));self.assertTrue(np.all(out==-1))
  empty=frozen(np.empty((0,2)));self.assertFalse(v2.fill(out,empty,b,li,ri,256,ann.agreement,[0]))
  large=frozen(np.zeros((2000,2)));idx=np.arange(256,dtype=np.int64)
  self.assertTrue(v2.fill(out,large,large,idx,idx,256,ann.agreement,[0]));self.assertEqual(v2.snapshot()['cache_reserved_bytes'],0);self.assertEqual(v2.snapshot()['cache_oversize_chunks'],1)
  for bad in (dict(policy.CACHE_POLICY,max_cache_retained_bytes=32*1024**2+1),dict(policy.CACHE_POLICY,atol=1e-7)):
   with self.assertRaises(ValueError):policy.freeze(bad)
 def test_pair_header_runtime_errmode_rounding_and_trace(self):
  for mutation in ('pair','header','numpy','geterr','rounding','trace'):
   a,b,li,ri=self.arrays();v2=self.adapter();out=np.empty(1024);v2.fill(out,a,b,li,ri,1024,ann.agreement,[0])
   if mutation=='pair':
    with self.assertRaises(ValueError):v2.fill(out,frozen(a),b,li,ri,1024,ann.agreement,[0])
   elif mutation=='header':
    a.shape=(65,4)
    with self.assertRaises(ValueError):v2.fill(out,a,b,li,ri,1024,ann.agreement,[0])
   elif mutation=='numpy':
    with patch.object(np,'exp',lambda *x:None):
     with self.assertRaises(ValueError):v2.fill(out,a,b,li,ri,1024,ann.agreement,[0])
   elif mutation=='geterr':
    with np.errstate(over='raise'):self.assertFalse(v2.fill(out,a,b,li,ri,1024,ann.agreement,[0]))
   elif mutation=='rounding':
    with patch.object(ann,'_nearest_rounding',lambda:0):
     with self.assertRaises(ValueError):v2.fill(out,a,b,li,ri,1024,ann.agreement,[0])
   else:
    sys.settrace(lambda *x:None)
    try:self.assertFalse(v2.fill(out,a,b,li,ri,1024,ann.agreement,[0]))
    finally:sys.settrace(None)
   policy._cache_release(v2)
 def test_fatal_poison_cleanup_preserves_original(self):
  a,b,li,ri=self.arrays();v2=self.adapter();out=np.empty(1024);fatal=KeyboardInterrupt('original')
  def fail(name,value):raise fatal
  with patch.object(phase,'add_count',fail):
   with self.assertRaises(KeyboardInterrupt) as caught:v2.fill(out,a,b,li,ri,1024,ann.agreement,[0])
  self.assertIs(caught.exception,fatal);self.assertIsNone(v2._cache_weights)
  with self.assertRaises(ValueError):v2.current()
 def test_immutable_hits_reuse_numeric_domain_and_invalid_initial_miss_allocates_nothing(self):
  a,b,li,ri=self.arrays();out=np.full(1024,-1.);calls=[];original=policy.kernel.fill_agreement
  def measured(*args):calls.append(args[-1]);return original(*args)
  with patch.object(policy.kernel,'fill_agreement',measured):
   v2=self.adapter();self.assertTrue(v2.fill(out,a,b,li,ri,1024,ann.agreement,[0]));saved=out.copy()
   self.assertTrue(v2.fill(out,a,b,li,ri,1024,ann.agreement,[0]));np.testing.assert_array_equal(out,saved)
   self.assertEqual(calls,[1024]);policy._cache_release(v2)
   invalid=frozen(np.full((130,2),1e200));v2=self.adapter();out[:]=-1.;progress=[0]
   self.assertFalse(v2.fill(out,invalid,b,li,ri,1024,ann.agreement,progress))
   self.assertTrue(np.all(out==-1));self.assertEqual(progress,[0]);self.assertEqual(v2.snapshot()['cache_reserved_bytes'],0)
 def test_mutable_and_subclass_fallback(self):
  a,b,li,ri=self.arrays();out=np.full(1024,-1.);v2=self.adapter()
  class Sub(np.ndarray):pass
  for bad in (a.copy(),a.view(Sub)):
   self.assertFalse(v2.fill(out,bad,b,li,ri,1024,ann.agreement,[0]));self.assertTrue(np.all(out==-1))
  self.assertEqual(v2.snapshot()['cache_reserved_bytes'],0)
 def test_complete_solver_and_checkpoint_recompute(self):
  for edges in (0,32):
   left=graph(edges);right=graph(edges,.031);compare(solve(left,right,CONFIG,1),solve(left,right,CONFIG,2))
  a=graph(130);b=graph(130,.031);old=solve(a,b,CONFIG,1);new=solve(a,b,CONFIG,2);compare(old,new)
  self.assertGreater(new[2]['adapter_lifetimes'][0]['cache_hit_entries'],0)
  self.assertEqual(new[2]['adapter_lifetimes'][0]['cache_reserved_bytes'],0)
  with tempfile.TemporaryDirectory() as temporary:
   reloaded=solve(a,b,CONFIG,2,checkpoint=Path(temporary)/'checkpoint');compare(new,reloaded)
  self.assertEqual(len(reloaded[2]['adapter_lifetimes']),2)
  self.assertGreater(sum(x['numpy_entries'] for x in reloaded[2]['adapter_lifetimes']),sum(x['numpy_entries'] for x in new[2]['adapter_lifetimes']))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--config-sha256',required=True);args,rest=parser.parse_known_args();CONFIG=config(args.config,args.config_sha256)
 unittest.main(argv=[sys.argv[0],*rest],verbosity=2)
