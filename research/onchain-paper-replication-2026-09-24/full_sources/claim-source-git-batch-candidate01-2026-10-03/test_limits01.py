import importlib.util,pathlib,unittest
from unittest.mock import patch
P=pathlib.Path(__file__).parent;s=importlib.util.spec_from_file_location('candidate',P/'candidate01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Limits(unittest.TestCase):
 def test_request_bound_before_spawn(self):
  with patch.object(m.subprocess,'Popen',side_effect=AssertionError('must not spawn')):
   with self.assertRaises(ValueError):m._git_transport(P,b'x'*65537)
   with self.assertRaises(ValueError):m._git_transport(P,b'', 'x'*131073)
 def test_all_cleanup_attempts_first_fatal_and_uncertainty(self):
  events=[];fatal=MemoryError('first')
  def fail(name,e):
   def action():events.append(name);raise e
   return action
  with self.assertRaises(MemoryError) as found:
   m._git_cleanup((fail('kill',OSError()),fail('reap',fatal),fail('stdin',SystemExit()),fail('stdout',OSError()),lambda:events.append('stderr')),ValueError())
  self.assertIs(found.exception,fatal);self.assertEqual(events,['kill','reap','stdin','stdout','stderr'])
  with self.assertRaises(m._GitCleanupFailure):m._git_cleanup((fail('last',OSError()),),None)
 def test_changed_body_second_invocation_not_cached(self):
  values=[b'a',b'b']
  def response(*args):
   body=values.pop(0);return b'1'*40+b' blob 1\n'+body+b'\n'
  with patch.object(m,'_git_transport',side_effect=response):
   m._verify_sources(P,{'x':m.hashlib.sha256(b'a').hexdigest()},{'1'*40})
   with self.assertRaisesRegex(ValueError,'hash mismatch'):m._verify_sources(P,{'x':m.hashlib.sha256(b'a').hexdigest()},{'1'*40})
 def test_distinct_commits_original_iteration(self):
  commits={'1'*40,'2'*40};seen=[]
  def response(root,request):
   seen.extend(request.splitlines());return (b'1'*40+b' blob 1\na\n')*2
  with patch.object(m,'_git_transport',side_effect=response):m._verify_sources(P,{'x':m.hashlib.sha256(b'a').hexdigest()},commits)
  self.assertEqual(seen,[(c+':x').encode() for c in commits])
unittest.main()
