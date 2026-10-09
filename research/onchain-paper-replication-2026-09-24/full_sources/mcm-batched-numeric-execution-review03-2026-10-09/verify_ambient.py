"""Enclosing-except cleanup-only failures: actual source, metadata only."""
import ast,hashlib,json,os,types
from pathlib import Path
import resource,signal
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
P=Path(__file__).resolve().parent;C=P.parent/'mcm-batched-numeric-execution03-2026-10-09';results=[]
def load(path):
 tree=ast.parse(path.read_text());tree.body=[n for n in tree.body if not(isinstance(n,ast.ImportFrom) and any(x.name=='batched_numeric_reuse' for x in n.names))];ns={};exec(compile(tree,str(path),'exec'),ns);return ns
def complete(ns,root):
 root.mkdir();(root/'numeric-batches').mkdir();x=object.__new__(ns['NumericExecution']);x.root=root;x.fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY);x.root_pin=ns['sig'](os.fstat(x.fd))[:2];x.batches_fd=os.open(root/'numeric-batches',os.O_RDONLY|os.O_DIRECTORY);x.batches_pin=ns['sig'](os.fstat(x.batches_fd))[:2];x.origins_fd=os.open(root/'numeric-origins.bin',os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);x.origin_sig=ns['sig'](os.fstat(x.origins_fd))
 x.memo=types.SimpleNamespace(end_batch=lambda:None,counters={},active=False);x.ordinal=1;x.cells=1;x.batch_cells=1;x.batches=1;x.buffer=bytearray(ns['RECORD'].pack(0,0));x.batch=0;x.batch_computed=1;x.batch_reused=0;x.computed=1;x.reused=0;x.batch_elapsed=0.;x.elapsed_seconds=0.;x.receipts=hashlib.sha256();x.summary_hash=hashlib.sha256();x.summary_inventory=hashlib.sha256();x.origin_hash=hashlib.sha256();x.summary_bytes=0;x.max_summary_bytes=8192;x.max_origin_bytes=9;x.closed=x.finished=x.poisoned=False
 return x
for version,path in [('03',C/'numeric_execution.py')]:
 ns=load(path)
 for scope in ('read','summary','verify'):
  root=P/f'ambient-{version}-{scope}';x=complete(ns,root)
  if scope=='read':
   child=os.open(root/'valid',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(child,b'ok');os.close(child)
  elif scope=='verify':x._complete_batch();binding=x.finish()
  cleanup=OSError('synthetic close failure after real close');opened=[];targets=[];closed=[]
  def opening(name,*a,**kw):
   d=os.open(name,*a,**kw);opened.append(d)
   if (scope=='read' and name=='valid') or (scope=='summary' and name=='000000000000.json' and a[0]&os.O_WRONLY) or (scope=='verify' and name=='numeric-origins.bin'):targets.append(d)
   return d
  def closing(d):
   os.close(d);closed.append(d)
   if d in targets:raise cleanup
  proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});proxy.open=opening;proxy.close=closing;ns['os']=proxy
  ambient=RuntimeError('unrelated caller exception');observed=None;success=False
  try:
   try:raise ambient
   except RuntimeError:
    try:
     if scope=='read':ns['read_file'](x.fd,'valid',8192)
     elif scope=='summary':x._complete_batch()
     else:ns['verify'](root,binding)
     success=True
    except BaseException as error:observed=error
  finally:
   ns['os']=os
   for d in (x.origins_fd,x.batches_fd,x.fd):os.close(d)
  if version=='02':assert success and observed is None and getattr(ambient,'__notes__',None)
  else:assert observed is cleanup and not success and not getattr(ambient,'__notes__',None)
  if scope=='summary':assert x.batch==(1 if version=='02' else 0)
  assert opened and set(opened)<=set(closed)
  for d in opened:
   try:os.fstat(d)
   except OSError:pass
   else:raise AssertionError('fixture descriptor leaked')
  results.append({'version':version,'scope':scope,'returned_success':success,'cleanup_exception_propagated':observed is cleanup,'ambient_notes':getattr(ambient,'__notes__',[]),'batch_credit':x.batch})
assert 'numpy' not in __import__('sys').modules
assert 'sys' not in (C/'numeric_execution.py').read_text()
(P/'AMBIENT_RESULT01.json').write_text(json.dumps({'status':'GREEN03_PRIOR_RED_REUSED','cases':results,'affinity':sorted(os.sched_getaffinity(0)),'numerical_imports':False},indent=2)+'\n');print('PASS: all three ambient exception cleanup-only errors refused03; no ambient notes or descriptor leaks')
