import ast,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('root_generator03',HERE/'generate04.py');M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)
RAW=(HERE.parent/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03/source-bodies/tradingagents/research/onchain_replication/resources.py').read_bytes()
class Native(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='cold-native-source-only-');self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
  self.target='tradingagents/research/onchain_replication/resources.py';p=self.root/self.target;p.parent.mkdir(parents=True);p.write_bytes(RAW);self.sources={self.target:hashlib.sha256(RAW).hexdigest()}
  f=next(n for n in ast.parse(RAW).body if isinstance(n,ast.FunctionDef) and n.name=='_native_owned_env');ns={'Path':Path};exec(compile(ast.Module(body=[f],type_ignores=[]),'selected-helper','exec'),ns);self.native=ns['_native_owned_env'](self.root)
 def request(self,value):
  p=self.root/'native.json';p.write_text(json.dumps(value));return {'native_environment':{'path':'native.json','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}}
 def test_distinct_real_native_map_passes_and_inventory_fails(self):
  self.assertEqual(M.native_environment(self.root,self.request(self.native),self.sources),self.native)
  with self.assertRaisesRegex(ValueError,'native shell environment'):M.native_environment(self.root,self.request({'inventory':{'python':'3.13.13'}}),self.sources)
 def test_changed_or_missing_native_reference_refuses(self):
  req=self.request(self.native);(self.root/'native.json').write_text('{}')
  with self.assertRaisesRegex(ValueError,'reference hash'):M.native_environment(self.root,req,self.sources)
  with self.assertRaises(KeyError):M.native_environment(self.root,{},self.sources)
 def test_changed_selected_helper_source_refuses(self):
  req=self.request(self.native);(self.root/self.target).write_bytes(RAW+b'\n# altered\n')
  with self.assertRaisesRegex(ValueError,'selected native helper'):M.native_environment(self.root,req,self.sources)
 def test_gate_routes_distinct_native_reference(self):
  tree=ast.parse((HERE/'generate04.py').read_bytes());render=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='render')
  pairs=[(k,v) for d in ast.walk(render) if isinstance(d,ast.Dict) for k,v in zip(d.keys,d.values) if isinstance(k,ast.Constant) and k.value=='native_environment']
  self.assertEqual(len(pairs),1);self.assertEqual(ast.unparse(pairs[0][1]),"request['native_environment']")
 def test_comparison_and_other_module_AST_unchanged(self):
  base=ast.parse((HERE.parent/'neural-cold-feature-handoff-engineering-registration-preparation03-2026-10-03/generate02.baseline.py').read_bytes());after=ast.parse((HERE/'generate04.py').read_bytes())
  before={n.name:ast.dump(n) for n in base.body if isinstance(n,ast.FunctionDef)};updated={n.name:ast.dump(n) for n in after.body if isinstance(n,ast.FunctionDef)}
  self.assertEqual(set(updated)-set(before),{'native_environment'})
  self.assertEqual({k:v for k,v in before.items() if k not in {'validate','render'}},{k:v for k,v in updated.items() if k not in {'validate','render','native_environment'}})
if __name__=='__main__':unittest.main(verbosity=2)
