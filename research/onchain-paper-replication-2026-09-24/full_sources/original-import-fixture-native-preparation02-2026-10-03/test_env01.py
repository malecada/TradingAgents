import ast,unittest,types
from pathlib import Path
D=Path(__file__).resolve().parent
class Env(unittest.TestCase):
    def function(self):
        tree=ast.parse((D/'resources.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_native_owned_env'];self.assertEqual(len(nodes),1,'native boundary env selection absent')
        ns={'Path':Path};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-native-env','exec'),ns);return ns['_native_owned_env']
    def test_exact_owned_writes_and_disabled_plugins(self):
        env=self.function()(Path('/capsule'));self.assertEqual(env['TMPDIR'],'/capsule/fixture_runtime/tmp');self.assertEqual(env['XDG_CACHE_HOME'],'/capsule/fixture_runtime/cache');self.assertEqual(env['TORCH_HOME'],'/capsule/fixture_runtime/torch');self.assertEqual(env['PYTHONDONTWRITEBYTECODE'],'1');self.assertEqual(env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'],'1');self.assertEqual(env['OMP_NUM_THREADS'],'2')
        for k in ('TMPDIR','XDG_CACHE_HOME','TORCH_HOME','MPLCONFIGDIR','HF_HOME','TORCH_EXTENSIONS_DIR'):self.assertTrue(Path(env[k]).is_relative_to('/capsule'))
    def test_systemd_actual_selected_branch_forwards_environment(self):
        text=(D/'resources.py').read_text();self.assertIn("'--setenv='+key+'='+value for key,value in _native_owned_env(cwd).items()",text);self.assertIn("ready['native_environment']",text);self.assertIn("state['native_environment']",text)
if __name__=='__main__':unittest.main()
