import importlib.util,os,sys,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent
P=Path(os.environ.get('CANDIDATE_SOURCE',H/'non_tail_context.py'))
spec=importlib.util.spec_from_file_location('candidate03',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_actual_reviewer_redirect(self):
  owned=H/os.environ.get('WITNESS','witness-green');owned.mkdir();parent=owned/'parent';parent.mkdir();p=parent/'dependency.py';p.write_bytes(b'original safe source');moved=owned/'moved';done=[];real=os.read
  def read(fd,n):
   if not done:parent.rename(moved);parent.symlink_to(moved,target_is_directory=True);done.append(1)
   return real(fd,n)
  with patch.object(m.os,'read',side_effect=read):
   with self.assertRaises(ValueError):m.bootstrap_read(p)
  self.assertTrue(parent.is_symlink());self.assertNotEqual(p.resolve(),p)
 def test_regular_parent_replacement(self):
  with tempfile.TemporaryDirectory() as d:
   parent=Path(d)/'p';parent.mkdir();p=parent/'x';p.write_bytes(b'abc');done=[];real=os.read
   def read(fd,n):
    if not done:parent.rename(Path(d)/'moved');parent.mkdir();p.write_bytes(b'abc');done.append(1)
    return real(fd,n)
   with patch.object(m.os,'read',side_effect=read):
    with self.assertRaises(ValueError):m.bootstrap_read(p)
 def test_file_replacement(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';p.write_bytes(b'abc');real=os.read;done=[]
   def read(fd,n):
    if not done:p.rename(Path(d)/'old');p.write_bytes(b'abc');done.append(1)
    return real(fd,n)
   with patch.object(m.os,'read',side_effect=read):
    with self.assertRaises(ValueError):m.bootstrap_read(p)
 def test_firstfatal_and_independent_closes(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';p.write_bytes(b'abc');first=MemoryError('first');seen=[];real=os.close
   def close(fd):seen.append(fd);real(fd);raise OSError('uncertain')
   with patch.object(m.os,'read',side_effect=first),patch.object(m.os,'close',side_effect=close):
    with self.assertRaises(MemoryError) as got:m.bootstrap_read(p)
   self.assertIs(got.exception,first);self.assertEqual(len(seen),2);self.assertEqual(len(set(seen)),2)
 def test_ordinary_close_then_first_actual_fatal(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';p.write_bytes(b'abc');first=SystemExit('first fatal');seen=[];real=os.close
   def close(fd):
    seen.append(fd);real(fd)
    if len(seen)==1:raise OSError('ordinary close')
    raise first
   with patch.object(m.os,'close',side_effect=close):
    with self.assertRaises(SystemExit) as got:m.bootstrap_read(p)
   self.assertIs(got.exception,first);self.assertEqual(len(set(seen)),2)
 def test_child_open_failure_closes_parent(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'missing';opened=[];closed=[];ro=os.open;rc=os.close
   def op(*a,**kw):fd=ro(*a,**kw);opened.append(fd);return fd
   def cl(fd):closed.append(fd);return rc(fd)
   with patch.object(m.os,'open',side_effect=op),patch.object(m.os,'close',side_effect=cl):
    with self.assertRaises(FileNotFoundError):m.bootstrap_read(p)
   self.assertEqual(len(opened),1);self.assertEqual(closed,opened)
if __name__=='__main__':unittest.main(verbosity=2)
