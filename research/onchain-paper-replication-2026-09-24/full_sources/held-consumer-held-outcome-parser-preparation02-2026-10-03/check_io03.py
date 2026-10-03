"""Actual descriptor failures using owned tiny files; no genuine authority."""
import importlib.util,os,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).parent
s=importlib.util.spec_from_file_location('held',P/'held_outcome01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Checks(unittest.TestCase):
 def root(self,name):
  p=P/'adversarial-io03'/name;p.mkdir(parents=True);(p/'data').write_bytes(b'abc');return p.resolve()
 def test_growth(self):
  p=self.root('growth');read=os.read;once=[]
  def changed(fd,n):
   if not once:
    once.append(1)
    with (p/'data').open('ab') as f:f.write(b'xyz')
   return read(fd,n)
  with patch.object(m.os,'read',changed),self.assertRaisesRegex(ValueError,'grew'):m.Reader(p).body('data',6)
 def test_parent_redirect(self):
  p=self.root('redirect');read=os.read;once=[]
  def changed(fd,n):
   if not once:
    once.append(1);p.rename(p.with_name('redirect-retained'));p.symlink_to(p.with_name('redirect-retained'),target_is_directory=True)
   return read(fd,n)
  with patch.object(m.os,'read',changed),self.assertRaises(ValueError):m.Reader(p).body('data')
 def test_read_fatal_independent_close(self):
  p=self.root('fatal');first=MemoryError('read');close=os.close;seen=[]
  def later(fd):seen.append(fd);close(fd);raise OSError('after actual close')
  with patch.object(m.os,'read',side_effect=first),patch.object(m.os,'close',later),self.assertRaises(MemoryError) as found:m.Reader(p).body('data')
  self.assertIs(found.exception,first);self.assertEqual(len(seen),2);self.assertEqual(len(set(seen)),2)
 def test_changed_between_reads(self):
  p=self.root('changed');r=m.Reader(p);r.body('data');(p/'data').write_bytes(b'xyz')
  with self.assertRaisesRegex(ValueError,'between checks'):r.body('data')
if __name__=='__main__':unittest.main()
