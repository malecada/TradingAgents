"""Prospective pure-policy tests; never a genuine transport run."""
import ast,json,pathlib,unittest
P=pathlib.Path(__file__).parent
class Tests(unittest.TestCase):
 def test_concrete_engine_exists(self):self.assertTrue((P/'selected_non_tail_transport.py').exists())
 def test_selected_dispatch_exists(self):
  tree=ast.parse((P/'archive_non_tail.py').read_text());op=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Operation');dispatch=next(n for n in op.body if isinstance(n,ast.FunctionDef) and n.name=='dispatch');self.assertIn('selected_non_tail_transport',ast.unparse(dispatch))
if __name__=='__main__':unittest.main(verbosity=2)
