"""Actual constructor scalar AST + source-only generator/oracle contract."""
import ast,os,sys,unittest,json,importlib.util,hashlib
from pathlib import Path
from types import SimpleNamespace
D=Path(__file__).resolve().parent;F=D.parent
OLD=F/'original-import-native-refusal-candidate04-2026-10-03'
SOURCE=F/'original-import-fixture-io-candidate02-2026-10-02/array_neighborhoods.py'
def formula(n,chunk):
 tree=ast.parse(SOURCE.read_text());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='ArrayNeighborhoodIndex');fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='__init__');start=next(i for i,x in enumerate(fn.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='buffer_allowance' for t in x.targets));scope=dict(self=SimpleNamespace(),n=n,e=n,node_width=32,edge_width=16,edge_chunk=chunk,max_buffer_bytes=1048576)
 exec(compile(ast.Module(body=fn.body[start:start+2],type_ignores=[]),str(SOURCE),'exec'),scope);return scope['self'].buffer_allowance
class Checks(unittest.TestCase):
 def test_selected_oracle_constructor_allowance(self):
  path=Path(os.environ.get('ORACLE_SOURCE',str(D/'guarded_formula_oracle05.py')));tree=ast.parse(path.read_text());call=next(x for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='ArrayNeighborhoodIndex');chunk=next(x.value.value for x in call.keywords if x.arg=='edge_chunk');self.assertEqual(formula(2,chunk),655600)
 def test_actual_old_refusal_and_new_bounds(self):
  for n,want in [(2,655600),(3,655692)]:
   with self.assertRaisesRegex(ValueError,'buffer allowance exceeded'):formula(n,65536)
   self.assertEqual(formula(n,4096),want)
 def test_oracle_loop_parity(self):
  a=ast.parse((OLD/'guarded_formula_oracle04.py').read_text());b=ast.parse((D/'guarded_formula_oracle05.py').read_text());get=lambda t:next(x for x in ast.walk(t) if isinstance(x,ast.With));x=get(a);y=get(b);self.assertEqual(ast.dump(ast.Module(body=x.body,type_ignores=[])),ast.dump(ast.Module(body=y.body,type_ignores=[])))
if __name__=='__main__':
 result=unittest.main(exit=False);assert not any(n.split('.')[0] in ('numpy','scipy','torch','tradingagents') for n in sys.modules);sys.exit(not result.result.wasSuccessful())
