import importlib.util,unittest,tempfile,os
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).parent;s=importlib.util.spec_from_file_location('recover',P/'recovery03.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Checks(unittest.TestCase):
 def setUp(self):
  self.base=Path(tempfile.mkdtemp(prefix='synthetic-io-',dir=P));self.r=self.base/'root';self.r.mkdir();(self.r/'body').write_bytes(b'abc')
 def test_firstfatal_allfds(self):
  first=MemoryError('first');close=os.close;seen=[]
  def later(fd):seen.append(fd);close(fd);raise OSError('uncertain')
  with patch.object(m.os,'read',side_effect=first),patch.object(m.os,'close',side_effect=later),self.assertRaises(MemoryError) as found:m.read(self.r,'body')
  self.assertIs(found.exception,first);self.assertEqual(len(seen),2);self.assertEqual(len(set(seen)),2)
 def test_parent_replaced(self):
  original=os.read;once=[]
  def replace(fd,n):
   if not once:once.append(1);self.r.rename(self.base/'retained');self.r.symlink_to(self.base/'retained',target_is_directory=True)
   return original(fd,n)
  with patch.object(m.os,'read',side_effect=replace),self.assertRaises(ValueError):m.read(self.r,'body')
 def test_growth(self):
  original=os.read;once=[]
  def grow(fd,n):
   if not once:once.append(1);(self.r/'body').write_bytes(b'abcdef')
   return original(fd,n)
  with patch.object(m.os,'read',side_effect=grow),self.assertRaises(ValueError):m.read(self.r,'body')
 def test_extra_trailing_framing(self):
  manifest=m.scan(self.r);a=self.base/'a.gz';info=m.pack(self.r,manifest,a);raw=a.read_bytes()+b'TRAILING';a.write_bytes(raw);info.update(bytes=len(raw),sha256=m.digest(raw))
  dest=self.base/'restore';dest.mkdir(mode=0o700)
  with self.assertRaises((ValueError,OSError,EOFError)):m.restore(a,info,manifest,dest)
 def test_fifo(self):
  os.mkfifo(self.r/'fifo')
  with self.assertRaises(ValueError):m.scan(self.r)
 def test_archive_overflow(self):
  sink=m.Sink();sink.count=m.FILE
  with self.assertRaises(ValueError):sink.write(b'x')
if __name__=='__main__':unittest.main()
