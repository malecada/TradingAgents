"""Remaining source pins/default path and outer close chain; ordinary FD only."""
import ast,copy,hashlib,json,os,resource,signal,sys,types
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];C=F/'matching-compiled-normalization-connected03-2026-10-10';O=F/'matching-compiled-normalization-connected02-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(10,)*2);signal.alarm(15);assert os.sched_getaffinity(0)=={3}
checks=[]
def ok(n,v=True):assert v,n;checks.append(n)
sha=lambda b:hashlib.sha256(b).hexdigest()
m=(O/'MANIFEST01.json').read_bytes();ok('frozen02 manifest',sha(m)=='d309ed04d988e7655628e4d42e6852d7ebc039cf08ef023a247b5dcdaa5dfc55')
for n in ('compiled_normalization_policy.py','compiled_small_lse.py','matching_immutable_session.py','batched_pair_executor.py','batched_numeric_reuse.py','matching_annealing.py','matching_checkpoint.py','batched_numeric_execution.py'):
 r=json.loads(m)['artifacts'][n];b=(O/n).read_bytes();ok('exact accepted02 body '+n,sha(b)==r['sha256'] and len(b)==r['bytes'])
def classtree(file):return next(n for n in ast.parse((C/file).read_bytes()).body if isinstance(n,ast.ClassDef))
def method(file,cls,name,ns):
 tree=ast.parse((C/file).read_bytes());c=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls);n=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[n],type_ignores=[]),str(C/file),'exec'),ns);return ns[name]
for file,cls,allowed in [('matching_immutable_session.py','ImmutablePairSession',{'__init__','current','advance'}),('batched_pair_executor.py','PairExecutor',{'__init__','__call__','close'}),('batched_numeric_reuse.py','NumericReuseExecutor',{'__init__','_current','_poison','close'})]:
 a=ast.parse((O/file).read_bytes());b=ast.parse((C/file).read_bytes())
 for t in (a,b):
  cl=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name==cls);cl.body=[n for n in cl.body if not isinstance(n,ast.FunctionDef) or n.name not in allowed]
  if file=='batched_numeric_reuse.py':t.body=[n for n in t.body if not isinstance(n,ast.Assign) or not any(isinstance(x,ast.Name) and x.id=='SOURCE_PINS' for x in n.targets)]
 ok('remaining whole AST exact '+file,ast.dump(a)==ast.dump(b))
p=types.ModuleType('review_policy');exec(compile((C/'compiled_normalization_policy.py').read_text(),'metadata','exec'),p.__dict__)
reuse=ast.parse((C/'batched_numeric_reuse.py').read_bytes());roster=next(n for n in reuse.body if isinstance(n,ast.FunctionDef) and n.name=='roster');ns=dict(types=types,MODULES=(p,));exec(compile(ast.Module(body=[roster],type_ignores=[]),'roster','exec'),ns)
ok('unchanged roster covers new owner constructor',any(x[1]=='BackendOwner.__init__' for x in ns['roster']()))
noop=lambda *a,**kw:None
edge=types.SimpleNamespace(attach=noop,current=noop,options=lambda *a:{},join=noop)
seam=types.SimpleNamespace(attach=p.attach,BackendOwner=lambda *a:(_ for _ in ()).throw(AssertionError('default allocated owner')))
tree=ast.parse((C/'batched_pair_executor.py').read_bytes());pair=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PairExecutor');ns=dict(copy=copy,adaptive_edge_policy=edge,compiled_normalization_policy=seam);exec(compile(ast.Module(body=[pair],type_ignores=[]),'pair','exec'),ns)
Pair=ns['PairExecutor'];default=Pair({},dict(max_publications=1),dict(max_checkpoints=1,calls_per_checkpoint=1,operations_per_call=1,max_total_checkpoints=1,max_total_checkpoint_bytes=1),noop)
ok('default constructs no backend owner',default._normalization_owner is None);default.close();ok('default closes',default.closed)
# Capture an ordinary descriptor in the original cleanup; use actual outer methods.
fd=os.open(P/'ordinary-source.txt',os.O_RDONLY);events=[]
def cleanup():events.append('backend_cleanup');os.close(fd)
obj=Pair.__new__(Pair);obj.closed=False;obj._normalization_cleanup=cleanup
memo=types.SimpleNamespace(active=False,poisoned=False,closed=False,_clear=lambda:events.append('cache_clear'),last_receipt=None,_executor_cleanup=obj.close)
memo.close=types.MethodType(method('batched_numeric_reuse.py','NumericReuseExecutor','close',{}),memo)
numeric=types.SimpleNamespace(closed=False,memo=memo,finished=True,origins_fd=None,batches_fd=None,fd=None,buffer=bytearray())
method('batched_numeric_execution.py','NumericExecution','close',dict(os=os))(numeric)
ok('actual outer close chain',events==['cache_clear','backend_cleanup'] and obj.closed and memo.closed and numeric.closed)
try:os.fstat(fd);closed=False
except OSError:closed=True
ok('outer close descriptor actually closed',closed)
ok('no native/scientific imports',not {'numpy','scipy','torch','ctypes','array'}&set(sys.modules))
(P/'ADDITIONAL02.json').write_text(json.dumps(dict(checks=checks,check_count=len(checks),events=events,native_or_numerical_execution=False),indent=2)+'\n');print(len(checks))
