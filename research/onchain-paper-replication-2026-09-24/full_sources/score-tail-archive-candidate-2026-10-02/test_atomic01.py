import importlib.util,os,pathlib,unittest
from unittest.mock import patch
P=pathlib.Path(__file__).with_name('score_tail_archive.py')
spec=importlib.util.spec_from_file_location('tail_candidate',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Atomic(unittest.TestCase):
 def method(self):
  self.assertTrue(hasattr(m,'publish_receipt'),'atomic exclusive receipt publication missing');return m.publish_receipt
 def test_atomic_receipt_rejects_existing_target_without_overwrite(self):
  publish=self.method();root=P.parent/'fixture-atomic01';root.mkdir();fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
  try:
   ref=publish(fd,'complete.json',b'abc');self.assertEqual(ref,m.digest(b'abc'))
   self.assertEqual(sorted(x.name for x in root.iterdir()),['complete.json'])
   with self.assertRaises(FileExistsError):publish(fd,'complete.json',b'new')
   self.assertEqual((root/'complete.json').read_bytes(),b'abc')
   self.assertEqual((root/'pending-complete.json').read_bytes(),b'new')
  finally:os.close(fd)
 def test_cleanup_parent_close_failure_also_closes_owned_child_once(self):
  root=P.parent/('fixture-close-'+str(os.getpid()));real=m.os.close;seen=[];fatal=KeyboardInterrupt('first close')
  def close(fd):
   seen.append(fd);real(fd)
   if len(seen)==1:raise fatal
  # Constructor's parent close fails only after the new child descriptor exists.
  with patch.object(m.os,'close',close):
   from test_candidate01 import fixture
   c,*parts=fixture()
   with self.assertRaises(KeyboardInterrupt) as caught:m.LocalChunk(root,c,lease=lambda:None)
  self.assertIs(caught.exception,fatal);self.assertEqual(len(seen),2);self.assertNotEqual(seen[0],seen[1])
if __name__=='__main__':unittest.main(verbosity=2)
