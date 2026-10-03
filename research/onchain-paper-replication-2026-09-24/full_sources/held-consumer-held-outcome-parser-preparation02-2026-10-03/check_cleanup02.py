import importlib.util,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
source=Path(sys.argv.pop(1)) if len(sys.argv)>1 else P/'held_outcome01.py'
s=importlib.util.spec_from_file_location('held_candidate',source);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Checks(unittest.TestCase):
 def fake(self,primary,late=None,closed_late=None):
  calls=[]
  class Stream:
   @property
   def closed(self):calls.append('closed');raise closed_late or AssertionError('unnecessary closed observation')
   def close(self):calls.append('close')
  class Child:
   stdin=Stream();stdout=Stream();stderr=Stream()
   def poll(self):calls.append('poll');raise late or AssertionError('unnecessary poll observation')
   def kill(self):calls.append('kill')
   def wait(self,timeout):calls.append('wait');return -9
  with patch.object(m.subprocess,'Popen',return_value=Child()),patch.object(m.selectors,'DefaultSelector',side_effect=primary):
   with self.assertRaises(type(primary)) as result:m.git(P,['--version'])
  self.assertIs(result.exception,primary);self.assertEqual(calls,['kill','wait','close','close','close'])
 def test_exact_reviewer_poll_oserror(self):self.fake(MemoryError('original'),OSError('later poll'))
 def test_exact_reviewer_poll_systemexit(self):self.fake(MemoryError('original'),SystemExit('later poll'))
 def test_closed_observation_avoided(self):self.fake(MemoryError('original'),closed_late=SystemExit('closed'))
 def test_independent_actions_and_first_fatal(self):
  for primary in (MemoryError('first'),KeyboardInterrupt('first'),SystemExit('first'),ValueError('ordinary')):
   calls=[];later=MemoryError('kill fatal')
   class Stream:
    def close(self):calls.append('close');raise OSError('close uncertain')
   class Child:
    stdin=Stream();stdout=Stream();stderr=Stream()
    def kill(self):calls.append('kill');raise later
    def wait(self,timeout):calls.append('wait');raise OSError('wait uncertain')
   with patch.object(m.subprocess,'Popen',return_value=Child()),patch.object(m.selectors,'DefaultSelector',side_effect=primary):
    with self.assertRaises(BaseException) as result:m.git(P,['--version'])
   self.assertIs(result.exception,primary if m.fatal(primary) else later);self.assertEqual(calls,['kill','wait','close','close','close'])
 def test_actual_reaped_git_positive(self):
  result=m.git(P,['--version'],cap=1024);self.assertTrue(result.startswith(b'git version '))
 def test_actual_alive_child_kill_reap_fd_release(self):
  popen=subprocess.Popen;children=[];first=MemoryError('selector birth')
  def child(*args,**kw):
   obj=popen([sys.executable,'-B','-c','import time; time.sleep(20)'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);children.append(obj);return obj
  with patch.object(m.subprocess,'Popen',side_effect=child),patch.object(m.selectors,'DefaultSelector',side_effect=first):
   with self.assertRaises(MemoryError) as result:m.git(P,['--version'])
  self.assertIs(result.exception,first);self.assertEqual(len(children),1);c=children[0]
  self.assertIsNotNone(c.poll());self.assertTrue(all(s.closed for s in (c.stdin,c.stdout,c.stderr)))
if __name__=='__main__':unittest.main()
