"""Exact current method, stdlib stubs, no NumPy import."""
import ast,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Current(unittest.TestCase):
 def test_legacy_policy_mutation_refuses_before_new_parse(self):
  tree=ast.parse((P/'matching_numeric_policy.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='current')
  np=object();calls=[];ns={'kernel':types.SimpleNamespace(np=np),'CACHE_POLICY':{'format':'bounded-numpy-agreement-c05-v2'},'_cache_current':lambda x:calls.append(x)}
  exec(compile(ast.Module(body=[method],type_ignores=[]),'current','exec'),ns)
  original=(('format','bounded-numpy-agreement-c05-v1'),)
  for mutation in ((('format','bounded-numpy-agreement-c05-v2'),),object()):
   adapter=types.SimpleNamespace(policy=mutation,_pin=original,_numpy=np)
   with self.assertRaisesRegex(ValueError,'numeric adapter changed'):ns['current'](adapter)
  self.assertEqual(calls,[])
if __name__=='__main__':unittest.main(verbosity=2)
