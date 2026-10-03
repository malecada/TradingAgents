"""Source seams and tiny receipt checks, never fake Binding/Owner execution."""
import ast,os,sys,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_oracle_precedes_mutation_in_actual_execute(self):
  p=Path(os.environ.get('WORKER_SOURCE',D/'resource_refusal.py'));tree=ast.parse(p.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute');calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='genuine_oracle'];self.assertEqual(len(calls),1)
  birth=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Target');mutations=[n for n in ast.walk(fn) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and ast.unparse(n.test)=="case == 'matching-swap'"];self.assertLess(birth.lineno,calls[0].lineno);self.assertLess(calls[0].lineno,mutations[0].lineno)
if __name__=='__main__':unittest.main()
