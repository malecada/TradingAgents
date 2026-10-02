import importlib.util,sys,unittest,ast
from pathlib import Path
D=Path(__file__).resolve().parent
P=D.parent/'original-import-fixture-io-candidate03-2026-10-02'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
matcher=load('test_active_fatal01',P/'test_active_fatal01.py');matcher.DEPENDENCY=D
assembly=load('prior_assembly',P/'test_assembly01.py');assembly.HERE=D
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(matcher.ActiveFatal),unittest.defaultTestLoader.loadTestsFromTestCase(assembly.Assembly)])
result=unittest.TextTestRunner(verbosity=2).run(suite)
# Full resource module AST differs only by removal of optional note try.
a=ast.parse((D/'resource_fixture.baseline.py').read_text());b=ast.parse((D/'resource_fixture.py').read_text())
f=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='_preserve_terminal')
f.body=[n for n in f.body if not (isinstance(n,ast.Try) and any(isinstance(k,ast.Attribute) and k.attr=='add_note' for k in ast.walk(n)))]
assert ast.dump(a)==ast.dump(b)
# Owned helper changes only selected-fatal annotation/cause block.
a=ast.parse((D/'owned_io.baseline.py').read_text());b=ast.parse((D/'owned_io.py').read_text())
f=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='_cleanup')
g=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=='_cleanup')
x=next(n for n in f.body if isinstance(n,ast.If) and ast.unparse(n.test)=='selected is not None')
y=next(n for n in g.body if isinstance(n,ast.If) and ast.unparse(n.test)=='selected is not None')
x.body=y.body
assert ast.dump(a)==ast.dump(b)
print('PASS: exact AST parity outside selected-fatal diagnostics; existing seven regressions')
raise SystemExit(not result.wasSuccessful())
