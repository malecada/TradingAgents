import ast,hashlib,importlib.util,os,stat,sys,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent
P=Path(os.environ.get('CANDIDATE_SOURCE',str(H/'non_tail_context.py')))
def module():
 spec=importlib.util.spec_from_file_location('context_under_test',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=module()
def policy(**x):
 p=dict(max_rounded_bytes=1048576,max_commands=10,max_parts=10,part_bytes=128,deadline_seconds=60);p.update(x);return p
class Tests(unittest.TestCase):
 def test_bounded_bootstrap_firstfatal(self):
  fatal=MemoryError('first');real=os.close;seen=[]
  def close(fd):seen.append(fd);real(fd);raise OSError('close')
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.py';p.write_bytes(b'abc')
   with patch.object(m.os,'read',side_effect=fatal),patch.object(m.os,'close',side_effect=close):
    with self.assertRaises(MemoryError) as got:m.bootstrap_read(p)
   self.assertIs(got.exception,fatal);self.assertEqual(len(seen),2)
 def test_bound_before_read(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.py';p.write_bytes(b'x'*(1048576+1))
   with patch.object(m.os,'read',side_effect=AssertionError('must not read')):
    with self.assertRaises(ValueError):m.bootstrap_read(p)
 def test_growth_refusal(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.py';p.write_bytes(b'abc');real=os.read;done=[]
   def read(fd,n):
    if not done:
     done.append(1)
     with p.open('ab') as f:f.write(b'd')
    return real(fd,n)
   with patch.object(m.os,'read',side_effect=read):
    with self.assertRaises(ValueError):m.bootstrap_read(p)
 def test_bootstrap_valid(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.py';p.write_bytes(b'abc');self.assertEqual(m.bootstrap_read(p),b'abc')
 def test_foreign_threads_no_lost_spend(self):
  b=m.Reservations(policy(max_commands=1));success=[];errors=[];barrier=threading.Barrier(2);old=m.require
  def interleave(v,msg):
   old(v,msg)
   if msg=='cumulative reservation exhausted':barrier.wait(timeout=2)
  def reserve():
   try:success.append(dict(b.reserve(1)))
   except BaseException as e:errors.append(type(e).__name__)
  with patch.object(m,'require',side_effect=interleave):
   ts=[threading.Thread(target=reserve) for _ in range(2)]
   for t in ts:t.start()
   for t in ts:t.join(3);self.assertFalse(t.is_alive())
  self.assertEqual(success,[]);self.assertEqual(len(errors),2);self.assertTrue(b.revoked);self.assertEqual(b.spent['commands'],0)
 def test_same_thread_reentrancy_revokes(self):
  b=m.Reservations(policy());old=m.require;inside=[]
  def hook(v,msg):
   old(v,msg)
   if msg=='cumulative reservation exhausted' and not inside:
    inside.append(1)
    try:b.reserve(1)
    except ValueError:pass
  with patch.object(m,'require',side_effect=hook):
   with self.assertRaises(ValueError):b.reserve(1)
  self.assertTrue(b.revoked);self.assertEqual(b.spent['commands'],0)
 def test_actual_transport_rounding(self):
  b=m.Reservations(policy());b.reserve(32768);self.assertEqual(b.spent['rounded_bytes'],65536)
  b.reserve(1);self.assertEqual(b.spent['rounded_bytes'],98304)
 def test_clean_close_poisons_shared_alias(self):
  spec=importlib.util.spec_from_file_location('tinyformat',m.D/'test_formats02.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);ref=f.batches(root);budget=m.Reservations(policy());alias=budget;cm=m.open_context(root,kind='score-batches',document_sha256=ref,limits=budget);c=cm.__enter__();rootfd=c._reader.fd;closed=[];real=os.close
   def close(fd):
    real(fd)
    if fd==rootfd:closed.append(fd);raise OSError('root close uncertainty')
   with patch.object(m.reader.os,'close',side_effect=close):
    with self.assertRaises(m.io.CleanupFailure):cm.__exit__(None,None,None)
   self.assertEqual(closed,[rootfd]);self.assertTrue(c.revoked);self.assertTrue(alias.revoked)
   with self.assertRaises(ValueError):alias.reserve(1)
 def test_positive_shared(self):
  b=m.Reservations(policy());b.reserve(1);b.reserve(1);self.assertEqual(b.spent['commands'],2)
 def test_failed_reader_birth_revokes_alias(self):
  b=m.Reservations(policy())
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises((ValueError,FileNotFoundError)):
    with m.open_context(Path(d),kind='score-batches',document_sha256='ab'*32,limits=b):pass
  self.assertTrue(b.revoked)
 def test_bootstrap_fatal_close_promoted(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.py';p.write_bytes(b'abc');fatal=SystemExit('close fatal');real=os.close;seen=[]
   def close(fd):real(fd);seen.append(fd);raise fatal
   with patch.object(m.os,'read',side_effect=ValueError('body')),patch.object(m.os,'close',side_effect=close):
    with self.assertRaises(SystemExit) as got:m.bootstrap_read(p)
   self.assertIs(got.exception,fatal);self.assertEqual(len(seen),2)
if __name__=='__main__':unittest.main(verbosity=2)
