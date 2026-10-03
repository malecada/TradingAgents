"""Independent source/metadata review only; no package or numerical imports."""
import ast,hashlib,json,pathlib,types,unittest
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3]
def require(v,m):
 if not v:raise ValueError(m)
class Checks(unittest.TestCase):
 def test_frozen_bodies_and_inventory(self):
  manifest=json.loads((D/'MANIFEST01.json').read_text())
  for row in manifest['files']:
   raw=(ROOT/row['path']).read_bytes();self.assertEqual(len(raw),row['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
  inv=json.loads((D/'source_inventory01.json').read_text());rows=inv['source_inventory'];self.assertEqual(len(rows),169);self.assertEqual(len({r['target'] for r in rows}),169)
  self.assertEqual(sum(r['target'].startswith('tradingagents/') for r in rows),144)
  for row in rows:
   raw=(ROOT/row['origin']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
   if row['target'].endswith('.py'):ast.parse(raw)
 def test_hook_only_and_mathematical_mutation_parity(self):
  old=ast.parse((D.parent/'original-import-native-refusal-candidate02-2026-10-03/resource_refusal.py').read_text());new=ast.parse((D/'resource_refusal.py').read_text())
  oldfn={x.name:x for x in old.body if isinstance(x,ast.FunctionDef)};newfn={x.name:x for x in new.body if isinstance(x,ast.FunctionDef)}
  for name in oldfn.keys()-{'execute'}:self.assertEqual(ast.dump(oldfn[name]),ast.dump(newfn[name]))
  a=next(x for x in ast.walk(oldfn['execute']) if isinstance(x,ast.If) and ast.unparse(x.test)=="case == 'matching-swap'")
  b=next(x for x in ast.walk(newfn['execute']) if isinstance(x,ast.If) and ast.unparse(x.test)=="case == 'matching-swap'")
  self.assertEqual(ast.dump(a),ast.dump(b))
 def test_selected_first_fatal_reducer(self):
  tree=ast.parse((D/'refusal_outer01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='select');ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual select','exec'),ns)
  class CleanupFailure(BaseException):pass
  fatal=MemoryError('first');cleanup=CleanupFailure('cleanup');ordinary=ValueError('ordinary')
  self.assertIs(ns['select'](fatal,cleanup,CleanupFailure),fatal);self.assertIs(ns['select'](cleanup,fatal,CleanupFailure),fatal);self.assertIs(ns['select'](ordinary,cleanup,CleanupFailure),cleanup)
 def test_counterexample_late_restore_leaves_passed_terminal(self):
  tree=ast.parse((D/'refusal_outer01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');guard=next(n for n in fn.body if isinstance(n,ast.Try) and any(isinstance(v,ast.For) and 'signal_handlers.items' in ast.unparse(v) for v in n.finalbody))
  restore=guard.finalbody[-1];self.assertIsInstance(restore,ast.For);self.assertIn('signal_handlers.items()',ast.unparse(restore))
  error=OSError('synthetic signal restoration failed');writes={'terminal.json':{'status':'passed'},'post-tail-storage.json':{'fixture':'previous completed observation'}};captured=[]
  def fail(*args):raise error
  ns={'signal_handlers':{2:None},'signal':types.SimpleNamespace(signal=fail),'retain':captured.append,'save':lambda n,v:writes.update({n:v})}
  exec(compile(ast.Module(body=[restore],type_ignores=[]),'actual signal restoration tail','exec'),ns)
  self.assertEqual(captured,[error]);self.assertEqual(writes['terminal.json']['status'],'passed');self.assertNotIn('post-terminal-failure.json',writes)
  self.assertTrue(isinstance(fn.body[-2],ast.If));self.assertIn('raise primary',ast.unparse(fn.body[-2]))
  print('REPRODUCED: actual after-claim tail selects restoration error and raises, but leaves passed terminal without additive failure marker. Tiny source fixture, no native job.')
if __name__=='__main__':unittest.main(verbosity=2)
