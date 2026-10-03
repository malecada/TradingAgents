import ast,copy,hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'batch-output-full-source-helper-preparation01-2026-10-03';checks=[]
def defs(p):return {n.name:n for n in ast.parse(p.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def ck(x,s):
 assert x,s
 checks.append(s)
a=defs(O.parent/'held-consumer-held-outcome-parser-preparation02-2026-10-03/held_outcome01.py');b=defs(P/'capsule_builder01.py')
for name in ('CleanupFailure','sha','canonical','equal','fatal','cleanup','signature','parse','Reader','git'):ck(ast.dump(a[name])==ast.dump(b[name]),'exact accepted success02 IO AST '+name)
a=defs(P/'build_release_draft01.py.baseline.txt')['held_metadata_draft'];b=defs(P/'build_release_draft01.py')['full_held_metadata_draft']
b.name=a.name;b.args=copy.deepcopy(a.args)
class Restore(ast.NodeTransformer):
 def visit_Call(self,n):
  if isinstance(n.func,ast.Attribute) and n.func.attr=='held_source_plan':n.keywords=[]
  if isinstance(n.func,ast.Attribute) and n.func.attr=='held_input_plan':n.keywords=[]
  return self.generic_visit(n)
 def visit_BinOp(self,n):
  if isinstance(n.op,ast.Add) and isinstance(n.right,ast.List) and [x.value for x in n.right.elts if isinstance(x,ast.Constant)]==['full202 raw caller missing; selected f64 worker remains201/206','full202/151/207 Root registration and native release absent']:return self.visit(n.left)
  return self.generic_visit(n)
b=Restore().visit(b);ck(ast.dump(a)==ast.dump(b),'draft full inverse: only dispatch keywords/signature and two blockers')
(O/'INVERSE03.json').write_text(json.dumps({'checks':checks},indent=2)+'\n');print('PASS',len(checks),'full inverse source checks')
