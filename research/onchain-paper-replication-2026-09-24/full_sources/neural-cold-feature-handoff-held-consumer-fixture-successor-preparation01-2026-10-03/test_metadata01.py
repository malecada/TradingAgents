import ast,hashlib,json,runpy,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
B=runpy.run_path(str(P/'capsule_builder01.py'));G=runpy.run_path(str(P/'generate_inputs01.py'))
class Tests(unittest.TestCase):
 def test_explicit_199_layout(self):
  self.assertEqual(B['HELD_COUNTS'],(199,148))
 def test_generation_refuses(self):
  with self.assertRaisesRegex(ValueError,'guarded'):G['generate_held_arrays']()
 def test_unknown_roles(self):
  with self.assertRaises(ValueError):G['held_input_plan']({'bad':{}},None)
 def test_old_functions_AST_unchanged(self):
  for name in ('capsule_builder01.py','generate_inputs01.py','build_release_draft01.py'):
   old=ast.parse((P/(name+'.baseline')).read_bytes());new=ast.parse((P/name).read_bytes())
   for node in old.body:
    if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
     current=next(x for x in new.body if type(x)is type(node) and x.name==node.name);self.assertEqual(ast.dump(current),ast.dump(node))
if __name__=='__main__':unittest.main(verbosity=2)
