"""Static route coverage, not actual admission."""
import ast
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent
class Route(unittest.TestCase):
 def test_unselected_cold_policy_is_not_silently_ignored(self):
  tree=ast.parse((HERE/'job_payload.py').read_text());guards=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.If) and 'compact_cold_handoff_input' in ast.unparse(n.test) and any(isinstance(x,ast.Raise) for x in n.body):guards.append(n)
  self.assertEqual(len(guards),2,'job and planned unselected cold policies need explicit refusal')
if __name__=='__main__':unittest.main(verbosity=2)
