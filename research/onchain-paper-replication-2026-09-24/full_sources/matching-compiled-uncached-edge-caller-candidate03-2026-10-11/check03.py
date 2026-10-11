"""Focused actual-AST regression; no owner/native/scientific construction."""
import ast,copy,difflib,hashlib,json,os,resource,signal,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(9,9));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(12)
P=Path(__file__).resolve().parent;O=P.parent/'matching-compiled-uncached-edge-caller-candidate02-2026-10-11';R=P.parents[3]
checks=[]
def ck(v,name):
 assert v,name
 checks.append(name)
def require(v,message):
 if not v:raise ValueError(message)
def factory(node,args,env):
 f=ast.parse('def make('+','.join(args)+'):\n pass').body[0]
 f.body=[copy.deepcopy(node),ast.Return(ast.Name(node.name,ast.Load()))]
 exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),'actual-extracted-closure','exec'),env)
 return env['make']
def find(tree,name):return next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
def noop_code(fn):
 free=fn.__code__.co_freevars
 ns={};exec('def make('+','.join(free)+'):\n def replacement():\n  if False: ('+','.join(free)+',)\n  return None\n return replacement\n' if free else 'def make():\n def replacement(): return None\n return replacement\n',ns)
 out=ns['make'](*([None]*len(free)));assert out.__code__.co_freevars==free;return out.__code__
def accepted(call):
 try:call();return True
 except ValueError:return False
results={}
for directory,success in ((O,True),(P,False)):
 tree=ast.parse((directory/'compiled_edge_owner.py').read_text());pairtree=ast.parse((directory/'batched_pair_executor.py').read_text());stree=ast.parse((directory/'matching_immutable_session.py').read_text())
 guard=next(n for n in find(tree,'metadata').body if isinstance(n,ast.For))
 pairguard=next(n for n in ast.walk(pairtree) if isinstance(n,ast.For) and isinstance(n.iter,ast.Attribute) and n.iter.attr=='_edge_methods')
 note_node=find(tree,'_note');env={'require':require,'types':types};exec(compile(ast.Module(body=[note_node],type_ignores=[]),'actual-note','exec'),env)
 outcomes=[]
 for member in ('current','borrow','close'):
  events=[]
  fn=factory(find(tree,'current'),['metadata','attempted','fd','module','native_fill','fdpin','seals','close'],env)(lambda:events.append('metadata'),False,None,None,None,None,None,lambda:events.append('cleanup'))
  owner=types.SimpleNamespace(current=fn,borrow=lambda:None,close=lambda:None)
  methods={name:((getattr(owner,name),getattr(owner,name).__code__) if directory==P else getattr(owner,name)) for name in ('current','borrow','close')}
  parent=types.SimpleNamespace(_edge_owner=owner,_edge_methods=tuple((name,*value) if directory==P else (name,value) for name,value in methods.items()))
  token=object()
  leasefn=factory(find(tree,'lease_current'),['released','active','token','current','methods','self'],env)(False,token,token,fn,methods,owner)
  lease=types.SimpleNamespace(fill=lambda:None,current=leasefn,close=lambda:None)
  session=types.SimpleNamespace(_edge_lease=lease,_edge_pin=lease,_edge_functions=tuple((n,getattr(lease,n),getattr(lease,n).__code__) for n in ('fill','current','close')))
  sns={'require':require,'compiled_edge_owner':types.SimpleNamespace(current_policy=lambda obj:None)}
  exec(compile(ast.Module(body=[find(stree,'_edge_current')],type_ignores=[]),'actual-session-check','exec'),sns)
  sns['_edge_current'](session);ck(events==['metadata'],directory.name+' normal callback '+member)
  getattr(owner,member).__code__=noop_code(getattr(owner,member))
  got=[accepted(lambda:exec(compile(ast.Module(body=[guard],type_ignores=[]),'actual-owner-guard','exec'),dict(env,self=owner,methods=methods))),accepted(lambda:exec(compile(ast.Module(body=[pairguard],type_ignores=[]),'actual-parent-guard','exec'),{'self':parent})),accepted(lambda:sns['_edge_current'](session))]
  ck(got==[success]*3,directory.name+' three boundary outcomes '+member)
  if directory==P or member=='current':ck(events==['metadata'],'refused/no-op callback did not validate '+directory.name+member)
  outcomes.append({'mutation':member,'owner_parent_session_accepted':got})
 results[directory.name]=outcomes
# Actual private cleanup closure and exact published clone expression: shared descriptor state,
# independent public function code; ambiguous close is not retried.
tree=ast.parse((P/'compiled_edge_owner.py').read_text());env={'require':require,'types':types}
exec(compile(ast.Module(body=[find(tree,'_note')],type_ignores=[]),'actual-note','exec'),env)
close_node=find(tree,'close')
clone_assign=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='close' for t in n.targets))
for fails in (False,True):
 calls=[];error=OSError('ambiguous cleanup')
 def closefd(fd):
  calls.append(fd)
  if fails:raise error
 private=factory(close_node,['fd','closed','close_error','active','close_fd'],env)(37,False,None,object(),closefd)
 obj=types.SimpleNamespace();exec(compile(ast.Module(body=[clone_assign],type_ignores=[]),'actual-exposed-clone','exec'),dict(env,self=obj,close=private))
 pairtree=ast.parse((P/'batched_pair_executor.py').read_text())
 capture=next(n for n in ast.walk(pairtree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='edge_cleanup' for t in n.targets) and isinstance(n.value,ast.Call))
 cap={'owner':obj,'edge_cleanup':obj.close,'types':types};exec(compile(ast.Module(body=[capture],type_ignores=[]),'actual-parent-capture','exec'),cap)
 obj.close.__code__=noop_code(obj.close)
 for callback in (cap['edge_cleanup'],private,cap['edge_cleanup']):
  try:callback();ck(not fails,'normal independent cleanup')
  except OSError as got:ck(fails and got is error,'ambiguous identity retained')
 ck(calls==[37],'single cleanup attempt despite replaced exposed code '+str(fails))
