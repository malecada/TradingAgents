from pathlib import Path
import ast,json
D=Path(__file__).resolve().parent
s=(D/'caller01.py').read_text();t=ast.parse(s)
# Import pure definitions only: no main/launcher/Root reads or authority fixture.
nodes=[x for x in t.body if isinstance(x,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.Assign))]
e={};exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'pure-caller-definitions','exec'),e)
for name in ('REMOTE','FLAT'):
 q=json.loads((D/(name+'_CONTRACT_DRAFT01.json')).read_text())
 try:e['contract'](q)
 except AssertionError:pass
 else:raise AssertionError('null draft admitted')
for name in ('../escape','/absolute','a/../b','a//b','./a'):
 try:e['local'](name)
 except AssertionError:pass
 else:raise AssertionError('redirect admitted')
assert s.index('rejoin();assert code is not None')>s.index("'_EXIT.json'")
print(json.dumps({'checks':8,'actual_root_reads':False,'actual_child':False,'actual_network':False}))
