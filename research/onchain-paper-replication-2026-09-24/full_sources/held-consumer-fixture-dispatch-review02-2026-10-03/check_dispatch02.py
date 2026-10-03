"""Independent exact-source metadata seams only; no numerical or authority imports."""
import ast,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent
PRIOR=F/'held-consumer-fixture-dispatch-review01-2026-10-03/check_dispatch01.py'
# Reuse the unchanged original review helper definitions and manifest checks,
# stopping before its first test/any evidence write; all outputs below are new.
prefix=PRIOR.read_text().split('j,pl,p,o=data();refusal')[0]
ns={'__file__':str(PRIOR)};exec(compile(prefix,str(PRIOR),'exec'),ns)
C=F/'held-consumer-fixture-dispatch-preparation02-2026-10-03'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((C/'MANIFEST02.json').read_bytes())=='7eea4137918c9dda0fcff22564fb05849498a0f512340b38a6addf876e8fdf2b'
members=json.loads((C/'MANIFEST02.json').read_bytes())['files']
for row in members:
 b=(C/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
assert (C/'baseline01.txt').read_bytes()==(ns['C']/'resource_fixture.py').read_bytes()
old=ns['NEW'];new=ns['functions'](C/'resource_fixture.py');data=ns['data'];seam=ns['seam'];refusal=ns['refusal']
checks=[]
for case,change in [('plan_only_selector',lambda s,item:s.pop('held_score_consumer_input')),('plan_only_unknown_selector',lambda s,item:item.update(held_score_typo='invalid'))]:
 j,pl,p,o=data();s=j['payload']['representation_jobs']['original32'];item=pl['producers']['original32'];change(s,item)
 if case=='plan_only_selector':o=o[:4]
 seam(old,j,pl,p,o);refusal(lambda:seam(new,j,pl,p,o));checks.append(case+': actual01 accepts, actual02 refuses')
j,pl,p,o=data();seam(new,j,pl,p,o);checks.append('valid selected six outputs')
del j['payload']['representation_jobs']['original32']['held_score_consumer_input'];del pl['producers']['original32']['held_score_consumer_input'];o=o[:4]
seam(new,j,pl,p,o);checks.append('legacy both absent, four outputs')
for label,mutate in [
 ('job_only',lambda s,item,p,o:item.pop('held_score_consumer_input')),
 ('mismatch',lambda s,item,p,o:item.update(held_score_consumer_input='other')),
 ('empty_both',lambda s,item,p,o:(s.update(held_score_consumer_input=''),item.update(held_score_consumer_input=''))),
 ('bool_both',lambda s,item,p,o:(s.update(held_score_consumer_input=True),item.update(held_score_consumer_input=True))),
 ('job_typo',lambda s,item,p,o:s.update(held_score_typo='x')),
 ('plan_typo',lambda s,item,p,o:item.update(held_score_other='x')),
 ('output_alias',lambda s,item,p,o:p['targets'][next(iter(p['targets']))].update(output='resource-binding.json')),
 ('missing_target',lambda s,item,p,o:p['targets'].pop(next(iter(p['targets'])))),
 ('missing_output',lambda s,item,p,o:o.pop()),
 ('extra_output',lambda s,item,p,o:o.append('extra.json'))]:
 j,pl,p,o=data();s=j['payload']['representation_jobs']['original32'];item=pl['producers']['original32'];mutate(s,item,p,o);refusal(lambda:seam(new,j,pl,p,o));checks.append(label)
for error in [MemoryError('policy read'),KeyboardInterrupt('policy read'),SystemExit('policy read')]:
 j,pl,p,o=data()
 try:seam(new,j,pl,p,o,read_error=error)
 except BaseException as actual:assert actual is error
 else:raise AssertionError('fatal suppressed')
 checks.append(type(error).__name__+' exact identity')
# Independent reverse deletion of precisely the new statements gives whole bytes.
a=(C/'baseline01.txt').read_text();b=(C/'resource_fixture.py').read_text();ta=ast.parse(a);tb=ast.parse(b)
pa=next(n for n in ta.body if isinstance(n,ast.FunctionDef) and n.name=='preflight');pb=next(n for n in tb.body if isinstance(n,ast.FunctionDef) and n.name=='preflight')
newloop=next(n for n in pb.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='value')
i=pb.body.index(newloop);newif=pb.body[i+1];assert isinstance(newif,ast.If)
lines=b.splitlines(True);del lines[newloop.lineno-1:newif.end_lineno];assert ''.join(lines)==a
del pb.body[i:i+2];assert ast.dump(ta)==ast.dump(tb);checks.append('inverse whole bytes and AST exact outside two new statements')
# Consumer reserved-prefix predicate is the actual one with only name/literal mapping.
route=next(n for n in ast.parse((ns['S']/'held_score_consumer.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='_route')
loop=next(n for n in route.body if isinstance(n,ast.For))
class Map(ast.NodeTransformer):
 def visit_Name(self,n):
  if n.id=='selected':return ast.copy_location(ast.Name(id='s',ctx=n.ctx),n)
  if n.id=='FIELD':return ast.copy_location(ast.Constant(value='held_score_consumer_input'),n)
  return n
assert ast.dump(Map().visit(loop))==ast.dump(newloop)
# Actual new seam never assigns representation variable name; execute it with a sentinel.
fragment=compile(ast.fix_missing_locations(ast.Module(body=[newloop,newif],type_ignores=[])),str(C/'resource_fixture.py'),'exec')
j,pl,p,o=data();env={'s':j['payload']['representation_jobs']['original32'],'item':pl['producers']['original32'],'require':new['require'],'name':'original32'}
exec(fragment,env);assert env['name']=='original32' and env['held_name']=='held_score_policy';checks.append('representation name retained; actual reserved predicate parity')
# Location proof: preflight finishes before any genuine binding factory in execute.
tree=ast.parse(b);execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
calls=[n for n in ast.walk(execute) if isinstance(n,ast.Call)]
preline=min(n.lineno for n in calls if isinstance(n.func,ast.Name) and n.func.id=='preflight')
ownerline=min(n.lineno for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='open_first')
assert preline<ownerline;checks.append(f'preflight line {preline} precedes open_first line {ownerline}')
record={'scope':'actual source AST with synthetic metadata/registered-reader stand-ins; no genuine Owner or numerical job','candidate_sha256':sha(b.encode()),'manifest_members_verified':len(members),'checks':checks,'old_review_helper_sha256':sha(PRIOR.read_bytes())}
(H/'READBACK02.json').write_text(json.dumps(record,indent=2)+'\n')
for c in checks:print('PASS',c)
print('PASS',len(checks),'bounded checks;',len(members),'manifest members; no numerical imports, actual claims or Owner')
