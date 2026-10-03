"""Actual new __exit__ only; module doubles test exception reduction, not authority."""
import ast,sys,types,threading,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).parent
src=ast.parse((P/'held_score_consumer.py').read_bytes());cls=next(x for x in src.body if isinstance(x,ast.ClassDef) and x.name=='_RawWorker')
cls.body=[x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='__exit__']
dep=ast.parse((P.parent/'batch-output-produced-f32-adapter-preparation02-2026-10-03/archive_non_tail.py').read_bytes())
# Same original select/fatal classification, with actual canonical cleanup type.
io=ast.parse((P.parent/'batch-output-exact-member-reader-candidate02-2026-10-03/owned_io.py').read_bytes());io_ns={};exec(compile(ast.Module([x for x in io.body if isinstance(x,ast.ClassDef) and x.name=='CleanupFailure'],[]),'owned_io','exec'),io_ns)
ns={'__package__':'qualified','threading':threading,'_LOCK':threading.RLock(),'require':lambda b,m:None if b else (_ for _ in ()).throw(ValueError(m))}
dn={'CleanupFailure':io_ns['CleanupFailure']};exec(compile(ast.Module([x for x in dep.body if isinstance(x,ast.FunctionDef) and x.name in ('fatal','select')],[]),'durable','exec'),dn)
exec(compile(ast.Module([cls],[]),'actual_RawWorker_exit','exec'),ns)
class Test(unittest.TestCase):
 def exercise(self,primary,later):
  calls=[]
  def close(*args):calls.append(args);raise later
  w=ns['_RawWorker']();w.thread=threading.get_ident();w.cm=types.SimpleNamespace(__exit__=close);ns['_WORKER']=w
  pkg=types.ModuleType('qualified');pkg.archive_non_tail=types.SimpleNamespace(select=dn['select'])
  with patch.dict(sys.modules,{'qualified':pkg}):
   try:w.__exit__(type(primary),primary,None)
   except BaseException as got:result=got
  self.assertEqual(len(calls),1);self.assertIsNone(ns['_WORKER']);return result
 def test_prior_fatal(self):
  for later in (OSError('close'),SystemExit('later')):
   first=MemoryError('first');self.assertIs(self.exercise(first,later),first)
 def test_later_fatal(self):
  later=KeyboardInterrupt();self.assertIs(self.exercise(ValueError('ordinary'),later),later)
if __name__=='__main__':unittest.main()
