import importlib.util,pathlib,tempfile,unittest
from unittest.mock import patch
P=pathlib.Path(__file__).parent;s=importlib.util.spec_from_file_location('c',P/'launcher02.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_ordinary_then_first_fatal_marker_promoted(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)/'root';root.mkdir();out=pathlib.Path(d)/'out';out.mkdir();fatal=MemoryError('marker failure');original=m.write;names=[]
   def write(directory,name,data):
    names.append(name)
    if name=='failure.json':raise fatal
    return original(directory,name,data)
   with patch.object(m,'write',side_effect=write),patch.object(m,'root_watch',return_value={'files':0,'allocated_bytes':0}):result=m.finish_tail(out,root,'synthetic',{'phase':'materialize','source':'a'*40},{},None,{},ValueError('ordinary first'),None,())
   self.assertIs(result,fatal);self.assertIn('late-failure.json',names);self.assertTrue((out/'late-failure.json').exists())
 def test_observation_publication_failure_remains_failed(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)/'root';root.mkdir();out=pathlib.Path(d)/'out';out.mkdir();error=OSError('observation write');original=m.write
   def write(directory,name,data):
    if name=='observation.json':raise error
    return original(directory,name,data)
   with patch.object(m,'write',side_effect=write),patch.object(m,'root_watch',return_value={'files':0,'allocated_bytes':0}):result=m.finish_tail(out,root,'synthetic',{'phase':'materialize','source':'a'*40},{},None,{},None,{'synthetic':True},())
   self.assertIs(result,error);self.assertTrue((out/'failure.json').exists());self.assertFalse((out/'tail-complete.json').exists())
if __name__=='__main__':unittest.main(verbosity=2)
