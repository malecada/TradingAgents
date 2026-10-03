import ast,copy,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'neural-cold-feature-handoff-comparison-outcome01-2026-10-03'
a=(OUT/'recover_comparison_outcome03.py').read_text();b=(OUT/'recover_comparison_outcome04.py').read_text()
expected=a.replace("'recover_comparison_outcome03.py', 'recover_comparison_outcome02.py'","'recover_comparison_outcome04.py', 'recover_comparison_outcome03.py', 'recover_comparison_outcome02.py'").replace("'RECOVERY_SOURCE_ADAPTATION03.json', 'RECOVERY_FAILURE01.json'","'RECOVERY_SOURCE_ADAPTATION04.json', 'RECOVERY_SOURCE_ADAPTATION03.json', 'RECOVERY_FAILURE01.json'").replace("('neural-cold-feature-handoff-comparison-outcome-recovery-source-review02-2026-10-03', 'MANIFEST01.json')","('neural-cold-feature-handoff-comparison-outcome-recovery-source-review02-2026-10-03', 'MANIFEST02.json')")
assert expected==b
old=ast.parse((OUT/'recover_comparison_outcome02.py').read_text());new=ast.parse(a)
def selection_removed(tree):
 start=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='names' for x in n.targets));end=next(i for i,n in enumerate(tree.body[start:],start) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='selected' for x in n.targets));tree.body[start:end]=[];return tree
old=selection_removed(old);new=selection_removed(new)
new.body=[n for n in new.body if not (isinstance(n,ast.For) and ast.unparse(n.iter)=="retained['members']")]
class Undo(ast.NodeTransformer):
 def visit_Constant(self,n):
  if n.value=='outcome-recovery02':n.value='outcome-recovery01'
  if n.value=='REMOTE_OUTCOME_RECOVERY02.json':n.value='REMOTE_OUTCOME_RECOVERY01.json'
  return n
 def visit_Assert(self,n):
  if ast.unparse(n.test)=='member.isdir() and member.size == 0':return ast.parse("assert member.isdir() and member.size == row['bytes'] == 0").body[0]
  return self.generic_visit(n)
new=Undo().visit(new)
assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)
print('PASS whole03→04 byte inverse: only self/adaptation selection and review02 manifest correction.')
print('PASS whole02→03 AST inverse outside explicit selected metadata, typed member validation, directory extent correction and fresh recovery/output identities.')
