import importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).parent;s=importlib.util.spec_from_file_location('candidate',P/'held_outcome01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Check(unittest.TestCase):
 def test_selector_and_all_streams_after_fatal(self):
  calls=[];first=MemoryError('setblocking');later=SystemExit('kill')
  class Stream:
   def fileno(self):return 1
   def close(self):calls.append('stream');raise OSError('close')
  class Child:
   stdin=Stream();stdout=Stream();stderr=Stream()
   def kill(self):calls.append('kill');raise later
   def wait(self,timeout):calls.append('wait');raise OSError('wait')
  class Selector:
   def close(self):calls.append('selector');raise KeyboardInterrupt('selector')
  with patch.object(m.subprocess,'Popen',return_value=Child()),patch.object(m.selectors,'DefaultSelector',return_value=Selector()),patch.object(m.os,'set_blocking',side_effect=first):
   with self.assertRaises(MemoryError) as r:m.git(P,['--version'])
  self.assertIs(r.exception,first);self.assertEqual(calls,['kill','wait','stream','stream','stream','selector'])
if __name__=='__main__':unittest.main()
