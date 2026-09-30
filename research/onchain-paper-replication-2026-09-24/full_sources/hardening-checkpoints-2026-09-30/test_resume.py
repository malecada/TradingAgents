import importlib.util
from pathlib import Path
import hashlib
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from tradingagents.research.onchain_replication.matching_reference import harden
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('resume',HERE/'resume.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def identity(x):return hashlib.sha256(x.tobytes()).hexdigest()

class Tests(unittest.TestCase):
 def finish(self,s,x):
  for _ in range(1000):
   if s['phase']=='done':break
   m.advance(s,x,input_sha256=identity(x),max_chunks=1)
  else:self.fail('did not terminate')
  out=np.zeros(x.shape,dtype=np.int8)
  for u,i in s['pairs']:out[u,i]=1
  np.testing.assert_array_equal(out,harden(x))
 def test_checkpoints_every_chunk_exact_row_major_and_integer_cast(self):
  cases=[np.array([[3.,3.,1.],[2.,1.,2.]]),np.zeros((4,3)),np.array([[2**60,2**60+1],[1,2]],dtype=np.int64),np.arange(20.).reshape(5,4)[:,::-1],np.empty((0,3))]
  for x in cases:
   s=m.create(x,input_sha256=identity(x),max_buffer_bytes=100000,chunk_entries=2)
   for _ in range(1000):
    if s['phase']=='done':break
    m.advance(s,x,input_sha256=identity(x),max_chunks=1)
    with tempfile.TemporaryDirectory() as tmp:
     path=Path(tmp)/'state.json';digest=m.save(s,path,max_checkpoint_bytes=100000)
     s=m.load(path,expected_sha256=digest,max_checkpoint_bytes=100000)
   self.finish(s,x)
 def test_tampering_identity_and_limits(self):
  x=np.ones((3,2))
  with self.assertRaises(ValueError):m.create(x,input_sha256=identity(x),max_buffer_bytes=1,chunk_entries=2)
  s=m.create(x,input_sha256=identity(x),max_buffer_bytes=10000,chunk_entries=2)
  with self.assertRaises(ValueError):m.advance(s,x,input_sha256='0'*64,max_chunks=1)
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'s.json'
   with self.assertRaises(ValueError):m.save(s,path,max_checkpoint_bytes=1)
   self.assertFalse(path.exists())
   digest=m.save(s,path,max_checkpoint_bytes=10000)
   with self.assertRaises(FileExistsError):m.save(s,path,max_checkpoint_bytes=10000)
   path.write_bytes(path.read_bytes()+b' ')
   with self.assertRaises(ValueError):m.load(path,expected_sha256=digest,max_checkpoint_bytes=10000)
 def test_nonfinite_validation_before_any_selection(self):
  x=np.array([[4.,3.],[2.,np.nan]])
  s=m.create(x,input_sha256=identity(x),max_buffer_bytes=10000,chunk_entries=1)
  with self.assertRaises(ValueError):m.advance(s,x,input_sha256=identity(x),max_chunks=10)
  self.assertEqual(s['pairs'],[]);self.assertFalse(s['safe'])
 def test_interruption_poisons_scratch_and_retains_prior_checkpoint(self):
  x=np.arange(6.).reshape(3,2);s=m.create(x,input_sha256=identity(x),max_buffer_bytes=10000,chunk_entries=2)
  m.advance(s,x,input_sha256=identity(x),max_chunks=3)
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'prior.json';digest=m.save(s,path,max_checkpoint_bytes=10000)
   with patch.object(m.np,'argmax',side_effect=KeyboardInterrupt):
    with self.assertRaises(KeyboardInterrupt):m.advance(s,x,input_sha256=identity(x),max_chunks=1)
   with self.assertRaises(ValueError):m.save(s,Path(tmp)/'bad.json',max_checkpoint_bytes=10000)
   self.finish(m.load(path,expected_sha256=digest,max_checkpoint_bytes=10000),x)
 def test_unreachable_state_and_duplicate_assignment_refused(self):
  x=np.ones((3,2));s=m.create(x,input_sha256=identity(x),max_buffer_bytes=10000,chunk_entries=2)
  for edit in ({'phase':'done'},{'pairs':[[0,0],[0,1]],'phase':'done'},{'cursor':1}):
   bad=s|edit
   with tempfile.TemporaryDirectory() as tmp:
    with self.assertRaises(ValueError):m.save(bad,Path(tmp)/'invalid.json',max_checkpoint_bytes=10000)
if __name__=='__main__':unittest.main(verbosity=2)
