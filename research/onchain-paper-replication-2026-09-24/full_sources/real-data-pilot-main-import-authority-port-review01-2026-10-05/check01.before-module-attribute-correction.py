from pathlib import Path
import ast, hashlib, inspect, json, os, stat, sys, tempfile, types
D=Path(__file__).resolve().parent; M=D.parents[3]; F=D.parent
A=F/'real-data-pilot-main-import-authority-port01-2026-10-05'; P=Path('tradingagents/research/onchain_replication'); T=A/'candidate'/P
C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads((A/'SOURCE_DELTA01.json').read_text()); result={}
for r in json.loads((A/'MANIFEST01.json').read_text())['members']:
 p=A/r['path']; assert p.stat().st_size==r['bytes'] and h(p)==r['sha256']
result['manifest_members_verified']=len(json.loads((A/'MANIFEST01.json').read_text())['members'])
for r in d['changed']:
 p=Path(r['path']); new=A/'candidate'/p; assert h(new)==r['candidate_sha256']==h(C/p)
 assert h(M/p)==r['baseline_sha256']==h(A/'baseline'/p.name)
 lines=new.read_text().splitlines(True)
 for e in reversed(r['edits']):
  assert lines[e['new_start']:e['new_end']]==e['new']; lines[e['new_start']:e['new_end']]=e['old']
 assert ''.join(lines).encode()==(M/p).read_bytes()
for r in d['reused']: assert h(A/'candidate'/r['path'])==r['sha256']==h(Path(r['origin']))
for p,pin in d['main_unchanged_package'].items(): assert h(M/p)==pin
result.update(changed_origin_and_inverse=7,reused_origins=17,protected_main_modules=len(d['main_unchanged_package']))
# Old named-callable interfaces remain, with only optional additions.
def defs(tree,prefix=''):
 out={}
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):out[prefix+n.name]=n
  elif isinstance(n,ast.ClassDef):out.update(defs(n,prefix+n.name+'.'))
 return out
def sig(n):
 a=n.args; pos=a.posonlyargs+a.args; defaults=[inspect.Parameter.empty]*(len(pos)-len(a.defaults))+[ast.unparse(v) for v in a.defaults]; pp=[]
 for i,(x,v) in enumerate(zip(pos,defaults)):pp.append(inspect.Parameter(x.arg,inspect.Parameter.POSITIONAL_ONLY if i<len(a.posonlyargs) else inspect.Parameter.POSITIONAL_OR_KEYWORD,default=v))
 if a.vararg:pp.append(inspect.Parameter(a.vararg.arg,inspect.Parameter.VAR_POSITIONAL))
 for x,v in zip(a.kwonlyargs,a.kw_defaults):pp.append(inspect.Parameter(x.arg,inspect.Parameter.KEYWORD_ONLY,default=inspect.Parameter.empty if v is None else ast.unparse(v)))
 if a.kwarg:pp.append(inspect.Parameter(a.kwarg.arg,inspect.Parameter.VAR_KEYWORD))
 return inspect.Signature(pp)
owned=defs(ast.parse((T/'owned_io.py').read_text())); tested=[]
for r in d['changed']:
 name=Path(r['path']).name; old=defs(ast.parse((A/'baseline'/name).read_text())); new=defs(ast.parse((T/name).read_text()))
 if name=='score_batches.py':new.update({k:owned[k] for k in ('_fatal','_flatten','_cleanup','_close_after_failure','_release','_closing','_opened','_read_path')})
 for key,n in old.items():
  assert key in new,(name,key,'removed'); before=sig(n); after=sig(new[key]);
  for pname,param in before.parameters.items():
   assert pname in after.parameters,(name,key,pname)
   now=after.parameters[pname]; assert param.kind==now.kind and param.default==now.default,(name,key,pname)
  for pname,param in after.parameters.items():
   if pname not in before.parameters: assert param.default is not inspect.Parameter.empty or param.kind in (param.VAR_POSITIONAL,param.VAR_KEYWORD),(name,key,pname)
  tested.append(name+':'+key)
