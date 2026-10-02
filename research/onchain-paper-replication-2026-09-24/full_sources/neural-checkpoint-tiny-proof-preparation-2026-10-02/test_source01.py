"""Pure source/protocol checks only. Never import the numerical oracle."""
import ast,json,pathlib,unittest
HERE=pathlib.Path(__file__).resolve().parent
class Source(unittest.TestCase):
 def tree(self):
  p=HERE/'oracle01.py';self.assertTrue(p.exists(),'finite actual-model oracle missing');return ast.parse(p.read_bytes())
 def test_frozen_tolerances_cases_and_modes(self):
  p=json.loads((HERE/'protocol01.json').read_bytes());self.assertEqual((p['rtol'],p['atol']),(1e-5,1e-6))
  self.assertEqual(p['modes'],['correctness','profile_false','profile_true']);self.assertEqual(len(p['cases']),5)
  self.assertEqual({c['graphs'] for c in p['cases']},{2,28});self.assertEqual(p['bounds']['memory_max_bytes'],2**30)
  self.tree()
 def test_no_top_level_numerical_import_or_execution(self):
  t=self.tree()
  for node in t.body:
   if isinstance(node,ast.Import):self.assertFalse(any(x.name.split('.')[0] in ('torch','numpy') for x in node.names))
   if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').startswith(('torch','numpy','tradingagents')))
  imports=[n.module for n in ast.walk(t) if isinstance(n,ast.ImportFrom)]
  self.assertIn('tradingagents.research.onchain_replication.model',imports)
  self.assertIn('tradingagents.research.onchain_replication.checkpoints',imports)
 def test_all_modes_and_measurement_separation(self):
  t=self.tree();functions={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
  for name in ('run_correctness','run_profile','arm','compare','fixture','main'):self.assertIn(name,functions)
  profile=ast.unparse(functions['run_profile']);self.assertNotIn('saved_tensors_hooks',profile);self.assertNotIn('register_forward',profile)
  self.assertIn('saved_tensors_hooks',ast.unparse(functions['arm']))
 def test_actual_training_checkpoint_and_exact_continuation_calls(self):
  text=ast.unparse(self.tree())
  for token in ('save_checkpoint','load_checkpoint','parameter_groups','capture_rng','restore_rng','backward','optimizer.step','same_arm_continuation','torch.testing.assert_close'):
   self.assertIn(token,text)
 def test_limits_and_exclusive_no_pytest_path(self):
  text=ast.unparse(self.tree());self.assertIn('os.O_EXCL',text);self.assertIn('os.O_NOFOLLOW',text)
  self.assertNotIn('pytest.main',text);self.assertNotIn('unlink(',text);self.assertNotIn('rmtree(',text)
  self.assertIn('max_phase_markers',text);self.assertIn('max_saved_records',text);self.assertIn('max_phase_samples',text)
if __name__=='__main__':unittest.main(verbosity=2)
