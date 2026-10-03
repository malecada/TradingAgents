import ast,json,hashlib
from pathlib import Path
H=Path(__file__).parent;P=H.parent/'batch-output-transport-context-preparation02-2026-10-03';O=P.parent/'batch-output-transport-context-preparation01-2026-10-03';ROOT=H.resolve().parents[3]
a=(O/'non_tail_context.py').read_text();b=(P/'non_tail_context.py').read_text();assert a==(P/'non_tail_context.baseline01.txt').read_text()
old=ast.parse(a);new=ast.parse(b);names=lambda t:{n.name:n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};x=names(old);y=names(new)
for name in x.keys()-{'load','Reservations','open_context'}:
 p=x[name];q=y[name];assert a.splitlines()[p.lineno-1:p.end_lineno]==b.splitlines()[q.lineno-1:q.end_lineno]
changes=[]
for name in ('load','Reservations','open_context'):
 p=x[name];q=y[name];start=lambda n:min([n.lineno]+[d.lineno for d in n.decorator_list])-1
 changes.append((start(q),q.end_lineno,a.splitlines(keepends=True)[start(p):p.end_lineno]))
for name in ('BootstrapCleanupFailure','bootstrap_read'):q=y[name];changes.append((q.lineno-1,q.end_lineno,[]))
lines=b.splitlines(keepends=True)
for start,end,body in sorted(changes,reverse=True):lines[start:end]=body
text=''.join(lines).replace('import hashlib,importlib.util,json,sys,time,os,stat\nfrom threading import current_thread','import hashlib,importlib.util,json,sys,time')
assert ast.dump(ast.parse(text))==ast.dump(old)
# Actual transport expression is source-read, not a network execution.
t=ast.parse((ROOT/'tradingagents/research/onchain_replication/archive_transport.py').read_text());get=next(n for c in t.body if isinstance(c,ast.ClassDef) and c.name=='Transport' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='get')
count=next(n.value for n in get.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='count');assert ast.unparse(count)=='expected_bytes // BLOCK_BYTES + 1'
reserve=next(n for n in y['Reservations'].body if isinstance(n,ast.FunctionDef) and n.name=='reserve');assignment=next(n for n in ast.walk(reserve) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='new');assert ast.unparse(assignment.value.elts[0])=='b + (size // BLOCK + 1) * BLOCK'
print('PASS inverse complete AST; all unaffected existing bodies byte-identical, including entire Context; actual Transport.get floor-plus-one expression agrees at block multiples. No command execution.')