# Exact current exception block retains fatal identity even when cleanup and annotation repr fail.
class BadError(Exception):
 def __repr__(self):raise MemoryError('annotation allocation')
primary=KeyboardInterrupt('primary');cleanup=BadError()
def die():raise primary
def badclose():raise cleanup
fn=factory(find(tree,'current'),['metadata','attempted','fd','module','native_fill','fdpin','seals','close'],env)(die,False,None,None,None,None,None,badclose)
try:fn()
except BaseException as got:ck(got is primary,'current primary identity survives cleanup and annotation failure')
combined=find(pairtree,'combined_cleanup');calls=[]
def normal():calls.append('normal');raise primary
def edge():calls.append('edge');raise cleanup
fn=factory(combined,['normal_cleanup','edge_cleanup'],env)(normal,edge)
try:fn()
except BaseException as got:ck(got is primary and calls==['normal','edge'],'both parent cleanup attempts preserve primary')
# Actual constructor: allocation failure after close acquisition must finalize both owners.
cl=copy.deepcopy(next(n for n in pairtree.body if isinstance(n,ast.ClassDef) and n.name=='PairExecutor'))
cl.body=[n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name in ('__init__','close')]
events=[];allocation=MemoryError('cleanup capability allocation')
def attachnormal(obj,value):obj._compiled_normalization_policy=value
def attachedge(obj,value):obj._compiled_edge_policy=value
def failclone(*args,**kwargs):raise allocation
edgeobj=types.SimpleNamespace(current=lambda:None,borrow=lambda:None,close=lambda:events.append('edge'))
constructor_env={'copy':copy,'sys':types.SimpleNamespace(modules={'scipy':object()}),'types':types.SimpleNamespace(FunctionType=failclone),'adaptive_edge_policy':types.SimpleNamespace(attach=lambda *args:None),'compiled_normalization_policy':types.SimpleNamespace(attach=attachnormal,BackendOwner=lambda value:types.SimpleNamespace(close=lambda:events.append('normal'))),'compiled_edge_owner':types.SimpleNamespace(attach=attachedge,EdgeOwner=lambda *args,**kwargs:edgeobj),'annealing':types.SimpleNamespace(np=object(),agreement=object())}
exec(compile(ast.Module(body=[cl],type_ignores=[]),'actual-constructor-allocation-failure','exec'),constructor_env)
schedule=dict(max_checkpoints=1,calls_per_checkpoint=1,operations_per_call=1,max_total_checkpoints=1,max_total_checkpoint_bytes=1)
try:constructor_env['PairExecutor']({},dict(max_publications=1),schedule,lambda:None,compiled_normalization_policy_value=(('x',1),),compiled_edge_policy_value=(('x',1),))
except BaseException as got:ck(got is allocation and events==['normal','edge'],'clone allocation failure preserves primary and finalizes both acquired owners')
else:ck(False,'allocation failure required')
events.clear();obj=constructor_env['PairExecutor']({},dict(max_publications=1),schedule,lambda:None);obj.close();ck(events==[],'default never constructs or clones backend')

# Exact ten-body requirement and changed-scope inverse. No package imports.
requirements=json.loads((P/'SOURCE_REQUIREMENTS01.json').read_text());changed=[]
for rel,row in requirements.items():
 name=Path(rel).name;body=(P/name).read_bytes();ck(hashlib.sha256(body).hexdigest()==row['sha256'] and len(body)==row['bytes'],'requirement '+name);ast.parse(body)
 before=(O/name).read_text();after=body.decode()
 if before!=after:
  changed.append(name)
  for a,b,suffix in ((before,after,'.from02.patch'),(after,before,'.to02.patch')):
   ck(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=name,tofile=name))==(P/(name+suffix)).read_text(),'exact predecessor inverse '+name+suffix)
ck(set(changed)=={'compiled_edge_owner.py','batched_pair_executor.py','batched_numeric_reuse.py'},'only two responsible bodies plus dependent pins changed')
memo=(P/'batched_numeric_reuse.py').read_text();oldmemo=(O/'batched_numeric_reuse.py').read_text()
for name in ('compiled_edge_owner.py','batched_pair_executor.py'):
 memo=memo.replace(hashlib.sha256((P/name).read_bytes()).hexdigest(),hashlib.sha256((O/name).read_bytes()).hexdigest())
ck(memo==oldmemo,'memo exact inverse changes only two source pins')
for name in ('metadata','acquire','current','borrow'):
 a=find(ast.parse((O/'compiled_edge_owner.py').read_text()),name);b=find(tree,name)
 ck(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='read_reference' for n in ast.walk(a))==sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='read_reference' for n in ast.walk(b)),'role read sites unchanged '+name)
out={'status':'PASS_FOCUSED_SOURCE_ONLY','checks':checks,'counterexample':results,'scientific_imports':False,'native_execution':False,'real_owner_constructed':False,'limits':{'cpu_affinity':[3],'nice':10,'cpu_seconds':9,'as_bytes':512*1024**2,'fsize_bytes':4*1024**2,'wall_alarm_seconds':12}}
(P/'RESULT03.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':out['status'],'checks':len(checks)}))
