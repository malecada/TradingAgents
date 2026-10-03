"""Actual git() body with tiny process stand-ins, never genuine authority."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).parent;name=sys.argv.pop(1)
s=importlib.util.spec_from_file_location('helper',P/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Checks(unittest.TestCase):
 def test_prior_fatal_poll_closed_uncertainty(self):
  first=MemoryError('selector allocation');events=[]
  class Pipe:
   def __init__(self,name):self.name=name
   @property
   def closed(self):raise OSError('untrusted closed read')
   def close(self):events.append(self.name)
  class Child:
   stdin=Pipe('stdin');stdout=Pipe('stdout');stderr=Pipe('stderr')
   def poll(self):raise OSError('untrusted poll')
   def kill(self):events.append('kill');raise OSError('kill uncertainty')
   def wait(self,timeout):events.append('wait')
  with patch.object(m.subprocess,'Popen',return_value=Child()),patch.object(m.selectors,'DefaultSelector',side_effect=first),self.assertRaises(MemoryError) as got:m.git(P,[])
  self.assertIs(got.exception,first);self.assertEqual(events,['kill','wait','stdin','stdout','stderr'])
if __name__=='__main__':unittest.main()
