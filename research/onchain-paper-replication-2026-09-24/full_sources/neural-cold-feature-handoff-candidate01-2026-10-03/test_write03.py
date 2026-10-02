import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
HERE=Path(__file__).resolve().parent
class Write(unittest.TestCase):
 def module(self):
  spec=importlib.util.spec_from_file_location('cold_files',HERE/'cold_files.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
  self.assertTrue(hasattr(m,'write_once'),'held exclusive writer absent');return m
 def test_exclusive_exact_bytes(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);s=p.stat();inode=(s.st_dev,s.st_ino);m.write_once(p,inode,'start.json',b'abc',10)
   self.assertEqual((p/'start.json').read_bytes(),b'abc')
   with self.assertRaises(FileExistsError):m.write_once(p,inode,'start.json',b'def',10)
   self.assertEqual((p/'start.json').read_bytes(),b'abc')
 def test_wrong_inode_and_oversize_leave_no_file(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);s=p.stat();inode=(s.st_dev,s.st_ino)
   for pin,raw,cap in [((0,0),b'x',10),(inode,b'abcd',3)]:
    with self.assertRaises(ValueError):m.write_once(p,pin,'start.json',raw,cap)
    self.assertFalse((p/'start.json').exists())
if __name__=='__main__':unittest.main(verbosity=2)
