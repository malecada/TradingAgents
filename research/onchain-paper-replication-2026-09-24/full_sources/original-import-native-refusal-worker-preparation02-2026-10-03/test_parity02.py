"""Whole-source inverse-patch parity and compact failure-marker policy."""
import ast,pathlib,unittest
D=pathlib.Path(__file__).resolve().parent;OLD=D.parent/'original-import-native-refusal-worker-preparation01-2026-10-03'
class Tests(unittest.TestCase):
 def test_unchanged_worker_parser_preclaim_and_templates(self):
  for name in ('resource_refusal.py','refusal_preclaim01.py','refusal_native01.py','refusal_oracle_evidence01.py','templates01.py'):self.assertEqual((D/name).read_bytes(),(OLD/name).read_bytes())
 def test_inverse_move_equals_full_predecessor_module_ast(self):
  tree=ast.parse((D/'refusal_outer01.py').read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');guard=next(n for n in run.body if isinstance(n,ast.Try) and any(isinstance(v,ast.For) and 'signal_handlers.items' in ast.unparse(v) for v in n.finalbody));marker=guard.finalbody.pop();self.assertEqual(ast.unparse(marker.test),'primary is not None');self.assertEqual(len(marker.body),1);self.assertIsInstance(marker.body[0],ast.Try)
  post=guard.finalbody[-2];self.assertIsInstance(post,ast.Try);self.assertIn('publish_post_tail',ast.unparse(post));post.handlers[0].body.extend(marker.body)
  self.assertEqual(ast.dump(tree),ast.dump(ast.parse((OLD/'refusal_outer01.py').read_text())))
if __name__=='__main__':unittest.main(verbosity=2)
