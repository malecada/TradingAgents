"""Extract actual cleanup/compute bodies; synthetic scalar IO, no numerical imports."""
import ast,hashlib,json,os,tempfile,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PKG=ROOT/'tradingagents/research/onchain_replication'

def stdlib_module(name):
 p=PKG/(name+'.py');m=types.ModuleType(name);m.__file__=str(p)
 exec(compile(p.read_bytes(),str(p),'exec'),vars(m));return m
io=stdlib_module('owned_io');durability=stdlib_module('chunk_durability')

def methods(filename,classname,names,env):
 tree=ast.parse((PKG/filename).read_text());original=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==classname)
 body=[n for n in original.body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert len(body)==len(names)
 node=ast.Module(body=[ast.ClassDef(name=classname,bases=[],keywords=[],body=body,decorator_list=[])],type_ignores=[])
 ast.fix_missing_locations(node);exec(compile(node,str(PKG/filename),'exec'),env)
 return env[classname]
Tail=methods('score_tail.py','ScoreTail',{'close','durability_barrier'},dict(batch=io,os=os))
Stream=methods('mcm_score_stream.py','MCMScoreStream',{'close'},dict(batch=io,os=os))

class Recorder:
 def __init__(self):self.calls=0
 def close(self):self.calls+=1

checks=[]
def run_case(source,*,failure=None,close_error=None,poison_early=False,closed_early=False,syscall_error=None):
 with tempfile.TemporaryDirectory(dir=HERE) as td:
  root=Path(td);path=root/'retained-synthetic-tail.bin';path.write_bytes(b'original synthetic retained tail\n')
  before=path.read_bytes();events=[];owner=types.SimpleNamespace(poisoned=False,matching={},bound=types.SimpleNamespace(context={},record={'workflow_identity':'synthetic'}),identity='synthetic')
  state={'stream':None,'tail':None,'lease_valid':True,'close_attempts':0}
  def live():
   events.append('live')
   if owner.poisoned or not state['lease_valid']:raise ValueError('owner poisoned or writer lease revoked')
  def stream_factory(*args,**kw):
   stream=Stream();tail=Tail();tail.closed=False
   tail.record_fd=os.open(path,os.O_RDWR);tail.fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
   tail._durability=durability.BatchSync({'schema_version':1,'scope':'resource-pilot-only','pair_records':1024,'tail_records':1024,'max_interval_ms':60000},'tail')
   tail._durability.acknowledge(tail.record_fd,1,'synthetic-head')
   def check(**kw):
    events.append('tail-check');state['close_attempts']+=1;live()
    if close_error is not None:raise close_error
    assert os.fstat(tail.record_fd).st_size==len(before)
   tail._check=check
   def sync(fd):
    if syscall_error=='fsync' and fd==tail.record_fd:raise OSError('actual synthetic descriptor fsync failure')
    return os.fsync(fd)
   def close(fd):
    result=os.close(fd)
    if syscall_error=='close' and fd==tail.record_fd:raise OSError('actual synthetic descriptor close reported uncertain')
    return result
   durability.os=types.SimpleNamespace(fsync=sync)
   Tail.close.__globals__['os']=types.SimpleNamespace(close=close)
   stream.closed=False;stream.active=tail;stream.batches=Recorder();stream.fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY);stream.scope={'workflow':'synthetic'}
   stream.finish=lambda: {'terminal_sha256':'synthetic-terminal'}
   state['stream']=stream;state['tail']=tail
   return stream
  def kernel_call(*args,**kw):
   events.append('kernel')
   if closed_early:state['stream'].close()
   if poison_early:owner.poisoned=True
   if failure is not None:raise failure
   return {'mcm':'synthetic-scalar-no-array'}
  env={'compact_matcher':types.SimpleNamespace(CompactMatcher=lambda *a,**k:types.SimpleNamespace(retention=None)),
       'thaw':lambda x:x,'stage_retention':types.SimpleNamespace(options=lambda stage:None),'MCMScoreStream':stream_factory,
       'BACKEND':{},'_imported':lambda _:False,'require':lambda ok,why:None if ok else (_ for _ in ()).throw(ValueError(why)),
       '_original':lambda *a:None,'_matrix':lambda *a:'synthetic-matrix-pin','io':io}
  parsed=ast.parse(source.read_text());outer=next(n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked')
  compute=next(n for n in ast.walk(outer) if isinstance(n,ast.FunctionDef) and n.name=='compute')
  template=ast.parse('''def factory(owner,stage,kernel):
    log=None
    stream=None
    p={'pair':{},'schedule':{},'score_chunk_cells':65536}
    policy={'schema_version':1,'max_entries':32,'numeric':{}}
    scope={'workflow':'synthetic'}
    graph=None
    graph_hash='synthetic'
    dictionary=type('D',(),{'dictionary':None})()
    start={'rows':1,'motifs':32}
    held_consumer=None
    held=None
    pass
    return compute
''')
  template.body[0].body[-2]=compute;ast.fix_missing_locations(template)
  exec(compile(template,str(source),'exec'),env)
  stage=types.SimpleNamespace(root=root)
  compute_call=env['factory'](owner,stage,types.SimpleNamespace(mcm=kernel_call))
  event_log=types.SimpleNamespace(durability_barrier=lambda:events.append('pair-barrier'))
  observed=None
  try:compute_call(event_log,live)
  except BaseException as e:observed=e
  # Exact writer ordering relevant to the defect: inner abort poisons Owner,
  # then writer-finally revokes lease, before outer producer stream cleanup.
  if failure is not None:
   events.append('writer-abort');owner.poisoned=True;state['lease_valid']=False
   stream=state['stream']
   if stream is not None and not stream.closed:
    try:io._cleanup((stream.close,),primary=observed)
    except BaseException as e:observed=e
  else:state['stream'].close()
  stream=state['stream'];tail=state['tail']
  assert path.read_bytes()==before
  assert stream.closed and tail.closed and stream.batches.calls==1
  attempts=state['close_attempts'];stream.close();tail.close();assert state['close_attempts']==attempts
  for fd in (stream.fd,tail.fd,tail.record_fd):
   try:os.fstat(fd)
   except OSError:pass
   else:raise AssertionError('synthetic descriptor leaked')
  return observed,tail._durability.snapshot(),events

baseline=PKG/'compact_mcm.py';candidate=HERE/'candidate/compact_mcm.py'
primary=ValueError('synthetic neighborhood capacity')
error,status,events=run_case(baseline,failure=primary)
assert isinstance(error,io.CleanupFailure) and primary in io._flatten(error.failures) and status['durable_records']==0
checks.append('baseline reproduces capacity primary plus late poisoned-authority CleanupFailure')
primary=ValueError('synthetic neighborhood capacity')
error,status,events=run_case(candidate,failure=primary)
assert error is primary and status['durable_records']==1 and events.index('tail-check')<events.index('writer-abort')
checks.append('candidate flushes/closes while authority live; same primary survives; later owner poison retained')
for failure in (OSError('synthetic fsync/identity refusal'),io.CleanupFailure('synthetic close uncertain'),MemoryError('synthetic fatal')):
 primary=ValueError('synthetic capacity')
 error,status,_=run_case(candidate,failure=primary,close_error=failure)
 if isinstance(failure,MemoryError):assert error is failure
 else:assert isinstance(error,io.CleanupFailure) and failure in io._flatten(error.failures) and primary in io._flatten(error.failures)
 assert status['durable_records']==0
checks.append('actual cleanup refusal/uncertainty/fatal remains fatal and preserves primary evidence')
primary=ValueError('capacity after authority loss');error,status,_=run_case(candidate,failure=primary,poison_early=True)
assert isinstance(error,io.CleanupFailure) and status['durable_records']==0
checks.append('authority already poisoned still refuses durability; no authority bypass')
for syscall in ('fsync','close'):
 primary=ValueError('capacity before syscall failure')
 error,status,_=run_case(candidate,failure=primary,syscall_error=syscall)
 assert isinstance(error,io.CleanupFailure) and primary in io._flatten(error.failures)
 assert any(isinstance(e,OSError) for e in io._flatten(error.failures))
 assert status['durable_records']==(0 if syscall=='fsync' else 1)
checks.append('actual BatchSync fsync and ScoreTail descriptor-close error seams retain fatal cleanup uncertainty')
primary=ValueError('later failure');error,status,_=run_case(candidate,failure=primary,closed_early=True)
assert error is primary and status['durable_records']==1
checks.append('already-closed stream and repeated outer cleanup are idempotent; descriptors close once')
error,status,_=run_case(candidate)
assert error is None and status['durable_records']==1
checks.append('synthetic success path unchanged; retained bytes preserved in every case')
compile(candidate.read_bytes(),str(candidate),'exec')
base=ast.parse(baseline.read_text());new=ast.parse(candidate.read_text())
def compute_node(tree):return next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='compute')
bc=compute_node(base);nc=compute_node(new)
assert len(nc.body)==2 and isinstance(nc.body[0],ast.Nonlocal) and isinstance(nc.body[1],ast.Try)
assert ast.dump(ast.Module(body=bc.body[1:],type_ignores=[]))==ast.dump(ast.Module(body=nc.body[1].body,type_ignores=[]))
nc.body=nc.body[:1]+nc.body[1].body;assert ast.dump(base)==ast.dump(new)
checks.append('AST inverse: only compute error-cleanup wrapper added; all original body and other source unchanged')
result={'status':'passed','profile':'stdlib-only extracted actual compute/stream/tail/owned-IO methods plus synthetic callbacks and temporary scalar bytes; no numerical module imports or empirical claims','checks':checks,'qualification':'Synthetic authority and OS-error injection does not replay actual19 files or certify their durability; current19 uncertainty remains retained.'}
with (HERE/'CHECKS01.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
