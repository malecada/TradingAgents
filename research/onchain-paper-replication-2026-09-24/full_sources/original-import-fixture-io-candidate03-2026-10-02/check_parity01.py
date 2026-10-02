import ast,json
from pathlib import Path
d=Path(__file__).resolve().parent
old=d.parent/'original-import-fixture-io-candidate02-2026-10-02'
dump=lambda x:ast.dump(x,include_attributes=False)
a=ast.parse((d/'compact_matcher.baseline02.py').read_text());b=ast.parse((d/'compact_matcher.py').read_text())
removed=0
for n in ast.walk(a):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='_cleanup':
  ks=[k for k in n.keywords if k.arg=='primary' and isinstance(k.value,ast.Name) and k.value.id=='primary']
  for k in ks:n.keywords.remove(k);removed+=1
assert removed==1 and dump(a)==dump(b)
a=ast.parse((d/'resource_fixture.baseline02.py').read_text());b=ast.parse((d/'resource_fixture.py').read_text())
def fn(t,name):return next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
x,y=fn(a,'execute'),fn(b,'execute');tx=next(n for n in x.body if isinstance(n,ast.Try));ty=next(n for n in y.body if isinstance(n,ast.Try));assert [dump(n) for n in tx.body]==[dump(n) for n in ty.body]
def initial(f):return next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='journal' for t in n.targets))
assert [dump(n) for n in x.body[:initial(x)+1]]==[dump(n) for n in y.body[:initial(y)+1]]
for n in a.body:
 if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name!='execute':assert dump(n)==dump(next(k for k in b.body if isinstance(k,type(n)) and k.name==n.name))
for name in ('compact_matcher','resource_fixture'):
 assert (d/(name+'.baseline02.py')).read_bytes()==(old/(name+'.py')).read_bytes()
print('PASS: matcher single keyword removal; exact resource numerical body/preflight and existing helpers/classes; both baselines equal IO02')
