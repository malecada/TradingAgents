import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).parent
old=ast.parse((HERE/'baseline.py').read_bytes());new=ast.parse((HERE/'candidate01.py').read_bytes())
a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='validate');b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='validate')
def bounds(fn):
 start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='indices')
 end=next(i for i,n in enumerate(fn.body) if i>start and isinstance(n,ast.Expr) and 'repeated representative' in ast.unparse(n));return start,end
x,y=bounds(a);xx,yy=bounds(b)
b.body[xx:yy]=a.body[x:y]
assert ast.dump(old)==ast.dump(new),'unexpected other source/AST change'
assert hashlib.sha256((HERE/'baseline.py').read_bytes()).hexdigest()=='cbe571a3758695b2ff63a45031c90840a7358538f9a2c0bad31077db8439a6d9'
# All state is local to each validate call. No new globals, callbacks, digests,
# imports, authority call removals or canonical implementation changes.
print(json.dumps({'status':'passed','whole_module_AST_equal_after_restoring_membership_slice':True,'baseline_sha256':hashlib.sha256((HERE/'baseline.py').read_bytes()).hexdigest(),'new_global_or_capability_cache':False}))
