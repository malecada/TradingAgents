"""Stdlib-only source and indexing-contract fixtures; not NumPy qualification."""
from pathlib import Path
import ast,types,copy,unittest
P=Path(__file__).resolve().parent
class Array:
 def __init__(self,rows=None,writable=False,indices=None):self.rows=rows;self.indices=indices;self.flags=types.SimpleNamespace(writeable=writable);self.calls=[]
 def __getitem__(self,key):
  row,indices=key;self.calls.append(row)
  if isinstance(row,slice):return tuple([r[k] for k in indices.indices] for r in self.rows)
  return [self.rows[row][k] for k in indices.indices]
class Checks(unittest.TestCase):
 def branch(self):
  t=ast.parse((P/'matching_annealing.py').read_text())
  return next(n for n in ast.walk(t) if isinstance(n,ast.If) and 'not a.edge_index.flags.writeable' in ast.unparse(n.test))
 def test_exact_default_fallback_and_full_ast_inverse(self):
  before=ast.parse((P/'BASELINE_matching_annealing.py').read_text());after=ast.parse((P/'matching_annealing.py').read_text());branch=self.branch();target=ast.dump(branch)
  class Restore(ast.NodeTransformer):
   def visit_If(self,node):
    if ast.dump(node)==target:return node.orelse
    return self.generic_visit(node)
  after=Restore().visit(after);self.assertEqual(ast.dump(before),ast.dump(after))
 def test_rows_equal_columns_and_mutable_subclass_fallback(self):
  branch=self.branch();execbody=compile(ast.Module(body=[branch],type_ignores=[]),'geometry','exec')
  class Sub(Array):pass
  for cls,writable,fast in ((Array,False,True),(Array,True,False),(Sub,False,False)):
   a=Array([[0,1,2],[2,0,1]]);b=cls([[3,4,5],[4,5,3]],writable=writable);left=Array(indices=[2,0,2]);right=Array(indices=[1,2,0]);ns=dict(a=types.SimpleNamespace(edge_index=a),b=types.SimpleNamespace(edge_index=b),left=left,right=right,np=types.SimpleNamespace(ndarray=Array))
   exec(execbody,ns);self.assertEqual(tuple(ns[k] for k in ('u','v','i','j')),([2,0,2],[1,2,1],[4,5,3],[5,3,4]))
   self.assertEqual(len(a.calls),2 if fast else 1);self.assertEqual(len(b.calls),2 if fast else 1)
if __name__=='__main__':unittest.main(verbosity=2)
