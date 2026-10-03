import importlib.util,unittest,tempfile,os
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).parent;s=importlib.util.spec_from_file_location('recovery',P/'recovery01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Checks(unittest.TestCase):
 def test_write_firstfatal_closes_both_once(self):
  with tempfile.TemporaryDirectory(dir=P) as d:
   first=MemoryError('write');close=os.close;fds=[]
   def later(fd):fds.append(fd);close(fd);raise OSError('later close')
   with patch.object(m.os,'write',side_effect=first),patch.object(m.os,'close',side_effect=later),self.assertRaises(MemoryError) as e:m.put(Path(d)/'retained',{'a':1})
   self.assertIs(e.exception,first);self.assertEqual(len(fds),len(set(fds)));self.assertEqual(len(fds),2);self.assertTrue((Path(d)/'retained').exists())
 def test_request_no_placeholder(self):
  with self.assertRaises(ValueError):m.request({})
 def test_parent_replace_writer(self):
  with tempfile.TemporaryDirectory(dir=P) as d:
   root=Path(d);p=root/'owned';p.mkdir()
   with self.assertRaises(ValueError):
    with m.new_file(p/'body') as fd:
     p.rename(root/'retained');p.symlink_to(root/'retained',target_is_directory=True);os.write(fd,b'kept')
if __name__=='__main__':unittest.main()
