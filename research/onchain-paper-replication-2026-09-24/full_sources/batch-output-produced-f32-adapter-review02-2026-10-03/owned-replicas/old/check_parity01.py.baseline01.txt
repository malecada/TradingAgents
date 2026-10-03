import ast,unittest
from pathlib import Path
P=Path(__file__).parent
def definitions(tree):
 result={}
 for node in tree.body:
  if isinstance(node,ast.FunctionDef):result[node.name]=node
  elif isinstance(node,ast.ClassDef):
   for child in node.body:
    if isinstance(child,ast.FunctionDef):result[node.name+'.'+child.name]=child
 return result
class Parity(unittest.TestCase):
 def test_unchanged_methods(self):
  allowed={'archive_non_tail.py':{'validate_policy','Context.__init__','Context.check','Context.close','Ledger.__init__','Operation.verify_local_recovery','Operation.dispatch'},'selected_non_tail_transport.py':{'policy','_selected','Session.__init__','Session.run'}}
  for name,changed in allowed.items():
   old=definitions(ast.parse((P/(name+'.baseline.txt')).read_text()));new=definitions(ast.parse((P/name).read_text()))
   self.assertEqual(set(old),set(new))
   for k in old:
    if k not in changed:self.assertEqual(ast.dump(old[k]),ast.dump(new[k]),name+':'+k)
 def test_default_policy_tail(self):
  for name,n in [('archive_non_tail.py','validate_policy'),('selected_non_tail_transport.py','policy')]:
   old=definitions(ast.parse((P/(name+'.baseline.txt')).read_text()))[n];new=definitions(ast.parse((P/name).read_text()))[n]
   new.body=new.body[(1 if name=='archive_non_tail.py' else 2):]
   self.assertEqual(ast.dump(old),ast.dump(new))
 def test_all_candidate_syntax(self):
  for name in ('compact_mcm.py','archive_non_tail.py','selected_non_tail_transport.py','completed_f32.py'):ast.parse((P/name).read_text())
if __name__=='__main__':unittest.main()
