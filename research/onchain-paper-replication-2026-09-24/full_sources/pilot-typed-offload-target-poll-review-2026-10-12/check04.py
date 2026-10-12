import os,resource
os.sched_setaffinity(0,{2,3});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
import ast,json,hashlib,difflib,runpy,types
from pathlib import Path
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');C=F/'pilot-typed-offload-target-poll-candidate-2026-10-12';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((C/'SOURCE_MANIFEST01.json').read_text());assert h(C/'SOURCE_MANIFEST01.json')=='78b83d76b23d46bf6fe602685d33430b3286c5e5f3146185cfb029de11e26fd4'
for row in [*m['source_pins'],*m['files']]:
 p=Path(row['path']);assert h(p)==row['sha256'] and p.stat().st_size==row['bytes']
names=['archive_owner_policy.py','archive_owner_operations.py','typed_payload_operations.py'];prefix='tradingagents/research/onchain_replication/'
patch='';inverse=''
for name in names:
 a=(C/('BASELINE_'+name)).read_text();b=(C/name).read_text()
 patch+=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+prefix+name,tofile='b/'+prefix+name))
 inverse+=''.join(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile='a/'+prefix+name,tofile='b/'+prefix+name))
assert (C/'CANDIDATE01.diff').read_text()==patch and (C/'INVERSE01.diff').read_text()==inverse
# Project away precisely the selected additions, then compare complete modules.
class Legacy(ast.NodeTransformer):
 def visit_FunctionDef(self,n):
  if n.name=='_poll_target_pre_cap' or (n.name=='_poll_target' and name=='archive_owner_policy.py'):return None
  if n.name in ('_inputs','_record','check','writer_policy','_current'):
   keep=[(a,d) for a,d in zip(n.args.kwonlyargs,n.args.kw_defaults) if a.arg!='target'];n.args.kwonlyargs=[a for a,d in keep];n.args.kw_defaults=[d for a,d in keep]
  return self.generic_visit(n)
 def visit_If(self,n):
  test=ast.unparse(n.test)
  if test=='target is not None' and len(n.body)==1 and isinstance(n.body[0],ast.Expr) and isinstance(n.body[0].value,ast.Call) and isinstance(n.body[0].value.func,ast.Name) and n.body[0].value.func.id=='_poll_target_pre_cap':return None
  if test=='target is not None' and len(n.body)==1 and '_poll_target(' in ast.unparse(n.body[0]):return None
  if test=='target is None' and len(n.body)==1 and 'error.add_note' in ast.unparse(n.body[0]):return n.body
  return self.generic_visit(n)
 def visit_Call(self,n):
  if isinstance(n.func,ast.Name) and n.func.id=='_Operation':return self.generic_visit(n)
  n.keywords=[k for k in n.keywords if not(k.arg is None and isinstance(k.value,ast.IfExp) and 'target' in ast.unparse(k.value))];return self.generic_visit(n)
for name in names:
 a=ast.parse((C/('BASELINE_'+name)).read_text());b=Legacy().visit(ast.parse((C/name).read_text()));assert ast.dump(a)==ast.dump(b),name
ns=runpy.run_path(str(C/'check01.py'));Fixture=ns['Fixture'];N=types.SimpleNamespace;controls=[]
# Independently vary cost close to deadline, never increase registered max_stale.
f=Fixture(cost=29);f.record();f.record();f.target.lease();assert f.t==348 and f.interval.policy['max_stale_ms']==60000
controls.append('repeated polls across348seconds with29second primitive work')
# Mutation of execution during target callback and held-transition failure stop before policy reads.
f=Fixture();f.hook=lambda t:setattr(t.execution,'_owner',object())
try:f.record()
except ValueError as e:assert 'changed during poll' in str(e) and 'execution_job' not in f.events
else:raise AssertionError('accepted owner swap')
controls.append('execution owner mutation during callback refuses before input reads')
f=Fixture();env={'require':ns['require'],'_poll_target':f.ns['_poll_target']};ns['load'](C/'typed_payload_operations.py',{'_poll_target_pre_cap'},env)
primary=KeyboardInterrupt('held transition changed');op=N(_target=f.target,_target_pin=f.target,owner=f.owner,parent=object());op.context=N(_cap=op.parent);op.held=N(check=lambda owner:(_ for _ in ()).throw(primary))
try:env['_poll_target_pre_cap'](op)
except KeyboardInterrupt as e:assert e is primary and not hasattr(op,'cap') and op.context._cap is op.parent
else:raise AssertionError('lost transition refusal')
controls.append('precap held failure preserves primary without child capability')
# Later policy read failure: existing order and exact error survive preceding polls.
f=Fixture();orig=f.owner.bound._run.read_input;fatal=SystemExit('plan failure')
def read(name):
 if name=='plan':raise fatal
 return orig(name)
f.owner.bound._run.read_input=read
try:f.record()
except SystemExit as e:assert e is fatal and f.events.count('execution_job')==1
else:raise AssertionError('accepted plan failure')
controls.append('registered plan read fatal identity/order')
# Legacy writer_policy(None) and no-keyword callers produce exactly the same trace.
a=Fixture(False);b=Fixture();ar=a.record(False);br=b.record(False);sa=a.ns['Selection'](a.owner,'archive',object(),ar);sb=b.ns['Selection'](b.owner,'archive',object(),br)
assert sa.writer_policy('mcm')==sb.writer_policy('mcm',target=None) and a.events==b.events
controls.append('legacy selection writer policy explicitNone and absence equal')
# Exact source constructor ends installing cap; no new callback after it while op=None.
t=ast.parse((C/'typed_payload_operations.py').read_text());cl=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='_Operation');init=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='__init__');at=next(i for i,n in enumerate(init.body) if isinstance(n,ast.Assign) and any(ast.unparse(x)=='self.context._cap' for x in n.targets));assert not any('_poll_target' in ast.unparse(n) for n in init.body[at+1:]);assert all('self.cap' not in ast.unparse(n) for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_poll_target_pre_cap')
print(json.dumps({'status':'PASS','controls':controls,'all_three_default_projection_ast_equal':True,'literal_patch_inverse':True,'registered_stale_ms':60000,'constructor_poll_after_cap_install':False,'qualification':'Instrumented synthetic fixture only; not genuine Target/Owner/registered execution.'},indent=2))