result['legacy_callable_signatures_verified']=len(tested)
# Resolve relative imports of the 24-body overlay against the unchanged Main union.
files={p.stem:p for p in (M/P).glob('*.py')}; files.update({p.stem:p for p in T.glob('*.py')})
def symbols(path):
 tree=ast.parse(path.read_text()); out=set()
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.ClassDef)):out.add(n.name)
  elif isinstance(n,(ast.Import,ast.ImportFrom)):out.update(x.asname or x.name.split('.')[0] for x in n.names)
  elif isinstance(n,(ast.Assign,ast.AnnAssign)):
   for t in (n.targets if isinstance(n,ast.Assign) else [n.target]):out.update(x.id for x in ast.walk(t) if isinstance(x,ast.Name))
 return out
changed={Path(r['path']).stem for r in d['changed']}; consumers=[]; links=0
for module,path in files.items():
 tree=ast.parse(path.read_text()); aliases={}; direct=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.ImportFrom) and n.level==1:
   if n.module is None:
    for a in n.names:
     assert a.name in files,(module,a.name); aliases[a.asname or a.name]=a.name
   elif n.module in files:
    for a in n.names:assert a.name in symbols(files[n.module]),(module,n.module,a.name)
    if n.module in changed:direct.append(n.module)
 for n in ast.walk(tree):
  if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and aliases.get(n.value.id) in changed:
   dest=aliases[n.value.id]; assert n.attr in symbols(files[dest]),(module,dest,n.attr,n.lineno);links+=1;direct.append(dest)
 if set(direct):consumers.append({'module':module,'changed_dependencies':sorted(set(direct))})
result['direct_api_attribute_links']=links;result['consumer_modules']=consumers
# Extract pure score I/O bodies, without importing numpy or authority classes.
owned_env={'os':os,'sys':sys}; tree=ast.parse((T/'owned_io.py').read_text())
exec(compile(tree,str(T/'owned_io.py'),'exec'),owned_env)
ioenv=dict(owned_env,hashlib=hashlib,json=json,stat=stat)
wanted={'_require','_hash','_json','_signature','_write','_read','_stamp'}
body=[n for n in ast.parse((T/'score_batches.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name in wanted]
exec(compile(ast.Module(body=body,type_ignores=[]),str(T/'score_batches.py'),'exec'),ioenv)
with tempfile.TemporaryDirectory(dir=D) as temp:
 root=Path(temp); fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY); original_write=os.write
 proxy=types.SimpleNamespace(**{name:getattr(os,name) for name in dir(os)})
 proxy.write=lambda child,body:original_write(child,body[:3]);ioenv['os']=proxy
 try:
  raw=b'{"metadata-only":"short writes retained exactly"}'
  assert ioenv['_write'](fd,'record.json',raw)==hashlib.sha256(raw).hexdigest()
  assert ioenv['_read'](fd,'record.json',len(raw))==raw
  try:ioenv['_read'](fd,'record.json',len(raw)-1)
  except ValueError:pass
  else:raise AssertionError('oversize accepted')
  try:ioenv['_write'](fd,'record.json',b'overwrite')
  except FileExistsError:pass
  else:raise AssertionError('overwrite accepted')
  assert (root/'record.json').read_bytes()==raw
  proxy.write=lambda child,body:0
  try:ioenv['_write'](fd,'partial.json',b'partial')
  except ValueError:pass
  else:raise AssertionError('no-progress accepted')
  assert (root/'partial.json').exists()
 finally:os.close(fd)
result['metadata_io']=['short writes complete exactly','oversize refused','exclusive existing body preserved','zero-progress partial retained']
assert not {'numpy','torch','scipy','networkx'}&set(sys.modules)
result.update(numerical_imports=False,authority_objects=False,native_execution=False,decision='source_metadata_checks_passed')
print(json.dumps(result,sort_keys=True,indent=2))
