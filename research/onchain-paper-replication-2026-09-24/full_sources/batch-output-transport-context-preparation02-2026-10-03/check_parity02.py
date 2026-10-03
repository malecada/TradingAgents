import ast,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;old=(H/'non_tail_context.baseline01.txt').read_text();new=(H/'non_tail_context.py').read_text()
def spans(s):return {n.name:n for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a=spans(old);b=spans(new);lines=new.splitlines(keepends=True)
changes=[]
for name in ('load','Reservations','open_context'):
 x=a[name];y=b[name];changes.append((min([d.lineno for d in y.decorator_list]+[y.lineno])-1,y.end_lineno,old.splitlines(keepends=True)[min([d.lineno for d in x.decorator_list]+[x.lineno])-1:x.end_lineno]))
for name in ('BootstrapCleanupFailure','bootstrap_read'):
 y=b[name];changes.append((y.lineno-1,y.end_lineno,[]))
for start,end,body in sorted(changes,reverse=True):lines[start:end]=body
normalized=''.join(lines).replace('import hashlib,importlib.util,json,sys,time,os,stat\nfrom threading import current_thread','import hashlib,importlib.util,json,sys,time')
# Remove only introduced blank separator surrounding deleted bootstrap block.
normalized=normalized.replace("'one original member name required'", "'one original member name required'")
assert ast.dump(ast.parse(normalized))==ast.dump(ast.parse(old))
# Exact untouched top-level function/class spans, including entire Context implementation.
for name in set(a)-{'load','Reservations','open_context'}:
 x=a[name];y=b[name];assert ''.join(old.splitlines(keepends=True)[x.lineno-1:x.end_lineno])==''.join(new.splitlines(keepends=True)[y.lineno-1:y.end_lineno]),name
# Within Reservations, only slots/init/check/reserve differ.
x=a['Reservations'];y=b['Reservations'];oldmethods={n.name:n for n in x.body if isinstance(n,ast.FunctionDef)};newmethods={n.name:n for n in y.body if isinstance(n,ast.FunctionDef)}
for name in set(oldmethods)-{'__init__','check','reserve'}:assert ast.dump(oldmethods[name])==ast.dump(newmethods[name])
print('PASS inverse whole AST; byte-exact all existing top-level bodies outside load/Reservations/open_context; unaffected Reservations methods unchanged.')
