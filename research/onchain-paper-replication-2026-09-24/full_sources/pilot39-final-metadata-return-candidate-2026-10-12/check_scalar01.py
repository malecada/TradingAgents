"""Offline scalar checks only; no Git or helper main invocation."""
import runpy,tempfile,hashlib,unittest
from pathlib import Path
M=runpy.run_path(str(Path(__file__).with_name('return_final01.py')))
class Checks(unittest.TestCase):
 def test_pins(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();p=root/'a';p.write_bytes(b'abc');p.chmod(0o600)
   ref={'path':'a','sha256':hashlib.sha256(b'abc').hexdigest(),'bytes':3,'mode':'0600'}
   self.assertEqual(M['read_pin'](root,ref),b'abc')
   for change in ({'bytes':True},{'bytes':4*1024**2+1},{'sha256':'0'*64},{'mode':'0644'}):
    with self.assertRaises(AssertionError):M['read_pin'](root,{**ref,**change})
   p.write_bytes(b'xyz')
   with self.assertRaises(AssertionError):M['read_pin'](root,ref)
   q=root/'link';q.symlink_to(p)
   with self.assertRaises(AssertionError):M['read_pin'](root,{**ref,'path':'link'})
 def test_fixed_paths(self):
  self.assertEqual(len(set(M['PATHS'])),3)
  self.assertEqual(tuple(Path(x).name for x in M['PATHS']),('BINDING01.json','RELEASE_REVIEW01.json','BINDING_REVIEW02.json'))
if __name__=='__main__':unittest.main()
