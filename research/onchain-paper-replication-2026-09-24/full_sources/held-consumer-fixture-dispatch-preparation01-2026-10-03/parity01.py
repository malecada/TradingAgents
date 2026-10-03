from pathlib import Path
import ast
H=Path(__file__).resolve().parent;a=(H/'baseline-source03.txt').read_text();b=(H/'resource_fixture.py').read_text();ta=ast.parse(a);tb=ast.parse(b)
for i,n in enumerate(ta.body):
 if isinstance(n,ast.FunctionDef) and n.name in ('selection','preflight'):tb.body[i]=n
 else:
  q=tb.body[i];assert ast.dump(n,include_attributes=False)==ast.dump(q,include_attributes=False)
  assert ''.join(a.splitlines(True)[n.lineno-1:n.end_lineno])==''.join(b.splitlines(True)[q.lineno-1:q.end_lineno])
assert ast.dump(ta,include_attributes=False)==ast.dump(tb,include_attributes=False)
sa=next(n for n in ast.parse(a).body if isinstance(n,ast.FunctionDef) and n.name=='selection');sb=next(n for n in ast.parse(b).body if isinstance(n,ast.FunctionDef) and n.name=='selection');assert len(sb.body)==len(sa.body)+1
# Exact original fields check replaced and one new optional validation inserted only.
sb.body[4]=sa.body[4];del sb.body[5];assert ast.dump(sa,include_attributes=False)==ast.dump(sb,include_attributes=False)
pa=next(n for n in ast.parse(a).body if isinstance(n,ast.FunctionDef) and n.name=='preflight');pb=next(n for n in ast.parse(b).body if isinstance(n,ast.FunctionDef) and n.name=='preflight');assert len(pa.body)==len(pb.body)
i=next(i for i,n in enumerate(pb.body) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Constant) and n.test.left.value=='held_score_consumer_input');assert ast.dump(pb.body[i].orelse[0],include_attributes=False)==ast.dump(pa.body[i],include_attributes=False);pb.body[i]=pa.body[i];assert ast.dump(pa,include_attributes=False)==ast.dump(pb,include_attributes=False)
print('PASS all other bodies byte+AST exact; selection two-statement delta; preflight only optional output branch; original else identical')
