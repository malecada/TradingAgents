"""Exact source/default/runtime-guard and inverse verification; stdlib only."""
import ast,difflib,hashlib,json,subprocess,tempfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3]
expected={'resources.py':{'guarded_run','assert_guarded_worker'},'job.py':{'resource_policy'},'real_pilot_import_caller.py':{'_amended_host_reserve','_finite_resources'}}
rows=[];diffs=[]
for name,allowed in expected.items():
 a=(H/'baseline'/name).read_bytes();b=(H/name).read_bytes();target=R/'tradingagents/research/onchain_replication'/name
 assert target.read_bytes()==a,'live source changed: '+name
 x=ast.parse(a);y=ast.parse(b);assert len(x.body)==len(y.body)
 changed=[]
 for before,after in zip(x.body,y.body):
  if ast.dump(before)==ast.dump(after):continue
  assert isinstance(before,ast.FunctionDef) and isinstance(after,ast.FunctionDef) and before.name==after.name
  assert ast.dump(before.args)==ast.dump(after.args),'function signature/defaults changed'
  changed.append(before.name)
  diffs.append({'file':name,'function':before.name,'before_ast':ast.dump(before,indent=2),'after_ast':ast.dump(after,indent=2)})
 assert set(changed)==allowed
 if name=='resources.py':
  def runtime_guard(tree):
   return next(n for n in ast.walk(tree) if isinstance(n,ast.If) and len(n.body)==1 and isinstance(n.body[0],ast.Raise) and 'host runtime memory reserve breached' in ast.unparse(n.body[0]))
  assert ast.dump(runtime_guard(x))==ast.dump(runtime_guard(y))
 compile(b,str(H/name),'exec')
 rows.append({'file':name,'before_sha256':hashlib.sha256(a).hexdigest(),'after_sha256':hashlib.sha256(b).hexdigest(),'changed_functions':changed,'all_signatures_defaults_unchanged':True,'outside_changed_functions_ast_equal':True,'live_unchanged':True})
with tempfile.TemporaryDirectory() as td:
 root=Path(td)
 for name in expected:
  p=root/'tradingagents/research/onchain_replication'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((H/'baseline'/name).read_bytes())
 for patch,baseline in [('FORWARD01.patch',False),('INVERSE01.patch',True)]:
  p=subprocess.run(['patch','--batch','-p1','-i',str(H/patch)],cwd=root,capture_output=True,text=True,timeout=10)
  assert p.returncode==0,p.stderr
  for name in expected:assert (root/'tradingagents/research/onchain_replication'/name).read_bytes()==((H/'baseline' if baseline else H)/name).read_bytes()
(H/'AST_DELTA01.json').write_text(json.dumps(diffs,indent=2)+'\n')
print(json.dumps({'files':rows,'runtime_kill_predicate_ast_unchanged':True,'forward_inverse_byte_exact':True},indent=2))
