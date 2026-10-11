import ast,copy,difflib,hashlib,json,os,resource,signal,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(20)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'matching-compiled-uncached-edge-caller-candidate03-2026-10-11';O=F/'matching-compiled-uncached-edge-caller-candidate02-2026-10-11';Q=F/'pilot34-native-owner-qualification01-2026-10-11';checks=[];refs={}
def read(p):
 b=p.read_bytes();assert len(b)<2*1024**2 and p.suffix!='.so';refs[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b.decode()
def ck(value,name):
 checks.append({'name':name,'pass':bool(value)});assert value,name
def find(tree,name):return next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
def require(value,message):
 if not value:raise ValueError(message)
def factory(node,names,env):
 f=ast.parse('def make('+','.join(names)+'):\n pass').body[0];f.body=[copy.deepcopy(node),ast.Return(ast.Name(node.name,ast.Load()))]
 exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),'actual-changed-closure-ast','exec'),env);return env['make']
def noop(fn):
 names=fn.__code__.co_freevars;ns={}
 text='def make('+','.join(names)+'):\n def replacement():\n  if False: ('+','.join(names)+(',)' if names else ')')+'\n  return None\n return replacement\n'
 exec(text,ns);replacement=ns['make'](*([None]*len(names)));assert replacement.__code__.co_freevars==names;return replacement.__code__
def refused(call):
 try:call()
 except ValueError:return True
 return False
manifest=json.loads(read(D/'MANIFEST03.json'));ck(refs[str((D/'MANIFEST03.json').relative_to(R))]['sha256']=='b538a58b35a13b567902b6325dbe35e402556fe08585b402defbd5948c9a4912','exact candidate03 manifest')
for name,row in manifest['files'].items():read(D/name);ck(refs[str((D/name).relative_to(R))]==row,'frozen member '+name)
requirements=json.loads(read(D/'SOURCE_REQUIREMENTS01.json'));changed=[]
for rel,row in requirements.items():
 name=Path(rel).name;after=read(D/name);before=read(O/name);ck(refs[str((D/name).relative_to(R))]==row,'source requirement '+name)
 if before!=after:
  changed.append(name)
  for a,b,suffix in ((before,after,'.from02.patch'),(after,before,'.to02.patch')):ck(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=name,tofile=name))==read(D/(name+suffix)),'exact changed inverse '+name+suffix)
ck(set(changed)=={'compiled_edge_owner.py','batched_pair_executor.py','batched_numeric_reuse.py'},'two behavioral repairs and memo only; seven bodies unchanged')
memo=read(D/'batched_numeric_reuse.py')
for name in ('compiled_edge_owner.py','batched_pair_executor.py'):memo=memo.replace(hashlib.sha256(read(D/name).encode()).hexdigest(),hashlib.sha256(read(O/name).encode()).hexdigest())
ck(memo==read(O/'batched_numeric_reuse.py'),'memo only two dependent hashes')
oldreview=read(F/'matching-compiled-uncached-edge-caller-source-review01-2026-10-11/REVIEW01.json');ck(hashlib.sha256(oldreview.encode()).hexdigest()=='69ac19c79da59e9a373fff222ba7d4815a7a030e81a71e79300d0d33adf00451','frozen refusal reused')
tree=ast.parse(read(D/'compiled_edge_owner.py'));pairtree=ast.parse(read(D/'batched_pair_executor.py'));sessiontree=ast.parse(read(D/'matching_immutable_session.py'))
guard=next(n for n in find(tree,'metadata').body if isinstance(n,ast.For));pguard=next(n for n in ast.walk(pairtree) if isinstance(n,ast.For) and isinstance(n.iter,ast.Attribute) and n.iter.attr=='_edge_methods')
env={'require':require,'types':types};exec(compile(ast.Module(body=[find(tree,'_note')],type_ignores=[]),'actual-note','exec'),env)
for name in ('current','borrow','close'):
 events=[];fn=factory(find(tree,'current'),['metadata','attempted','fd','module','native_fill','fdpin','seals','close'],env)(lambda:events.append('metadata'),False,None,None,None,None,None,lambda:None)
 owner=types.SimpleNamespace(current=fn,borrow=lambda:None,close=lambda:None);methods={n:(getattr(owner,n),getattr(owner,n).__code__) for n in ('current','borrow','close')};parent=types.SimpleNamespace(_edge_owner=owner,_edge_methods=tuple((n,*v) for n,v in methods.items()));token=object()
 leasefn=factory(find(tree,'lease_current'),['released','active','token','current','methods','self'],env)(False,token,token,fn,methods,owner)
 lease=types.SimpleNamespace(fill=lambda:None,current=leasefn,close=lambda:None);session=types.SimpleNamespace(_edge_lease=lease,_edge_pin=lease,_edge_functions=tuple((n,getattr(lease,n),getattr(lease,n).__code__) for n in ('fill','current','close')))
 sns={'require':require,'compiled_edge_owner':types.SimpleNamespace(current_policy=lambda obj:None)};exec(compile(ast.Module(body=[find(sessiontree,'_edge_current')],type_ignores=[]),'unchanged-session-guard','exec'),sns)
 sns['_edge_current'](session);ck(events==['metadata'],'normal current '+name)
 getattr(owner,name).__code__=noop(getattr(owner,name))
 outcomes=[refused(lambda:exec(compile(ast.Module(body=[guard],type_ignores=[]),'owner-guard','exec'),dict(env,self=owner,methods=methods))),refused(lambda:exec(compile(ast.Module(body=[pguard],type_ignores=[]),'parent-guard','exec'),{'self':parent})),refused(lambda:sns['_edge_current'](session))]
 ck(all(outcomes) and events==['metadata'],'same-object '+name+' code mutation refused before current by owner/parent/session')
