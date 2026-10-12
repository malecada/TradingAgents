from pathlib import Path
import os,resource
os.sched_setaffinity(0,{2,3});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
import ast,json,hashlib,difflib,runpy,copy
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');C=F/'pilot40-continuation-contract-template-candidate-2026-10-12';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(C/'SOURCE_MANIFEST02.json')=='6bbdf3f80aaa6fe5a4525e556af1de8232a51070ac2b3ec244caf02e6af2ff58'
m=json.loads((C/'SOURCE_MANIFEST02.json').read_text())
for row in m['files']+m['source_pins']:
 p=Path(row['path']);assert p.stat().st_size==row['bytes'] and h(p)==row['sha256']
a=(C/'BASELINE_batched_continuation.py').read_text();b=(C/'batched_continuation.py').read_text();name='tradingagents/research/onchain_replication/batched_continuation.py'
assert ''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+name,tofile='b/'+name))==(C/'CANDIDATE02.diff').read_text()
assert ''.join(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile='a/'+name,tofile='b/'+name))==(C/'INVERSE02.diff').read_text()
class Legacy(ast.NodeTransformer):
 def visit_FunctionDef(self,n):
  if n.name=='_bind_contract_template':return None
  return self.generic_visit(n)
 def visit_If(self,n):
  test=ast.unparse(n.test)
  if test in ("'contract_mode' in m","'contract_mode' in _json(manifest)",'runtime_descriptor is not None'):return [self.visit(x) for x in n.orelse]
  if test=='runtime_descriptor is None':return [self.visit(x) for x in n.body]
  return self.generic_visit(n)
 def visit_Assign(self,n):
  if any(isinstance(x,ast.Name) and x.id=='runtime_descriptor' for x in n.targets):return None
  return n
assert ast.dump(Legacy().visit(ast.parse(b)))==ast.dump(ast.parse(a))
ns=runpy.run_path(str(C/'check01.py'));fixture=ns['fixture'];body=ns['body'];controls=[]
def bind(f):
 t,c,d,m,e,events=f;return e['_bind_contract_template'](t.owner.bound._run,t,m,c)
def refuse(f):
 try:bind(f)
 except ValueError:return
 raise AssertionError('unexpected template acceptance')
# Same pre-registration template is usable across actual metadata/claim identities,
# while an old actual contract is rejected on rebinding to a new identity.
x=fixture('independent-one','1'*64);y=fixture('independent-two','2'*64)
assert body(x[3])==body(y[3]);assert bind(x)==x[2] and bind(y)==y[2]
z=list(y);z[1]=x[1];refuse(z);controls.append('same frozen template across metadata/claim changes; stale actual contract refused')
# Exact source closure remains fixed even if all local synthetic mirrors agree.
f=fixture();t,c,d,m,e,_=f;required=set(t.numerical['files']);e['job'].required_sources=lambda:required
for src in (m['numerical_source']['files'],t.pair['numerical_source']['files'],t.owner.bound.record['numerical_source']['files']):src['extra.py']='5'*64
t.owner.bound._run.admission.experiment['source_files']['extra.py']='5'*64;t.owner.bound.record['policy_sha256']=ns['digest'](body(t.pair));refuse(f);controls.append('coherent extra numerical source still refuses fixed roster')
# Runtime callback cannot silently replace the bound identity after source reads.
f=fixture();t,c,d,m,e,_=f
old=e['_poll_target']
def poll(run,target):
 old(run,target);target.owner.bound=copy.copy(target.owner.bound)
e['_poll_target']=poll;refuse(f);controls.append('post-read bound replacement refused')
# Canonical comparison independently distinguishes integer/float equality.
f=fixture();f[3]['contract']['batch_cells']=4096.0;refuse(f);controls.append('float batch geometry refused')
# Proof, reader and all original authority/lock functions remain unchanged except explicit mode branch.
funcs={n.name:n for n in ast.parse(b).body if isinstance(n,ast.FunctionDef)}
for name,count in [('verify_prefix',2),('restore_prefix',1)]:
 assert sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_bind_contract_template' for n in ast.walk(funcs[name]))==count
for n in ast.walk(ast.parse(b)):
 if isinstance(n,ast.With) and any('_lock(' in ast.unparse(i.context_expr) for i in n.items):
  assert not any(isinstance(c,ast.Call) and isinstance(c.func,ast.Name) and c.func.id in ('_poll_target','_bind_contract_template') for c in ast.walk(n))
print(json.dumps({'status':'PASS','candidate_sha256':h(C/'batched_continuation.py'),'default_entire_module_ast_restored':True,'literal_inverse_and_manifest':True,'controls':controls,'initial_final_restore_bindings':True,'callbacks_outside_lifecycle_lock':True,'genuine_authority_or_numerical_imports':False},indent=2))
