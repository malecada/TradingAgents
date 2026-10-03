from pathlib import Path
import ast
H=Path(__file__).resolve().parent;a=(H/'baseline01.txt').read_text();b=(H/'resource_fixture.py').read_text();t=ast.parse(b);f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='preflight');i=next(i for i,n in enumerate(f.body) if isinstance(n,ast.For) and ast.unparse(n.iter)=='(s, item)');removed=f.body[i:i+2];assert isinstance(removed[1],ast.If)
lines=b.splitlines(True);assert ''.join(lines[:removed[0].lineno-1])+''.join(lines[removed[-1].end_lineno:])==a
del f.body[i:i+2];assert ast.dump(t,include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False)
source=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-03/source/tradingagents/research/onchain_replication/held_score_consumer.py');route=next(n for n in ast.parse(source.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='_route');loop=next(n for n in route.body if isinstance(n,ast.For));new=removed[0]
class Normalize(ast.NodeTransformer):
 def visit_Name(self,n):
  if n.id=='FIELD':return ast.copy_location(ast.Constant('held_score_consumer_input'),n)
  if n.id=='selected':return ast.copy_location(ast.Name(id='s',ctx=n.ctx),n)
  return n
assert ast.dump(Normalize().visit(loop),include_attributes=False)==ast.dump(new,include_attributes=False)
print('PASS whole inverse AST+bytes with only two new preflight statements removed; reserved-prefix loop exactly actual consumer under FIELD/selected renaming')
