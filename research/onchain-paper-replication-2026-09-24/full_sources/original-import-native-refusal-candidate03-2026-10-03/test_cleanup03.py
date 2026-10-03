"""Extract actual producer except handler; qualified lease/IO error sentinels only."""
import ast,os,sys,unittest
from pathlib import Path
from types import SimpleNamespace
D=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('MCM_SOURCE',D.parent/'original-import-native-refusal-candidate02-2026-10-03/compact_mcm.py'))
def handler():
 tree=ast.parse(SOURCE.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked')
 h=next(n for n in ast.walk(function) if isinstance(n,ast.ExceptHandler) and n.name=='primary' and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='actions' for t in x.targets) for x in n.body))
 f=ast.parse('def selected():\n try:raise sentinel\n except BaseException as primary:pass').body[0];f.body[0].handlers[0].body=h.body
 return compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),'<actual-producer-handler>','exec')
class Cleanup(unittest.TestCase):
 def run_case(self,fatal=False,close_fails=False):
  owner=SimpleNamespace(poisoned=False,identity='a'*64);calls=[];primary=MemoryError('first') if fatal else ValueError('expected mutation')
  def fail(reason):
   calls.append('fail');self.assertFalse(owner.poisoned,'actual lease would refuse before failed terminal')
  def close():
   calls.append('close')
   if close_fails:raise OSError('close uncertain')
  class Uncertain(BaseException):pass
  def cleanup(actions,primary):
   errors=[]
   for action in actions:
    try:action()
    except BaseException as e:errors.append(e)
   if errors and not isinstance(primary,MemoryError):raise Uncertain() from primary
  env={'owner':owner,'stream':None,'log':SimpleNamespace(closed=False,fail=fail,close=close),'claimed':True,'fd':10,'sentinel':primary,'io':SimpleNamespace(_cleanup=cleanup,_write=lambda *a:calls.append('marker'),_json=lambda x:x)}
  exec(handler(),env)
  with self.assertRaises(BaseException) as got:env['selected']()
  self.assertTrue(owner.poisoned);self.assertEqual(calls,['fail','close','marker'])
  if fatal or not close_fails:self.assertIs(got.exception,primary)
  else:self.assertIsInstance(got.exception,Uncertain)
 def test_terminal_before_poison(self):self.run_case()
 def test_fatal_identity_and_all_closes(self):self.run_case(True,True)
 def test_uncertain_close_still_poisoned(self):self.run_case(False,True)
if __name__=='__main__':unittest.main()
