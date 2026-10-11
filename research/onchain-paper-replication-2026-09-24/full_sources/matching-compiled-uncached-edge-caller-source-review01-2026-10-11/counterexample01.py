import ast,hashlib,json,os,resource,signal,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(20)
P=Path(__file__).resolve().parent;D=P.parent/'matching-compiled-uncached-edge-caller-candidate02-2026-10-11'
source=(D/'compiled_edge_owner.py').read_text();tree=ast.parse(source)
current=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='current')
metadata=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='metadata')
guard=next(n for n in metadata.body if isinstance(n,ast.For))
def require(ok,message):
    if not ok:raise ValueError(message)
events=[]
# Actual nested current function in an inert synthetic closure: no owner construction or native path.
factory=ast.parse('def make(metadata,attempted,fd,module,native_fill,fdpin,seals,close):\n pass').body[0]
factory.body=[current,ast.Return(value=ast.Name(id='current',ctx=ast.Load()))]
ns={'require':require,'_note':lambda *args:None}
exec(compile(ast.fix_missing_locations(ast.Module(body=[factory],type_ignores=[])),'actual-current-ast','exec'),ns)
fn=ns['make'](lambda:events.append('metadata'),False,None,None,None,None,None,lambda:events.append('close'))
owner=types.SimpleNamespace(current=fn,borrow=lambda:None,close=lambda:None)
methods=dict(current=fn,borrow=owner.borrow,close=owner.close)
fn();assert events==['metadata']
free=fn.__code__.co_freevars
replacement='def make('+','.join(free)+'):\n def replacement():\n  if False: ('+','.join(free)+')\n  return None\n return replacement\n'
replacement_ns={};exec(replacement,replacement_ns)
replacement_fn=replacement_ns['make'](*([None]*len(free)))
assert replacement_fn.__code__.co_freevars==free
fn.__code__=replacement_fn.__code__
# Exact owner metadata method guard accepts unchanged function identity with changed code.
exec(compile(ast.fix_missing_locations(ast.Module(body=[guard],type_ignores=[])),'actual-owner-guard','exec'),dict(ns,self=owner,methods=methods))
pairtree=ast.parse((D/'batched_pair_executor.py').read_text())
pairguard=next(n for n in ast.walk(pairtree) if isinstance(n,ast.For) and isinstance(n.iter,ast.Attribute) and n.iter.attr=='_edge_methods')
parent=types.SimpleNamespace(_edge_owner=owner,_edge_methods=tuple(methods.items()))
exec(compile(ast.fix_missing_locations(ast.Module(body=[pairguard],type_ignores=[])),'actual-parent-guard','exec'),{'self':parent})
# Borrow wrapper's own function/code pin remains valid; its captured current function changed.
def wrap(current):
    def lease_current():current()
    return lease_current
lease=types.SimpleNamespace(fill=lambda:None,current=wrap(fn),close=lambda:None)
session=types.SimpleNamespace(_edge_lease=lease,_edge_pin=lease,_edge_functions=tuple((name,getattr(lease,name),getattr(lease,name).__code__) for name in ('fill','current','close')))
stree=ast.parse((D/'matching_immutable_session.py').read_text())
edge_current=next(n for n in ast.walk(stree) if isinstance(n,ast.FunctionDef) and n.name=='_edge_current')
sns={'require':require,'compiled_edge_owner':types.SimpleNamespace(current_policy=lambda obj:None)}
exec(compile(ast.Module(body=[edge_current],type_ignores=[]),'actual-session-guard','exec'),sns)
sns['_edge_current'](session)
assert events==['metadata']
out={'status':'CONFIRMED_CODE_IDENTITY_GAP','actual_owner_constructed':False,'native_or_science_executed':False,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'counterexample':'Same function object __code__ replaced with equal-freevar no-op; exact owner guard, parent guard and session _edge_current accept; metadata counter remains one after borrowed current call.','old_current_freevars':list(free),'metadata_calls_before_mutation':1,'metadata_calls_after_borrowed_current':1,'guards_accepted':['EdgeOwner.metadata method identity loop','PairExecutor.__call__ parent method identity loop','ImmutablePairSession._edge_current wrapper function/code loop']}
with (P/'COUNTEREXAMPLE01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(out,sort_keys=True))
