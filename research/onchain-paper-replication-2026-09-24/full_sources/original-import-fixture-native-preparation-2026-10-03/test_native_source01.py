import ast,unittest,types
from pathlib import Path
D=Path(__file__).resolve().parent

def functions(names):
    tree=ast.parse((D/'resources.py').read_text());ns={}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==set(names),'actual native seam missing'
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-native-resource-functions','exec'),ns)
    return ns

class Native(unittest.TestCase):
    def test_policy_strictness_and_legacy_none(self):
        f=functions(['_native_policy'])['_native_policy'];self.assertIsNone(f(None))
        self.assertEqual(f({'file_size_bytes':4194304}),{'file_size_bytes':4194304})
        for bad in ({},{'file_size_bytes':True},{'file_size_bytes':0},{'file_size_bytes':4194305},{'file_size_bytes':4194304,'extra':1}):
            with self.assertRaises(ValueError):f(bad)
    def test_native_readback_refuses_missing_or_wrong(self):
        f=functions(['_native_policy','_native_seconds','_native_ready'])['_native_ready'];p={'file_size_bytes':4194304}
        props={'LimitFSIZE':'4194304','LimitFSIZESoft':'4194304','RuntimeMaxUSec':'30min'}
        f(p,{'native_unit_limits':p,'file_size_limit':[4194304,4194304]},props,1800)
        for ready in ({},{'file_size_limit':[4194304,4194304]},{'native_unit_limits':p,'file_size_limit':[True,4194304]}):
            with self.assertRaises(ValueError):f(p,ready,props,1800)
        with self.assertRaises(ValueError):f(p,{'native_unit_limits':p,'file_size_limit':[4194304,4194304]}, {},1800)
    def test_actual_worker_readback_before_claim(self):
        tree=ast.parse((D/'job.py').read_text());worker=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='worker')
        calls=[n for n in ast.walk(worker) if isinstance(n,ast.Call)]
        capture=next(n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='_resource_limit_receipt')
        start=next(n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='start')
        self.assertLess(capture.lineno,start.lineno)
    def test_native_options_only_optin(self):
        tree=ast.parse((D/'resources.py').read_text());guard=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='guarded_run')
        self.assertIn('native_unit_limits',[a.arg for a in guard.args.kwonlyargs])
        for literal in ('--native-file-limit','--property=LimitFSIZE='):
            self.assertIn(literal,(D/'resources.py').read_text())
        self.assertIn('native_unit_limits=job[\'resources\'].get(\'native_unit_limits\')',(D/'job.py').read_text())

if __name__=='__main__':unittest.main()
