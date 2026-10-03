import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from test_projection01 import load
class IOTests(unittest.TestCase):
 def test_actual_reader_firstfatal_survives_close_once(self):
  m=load()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'metadata.json';p.write_bytes(b'{}');fatal=MemoryError('original');calls=[];close=os.close
   def badclose(fd):calls.append(fd);close(fd);raise OSError('uncertain close')
   with patch.object(m.os,'read',side_effect=fatal),patch.object(m.os,'close',side_effect=badclose):
    try:m._read(p,8192)
    except BaseException as got:self.assertIs(got,fatal)
    else:self.fail('fatal suppressed')
   self.assertEqual(len(calls),1)
 def test_actual_reader_link_and_extent_refusal(self):
  m=load()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'metadata.json';p.write_bytes(b'{}')
   self.assertEqual(m._read(p,2),b'{}')
   with self.assertRaises(ValueError):m._read(p,1)
   q=Path(d)/'linked';os.link(p,q)
   with self.assertRaises(ValueError):m._read(p,2)
 def test_actual_reader_laterfatal_promotes_ordinary_primary(self):
  m=load()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'metadata.json';p.write_bytes(b'{}');fatal=SystemExit(7);close=os.close;calls=[]
   def badclose(fd):calls.append(fd);close(fd);raise fatal
   with patch.object(m.os,'read',side_effect=OSError('body')),patch.object(m.os,'close',side_effect=badclose):
    try:m._read(p,8192)
    except BaseException as got:self.assertIs(got,fatal)
    else:self.fail('fatal suppressed')
   self.assertEqual(len(calls),1)
if __name__=='__main__':unittest.main()
