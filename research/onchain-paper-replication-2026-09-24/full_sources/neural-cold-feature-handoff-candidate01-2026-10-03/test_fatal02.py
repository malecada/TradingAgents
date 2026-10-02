import ast
import pathlib
import types
import unittest
HERE=pathlib.Path(__file__).resolve().parent
class Fatal(unittest.TestCase):
 def test_first_fatal_identity(self):
  tree=ast.parse((HERE/'cold_files.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('fatal','preserve')]
  self.assertEqual(len(nodes),2,'first-fatal reducer absent')
  ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual cold_files reducers','exec'),ns)
  first=MemoryError('original');later=KeyboardInterrupt();ordinary=ValueError('initial')
  self.assertIs(ns['preserve'](first,later),first);self.assertIs(ns['preserve'](ordinary,later),later)
  self.assertIs(ns['preserve'](ordinary,None),ordinary)
 def test_full_check_does_not_reenter_same_authority_lock(self):
  t=ast.parse((HERE/'compact_cold_features.py').read_text());c=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Authority');f=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='check')
  calls=[n for n in ast.walk(f) if isinstance(n,ast.Call) and ast.unparse(n.func)=='compact_stage.verify']
  self.assertEqual(len(calls),1)
  self.assertNotEqual(ast.unparse(next(k.value for k in calls[0].keywords if k.arg=='lease')),'self.lease','full verification recursively acquires the same lock')
 def test_failure_marker_does_not_swallow_fatal(self):
  t=ast.parse((HERE/'compact_cold_features.py').read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
  self.assertFalse(any(isinstance(n,ast.ExceptHandler) and isinstance(n.type,ast.Name) and n.type.id=='BaseException' and len(n.body)==1 and isinstance(n.body[0],ast.Pass) for n in ast.walk(f)),'marker first fatal can be discarded')
if __name__=='__main__':unittest.main(verbosity=2)
