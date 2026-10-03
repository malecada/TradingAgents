from pathlib import Path
import ast
H=Path(__file__).resolve().parent
old=(H/'baseline02.txt').read_text();new=(H/'non_tail_context.py').read_text()
def outside(s):
 t=ast.parse(s);n=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='bootstrap_read');lines=s.splitlines(True);return ''.join(lines[:n.lineno-1])+''.join(lines[n.end_lineno:])
assert outside(old)==outside(new)
a=ast.parse(old);b=ast.parse(new)
for i,n in enumerate(a.body):
 if isinstance(n,ast.FunctionDef) and n.name=='bootstrap_read':b.body[i]=n
assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
p=H.parent/'batch-output-transport-context-preparation02-2026-10-03'
assert (H/'test_legacy01.py').read_bytes()==(p/'test_legacy01.py').read_bytes()
assert (H/'test_corrections02.py').read_text()==(p/'test_corrections02.py').read_text().replace('self.assertEqual(len(seen),1)','self.assertEqual(len(seen),2)')
print('PASS byte+AST inverse outside bootstrap_read; legacy test exact; prior tests changed only acquired FD count1→2')
