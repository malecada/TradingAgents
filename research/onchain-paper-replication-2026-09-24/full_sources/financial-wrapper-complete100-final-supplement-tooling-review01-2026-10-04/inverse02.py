from pathlib import Path
import json,ast,hashlib,copy
D=Path(__file__).resolve().parent;A=D.parent/'financial-wrapper-complete100-final-supplement-tooling01-2026-10-04';checks=[]
def ok(v,n):assert v,n;checks.append(n)
s=(A/'ORIGINAL_REMOTE01.py').read_text();inv=json.loads((A/'SOURCE_INVERSE01.json').read_bytes());ok(len(inv['changes'])==4,'exact4 remote substitutions')
for r in inv['changes']:ok(s.count(r['original'])==1,'unique original substitution');s=s.replace(r['original'],r['replacement'],1)
ok(s==(A/'recover01.py').read_text(),'full literal remote inverse');ok(ast.dump(ast.parse(s))==ast.dump(ast.parse((A/'recover01.py').read_text())),'whole remote AST inverse')
ns={'Path':Path,'hashlib':hashlib,'json':json,'FILE':4194304,'REQUIRED':json.loads((A/'REQUIRED_BODIES01.json').read_bytes())};tree=ast.parse(s)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ('require','digest','validate_fixed_selection')],type_ignores=[]),'actual_pure_selection','exec'),ns)
v={'remote_commit':None,'rows':[dict(path=k,**r)for k,r in sorted(ns['REQUIRED'].items())]};ns['validate_fixed_selection'](v)
for label,fn in [('missing',lambda q:q['rows'].pop()),('duplicate',lambda q:q['rows'].append(q['rows'][0])),('hash',lambda q:q['rows'][0].update(sha256='0'*64)),('path',lambda q:q['rows'][0].update(path='../x')),('size',lambda q:q['rows'][0].update(bytes=4194305))]:
 q=copy.deepcopy(v);fn(q)
 try:ns['validate_fixed_selection'](q)
 except ValueError:checks.append('refused '+label)
 else:raise AssertionError(label)
(D/'INVERSE02.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks,'actual_helper_entry':False},indent=2)+'\n');print(len(checks))
