"""Prove numerical body parity after removing only four declared fixture hooks."""
import ast,copy,unittest
from pathlib import Path
D=Path(__file__).parent
class Strip(ast.NodeTransformer):
 def visit_ImportFrom(self,node):
  if node.module is None and [a.name for a in node.names]==['resource_refusal']:return None
  return node
 def visit_Assign(self,node):
  if any(isinstance(t,ast.Name) and t.id=='selected_compute' for t in node.targets):return None
  if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=='resource_refusal' and node.value.func.attr=='returned':return None
  return self.generic_visit(node)
 def visit_keyword(self,node):
  if node.arg=='compute' and isinstance(node.value,ast.Name) and node.value.id=='selected_compute':node.value=ast.Name(id='matcher',ctx=ast.Load())
  if node.arg=='score_pair' and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='score_callback':node.value=ast.Name(id='stream',ctx=ast.Load())
  return self.generic_visit(node)
class Parity(unittest.TestCase):
 def test_numerical_source_exact_outside_declared_hooks(self):
  old=ast.parse((D/'compact_mcm.baseline.py').read_text());new=ast.parse((D/'compact_mcm.py').read_text());new=Strip().visit(new)
  self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(new,include_attributes=False))
 def test_genuine_worker_dispatch_only_and_no_fake_constructor(self):
  tree=ast.parse((D/'resource_refusal.py').read_text());calls=[n.func for n in ast.walk(tree) if isinstance(n,ast.Call)]
  self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr in ('Binding','Produced','Owner','ResearchRun') for n in calls))
  for required in ('open_first','prepare','attach','ImportedExecution','Target','produce_imported'):
   self.assertTrue(any(isinstance(n,ast.Attribute) and n.attr==required or isinstance(n,ast.Name) and n.id==required for n in calls),required)
if __name__=='__main__':unittest.main()
