"""AST route specialization; source proof only, not real policy execution."""
import ast
import copy
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent
old=ast.parse((HERE/'resources.baseline02.py').read_text());new=ast.parse((HERE/'resources.py').read_text())
def dump(node):return ast.dump(node,include_attributes=False)
def funcs(tree):return {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
class Legacy(ast.NodeTransformer):
 def truth(self,node):
  if isinstance(node,ast.Compare) and isinstance(node.left,ast.Name) and node.left.id=='native_unit_limits' and len(node.ops)==1 and isinstance(node.comparators[0],ast.Constant) and node.comparators[0].value is None:
   if isinstance(node.ops[0],ast.Is):return True
   if isinstance(node.ops[0],ast.IsNot):return False
  if isinstance(node,ast.BoolOp):
   values=[self.truth(x) for x in node.values]
   if isinstance(node.op,ast.And) and False in values:return False
   if isinstance(node.op,ast.Or) and True in values:return True
  return None
 def visit_If(self,node):
  node=self.generic_visit(node);v=self.truth(node.test)
  return node.body if v is True else node.orelse if v is False else node
class Parity(unittest.TestCase):
 def test_none_and_physical_guard_control_ast_identical(self):
  a=Legacy().visit(copy.deepcopy(funcs(old)['guarded_run']));b=Legacy().visit(copy.deepcopy(funcs(new)['guarded_run']))
  self.assertEqual(dump(a),dump(b))
 def test_all_existing_other_functions_identical(self):
  a=funcs(old);b=funcs(new)
  for name in a.keys()-{'guarded_run'}:
   with self.subTest(function=name):self.assertEqual(dump(a[name]),dump(b[name]))
 def test_native_systemd_properties_and_worker_ready_unchanged(self):
  def launch(tree):
   run=funcs(tree)['guarded_run']
   return [dump(n) for n in ast.walk(run) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='args' for t in n.targets)]
  self.assertEqual(launch(old),launch(new));self.assertEqual(dump(funcs(old)['_native_ready']),dump(funcs(new)['_native_ready']))
if __name__=='__main__':unittest.main(verbosity=2)
