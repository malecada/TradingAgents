import ast,hashlib,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent

def tree(name,old=False):return ast.parse((HERE/('baseline' if old else '.')/name).read_text())
def funcs(t):return {n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
def digest(node):return hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()
class StripClose(ast.NodeTransformer):
 def visit_Call(self,node):
  node=self.generic_visit(node)
  if isinstance(node.func,ast.Name) and node.func.id=='_closing':return node.args[0]
  return node

class NumericalParity(unittest.TestCase):
 def test_every_non_io_engine_function_identical(self):
  excluded={'matching_checkpoint.py':{'save','load'},'matching_annealing.py':{'sha','sync','save','load'},'matching_hardening.py':{'sha','sync','close','save','load'}}
  self.rows=[]
  for name,skip in excluded.items():
   old=funcs(tree(name,True));new=funcs(tree(name));self.assertEqual(set(old),set(new))
   for key in sorted(set(old)-skip):
    self.assertEqual(digest(old[key]),digest(new[key]),name+':'+key);self.rows.append(name+':'+key)
  self.assertGreaterEqual(len(self.rows),20)
 def test_kernel_bytes_identical(self):
  self.assertEqual((HERE/'imported_kernel.py').read_bytes(),(HERE/'baseline/imported_kernel.py').read_bytes())
 def test_neighborhood_extraction_and_constructor_numerics_identical(self):
  before=next(n for n in tree('array_neighborhoods.py',True).body if isinstance(n,ast.ClassDef));after=next(n for n in tree('array_neighborhoods.py').body if isinstance(n,ast.ClassDef))
  old={n.name:n for n in before.body if isinstance(n,ast.FunctionDef)};new={n.name:n for n in after.body if isinstance(n,ast.FunctionDef)}
  for key in ('_blocks','_select','_induced_blocks','_neighborhood'):
   self.assertEqual(digest(old[key]),digest(new[key]),key)
  for key in ('__init__','selected','neighborhood'):
   a=next(n for n in old[key].body if isinstance(n,ast.Try));b=next(n for n in new[key].body if isinstance(n,ast.Try))
   self.assertEqual(digest(ast.Module(body=a.body,type_ignores=[])),digest(ast.Module(body=b.body,type_ignores=[])),key)
 def test_resident_graph_numeric_load_save_only_context_cleanup_changed(self):
  for key in ('_resident_array','save_graph'):
   a=funcs(tree('graph_store.py',True))[key];b=StripClose().visit(funcs(tree('graph_store.py'))[key])
   self.assertEqual(digest(a),digest(b),key)
 def test_early_helper_import_is_stdlib_only(self):
  allowed={'os','sys','contextlib'}
  imports=[n for n in tree('owned_io.py').body if isinstance(n,(ast.Import,ast.ImportFrom))]
  for node in imports:
   names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module]
   self.assertTrue(set(names)<=allowed)

if __name__=='__main__':unittest.main()