clone=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='close' for t in n.targets))
capture=next(n for n in ast.walk(pairtree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='edge_cleanup' for t in n.targets) and isinstance(n.value,ast.Call))
calls=[];error=OSError('synthetic ambiguous close')
def closefd(fd):calls.append(fd);raise error
private=factory(find(tree,'close'),['fd','closed','close_error','active','close_fd'],env)(37,False,None,object(),closefd)
owner=types.SimpleNamespace();exec(compile(ast.Module(body=[clone],type_ignores=[]),'actual-exposed-close-clone','exec'),dict(env,self=owner,close=private));cap={'edge_cleanup':owner.close,'types':types};exec(compile(ast.Module(body=[capture],type_ignores=[]),'actual-parent-capture','exec'),cap)
owner.close.__code__=noop(owner.close)
for callback in (cap['edge_cleanup'],private,cap['edge_cleanup']):
 try:callback()
 except OSError as got:ck(got is error,'captured ambiguous error identity retained')
 else:ck(False,'close should fail')
ck(calls==[37],'captured private cleanup unaffected by exposed code; no ambiguous retry')
# Extract parent constructor, force failure at newly added clone allocation.
cl=copy.deepcopy(next(n for n in pairtree.body if isinstance(n,ast.ClassDef) and n.name=='PairExecutor'));cl.body=[n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name in ('__init__','close')]
events=[];primary=MemoryError('synthetic copy allocation')
def failclone(*a,**k):raise primary
def attachnormal(obj,value):obj._compiled_normalization_policy=value
def attachedge(obj,value):obj._compiled_edge_policy=value
edge=types.SimpleNamespace(close=lambda:events.append('edge'),current=lambda:None,borrow=lambda:None)
cenv={'types':types.SimpleNamespace(FunctionType=failclone),'copy':copy,'sys':types.SimpleNamespace(modules={'scipy':object()}),'adaptive_edge_policy':types.SimpleNamespace(attach=lambda *a:None),'compiled_normalization_policy':types.SimpleNamespace(attach=attachnormal,BackendOwner=lambda v:types.SimpleNamespace(close=lambda:events.append('normal'))),'compiled_edge_owner':types.SimpleNamespace(attach=attachedge,EdgeOwner=lambda *a,**k:edge),'annealing':types.SimpleNamespace(np=object(),agreement=object())};exec(compile(ast.Module(body=[cl],type_ignores=[]),'constructor-standins','exec'),cenv)
schedule=dict(max_checkpoints=1,calls_per_checkpoint=1,operations_per_call=1,max_total_checkpoints=1,max_total_checkpoint_bytes=1)
try:cenv['PairExecutor']({},dict(max_publications=1),schedule,lambda:None,compiled_normalization_policy_value=(('x',1),),compiled_edge_policy_value=(('x',1),))
except BaseException as got:ck(got is primary and events==['normal','edge'],'clone allocation failure closes both owners before publication with primary retained')
else:ck(False,'expected clone failure')
events.clear();default=cenv['PairExecutor']({},dict(max_publications=1),schedule,lambda:None);default.close();ck(not events,'default constructs no owner or clone')
harness=read(Q/'qualify01.py');ck(hashlib.sha256(harness.encode()).hexdigest()=='f67e3915324472e01a704353d18cc8660994813b181de940db5020821c1b0848','exact queued harness');ast.parse(harness);read(Q/'SOURCE_CHECK01.json')
ck(harness.index('not UNIT.exists()')<harness.index('out.mkdir')<harness.index('import numpy'),'active refusal before exclusive output before numerical imports')
ck(all(s in harness for s in ["owner_path = pinned(args.owner, args.owner_sha256)","kernel_path = pinned(args.kernel, args.kernel_sha256)","baseline_path = pinned(","policy_path = pinned(","owner_module = load(","candidate = load(","exist_ok=False","result_path.open('xb')"]),'explicit source/policy pins unique loads and exclusive result')
ck(all(s in harness for s in ['np.frombuffer(array.tobytes()',"counts['accepted'] > 0",'a.tobytes() == b.tobytes()','require(u == v',"errors[0] == errors[1]","'OverflowError'",'equal(x, y)']),'immutable eligibility native-hit denominator exact state count and error controls present')
ck("native.fill.__module__ not in ('_edge_chunk',native.__name__)" in read(D/'edge_chunk_adapter.py'),'adapter allows unqualified or actual qualified module; report wording corrected')
out={'status':'PASS_CHANGED_SOURCE_AND_QUEUED_HARNESS_ONLY','checks':checks,'references':refs,'executed_real_owner_native_science_or_harness':False,'reused_prior_upper_checks':98,'reused_prior_lower_checks':40}
with (P/'RESULT01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'status':out['status'],'checks':len(checks),'result_sha256':hashlib.sha256((P/'RESULT01.json').read_bytes()).hexdigest()}))
