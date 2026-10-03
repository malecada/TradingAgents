"""Independent source arithmetic: no graph arrays or numerical package imports."""
import ast,hashlib,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
source=P.parent/'original-import-fixture-io-candidate02-2026-10-02/array_neighborhoods.py'
t=ast.parse(source.read_text());cls=next(x for x in t.body if isinstance(x,ast.ClassDef) and x.name=='ArrayNeighborhoodIndex');ctor=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='__init__');assign=next(x for x in ctor.body if isinstance(x,ast.Assign) and any(isinstance(a,ast.Attribute) and a.attr=='buffer_allowance' for a in x.targets))
# Use the actual source expression, independently of the author's helper.
formula=compile(ast.Expression(assign.value),str(source),'eval')
for n in (2,3):
 for chunk in (65536,4096):
  size=eval(formula,{},dict(n=n,e=n,node_width=32,edge_width=16,edge_chunk=chunk))
  output=2*(n*32+n*(16+16))
  if chunk==65536:assert size>1048576
  else:assert size+output<=1048576
  print(n,chunk,size,'full-local-output-addition',output,'bound',1048576)
# Compare original numerical loop AST exactly, including purpose and pair.
old=ast.parse((P.parent/'original-import-native-refusal-candidate04-2026-10-03/guarded_formula_oracle04.py').read_text());new=ast.parse((P/'guarded_formula_oracle05.py').read_text())
a=next(n for n in ast.walk(old) if isinstance(n,ast.With));b=next(n for n in ast.walk(new) if isinstance(n,ast.With));assert ast.dump(ast.Module(body=a.body,type_ignores=[]))==ast.dump(ast.Module(body=b.body,type_ignores=[]))
assert all(isinstance(n,(ast.Expr,ast.FunctionDef)) for n in new.body)
assert not any(k.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for k in sys.modules)
print('Original loop identical. No top-level numerical/package imports or execution. Source-only arithmetic; no RSS/OS capacity proof.')
