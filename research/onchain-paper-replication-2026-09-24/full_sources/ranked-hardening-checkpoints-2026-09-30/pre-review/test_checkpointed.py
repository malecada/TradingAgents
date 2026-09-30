from pathlib import Path
import importlib.util,hashlib,tempfile,unittest
from unittest.mock import patch
import numpy as np
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('checkpointed',HERE/'checkpointed.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
spec=importlib.util.spec_from_file_location('ranked',HERE.with_name('ranked-hardening-2026-09-30')/'ranked.py');ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)

def identity(x):return hashlib.sha256(memoryview(x).cast('B')).hexdigest()
class Tests(unittest.TestCase):
 def create(self,x):return m.create(x,max_pair_entries=4_000_000,max_explicit_bytes=1_000_000)
 def finish(self,s):
  while s['phase']!='done':m.advance(s,input_sha256=s['input_sha256'],max_entries=2)
  return s['pairs']
 def test_every_boundary_restore_exact_order(self):
  rng=np.random.default_rng(28)
  for x in [np.zeros((4,3)),rng.integers(-3,4,(7,4)).astype(float),rng.normal(size=(3,8)),np.empty((0,3))]:
   s=self.create(x)
   with tempfile.TemporaryDirectory() as tmp:
    initial=Path(tmp)/'initial';h=m.save(s,initial,max_checkpoint_bytes=1_000_000)
    s=m.load(initial,expected_sha256=h,input_sha256=s['input_sha256'],max_pair_entries=4_000_000,max_explicit_bytes=1_000_000)
    for step in range(100):
     if s['phase']=='done':break
     m.advance(s,input_sha256=identity(x),max_entries=1)
     p=Path(tmp)/str(step);h=m.save(s,p,max_checkpoint_bytes=1_000_000)
     s=m.load(p,expected_sha256=h,input_sha256=identity(x),max_pair_entries=4_000_000,max_explicit_bytes=1_000_000)
    else:self.fail('did not finish')
   expected=ref.harden_pairs(x,max_pair_entries=4_000_000,max_explicit_bytes=1_000_000).tolist()
   self.assertEqual(s['pairs'],expected)
 def test_limits_identity_and_exclusive_publication(self):
  x=np.ones((3,2));s=self.create(x)
  with self.assertRaises(ValueError):m.create(x,max_pair_entries=5,max_explicit_bytes=100000)
  with self.assertRaises(ValueError):m.create(x,max_pair_entries=6,max_explicit_bytes=1)
  with self.assertRaises(ValueError):m.create(np.array([[np.nan]]),max_pair_entries=6,max_explicit_bytes=100000)
  with self.assertRaises(ValueError):m.advance(s,input_sha256='0'*64,max_entries=1)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'s'
   with self.assertRaises(ValueError):m.save(s,p,max_checkpoint_bytes=1)
   self.assertFalse(p.exists());h=m.save(s,p,max_checkpoint_bytes=100000)
   with self.assertRaises(FileExistsError):m.save(s,p,max_checkpoint_bytes=100000)
   with self.assertRaises(ValueError):m.load(p,expected_sha256=h,input_sha256=identity(x),max_pair_entries=5,max_explicit_bytes=1000000)
   (p/'order.npy').write_bytes((p/'order.npy').read_bytes()+b'x')
   with self.assertRaises(ValueError):m.load(p,expected_sha256=h,input_sha256=identity(x),max_pair_entries=4000000,max_explicit_bytes=1000000)
 def test_interruption_requires_prior_checkpoint(self):
  x=np.zeros((4,3));s=self.create(x)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'prior';h=m.save(s,p,max_checkpoint_bytes=100000)
   with patch.object(m,'_accept',side_effect=KeyboardInterrupt):
    with self.assertRaises(KeyboardInterrupt):m.advance(s,input_sha256=identity(x),max_entries=2)
   self.assertFalse(s['safe'])
   with self.assertRaises(ValueError):m.save(s,Path(tmp)/'bad',max_checkpoint_bytes=100000)
   restored=m.load(p,expected_sha256=h,input_sha256=identity(x),max_pair_entries=4000000,max_explicit_bytes=1000000)
   self.assertEqual(self.finish(restored),[[0,0],[1,1],[2,2]])
 def test_structural_corruption_refused(self):
  x=np.ones((3,2));s=self.create(x)
  for edit in ({'phase':'done'},{'cursor':7},{'pairs':[[0,0],[0,1]]}):
   with tempfile.TemporaryDirectory() as tmp:
    with self.assertRaises(ValueError):m.save(s|edit,Path(tmp)/'invalid',max_checkpoint_bytes=100000)
if __name__=='__main__':unittest.main(verbosity=2)
