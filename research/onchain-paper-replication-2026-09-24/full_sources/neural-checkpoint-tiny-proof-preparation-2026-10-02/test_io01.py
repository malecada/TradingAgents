"""Stdlib only: load definitions via AST, not the deferred numerical program."""
import ast,json,os,pathlib,re,stat,sys,unittest
HERE=pathlib.Path(__file__).resolve().parent
class IO(unittest.TestCase):
 def helpers(self):
  tree=ast.parse((HERE/'oracle01.py').read_bytes());names={'require','close_once','write_new','sha','encoded'}
  ns={'os':os,'re':re,'stat':stat,'sys':sys,'json':json,'P':json.loads((HERE/'protocol01.json').read_bytes())}
  exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names],type_ignores=[]),'<candidate-io>','exec'),ns);return ns
 def test_exclusive_regular_write_and_limit(self):
  ns=self.helpers();root=HERE/'io-fixture01';root.mkdir()
  ns['write_new'](root,'one.json',b'{}\n');self.assertEqual((root/'one.json').read_bytes(),b'{}\n')
  with self.assertRaises(FileExistsError):ns['write_new'](root,'one.json',b'changed')
  with self.assertRaises(RuntimeError):ns['write_new'](root,'../outside',b'x')
  with self.assertRaises(RuntimeError):ns['write_new'](root,'oversize',b'x'*(ns['P']['max_metadata_bytes']+1))
  self.assertEqual(sorted(p.name for p in root.iterdir()),['one.json'])
 def test_first_fatal_preserved_and_closes_once(self):
  ns=self.helpers();first=KeyboardInterrupt('original');calls=[]
  def a():calls.append('a');raise OSError('cleanup')
  def b():calls.append('b');raise MemoryError('second fatal')
  ns['close_once']((a,b),first);self.assertEqual(calls,['a','b']);self.assertEqual(len(first.__notes__),2)
 def test_marker_bound_and_coordinator_defers_cleanup(self):
  protocol=json.loads((HERE/'protocol01.json').read_bytes())
  # 14 phases per correctness arm, 5 comparisons, import+complete.
  self.assertLessEqual(2*len(protocol['cases'])*14+len(protocol['cases'])+2,protocol['max_phase_markers'])
  tree=ast.parse((HERE/'coordinator01.py').read_bytes());source=ast.unparse(tree)
  self.assertIn('active.wait()',source);self.assertIn('returncode=code',source);self.assertIn('outer-native-guard',source)
  self.assertNotIn('torch',source);self.assertNotIn('numpy',source)
if __name__=='__main__':unittest.main(verbosity=2)
