"""Pure selected-policy parsing and arithmetic; no numeric imports."""
from pathlib import Path
from types import MappingProxyType
import ast,unittest
P=Path(__file__).resolve().parent
class Reservation(unittest.TestCase):
 def test_exact_charge_and_types(self):
  tree=ast.parse((P/'matching_numeric_policy.py').read_text());nodes=[]
  for n in tree.body:
   if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('POLICY','CACHE_POLICY') for t in n.targets):nodes.append(n)
   if isinstance(n,ast.FunctionDef) and n.name in ('freeze','cache_reservation'):nodes.append(n)
  ns={'MappingProxyType':MappingProxyType};exec(compile(ast.Module(body=nodes,type_ignores=[]),'policy','exec'),ns)
  f=ns['cache_reservation'];self.assertEqual(f(None),0);self.assertEqual(f(dict(ns['POLICY'])),0);self.assertEqual(f(dict(ns['CACHE_POLICY'])),33619968)
  self.assertEqual(751331316+f(dict(ns['CACHE_POLICY'])),784951284)
  for change in ({'max_cache_scratch_bytes':65536.0},{'max_cache_retained_bytes':33554433},{'rtol':1e-5}):
   with self.assertRaises(ValueError):f(dict(ns['CACHE_POLICY'])|change)
if __name__=='__main__':unittest.main(verbosity=2)
