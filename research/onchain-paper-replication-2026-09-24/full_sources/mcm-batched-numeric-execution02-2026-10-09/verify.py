"""Two actual-source IO cleanup scopes, no numerical imports."""
import ast,hashlib,json,os,types
from pathlib import Path
P=Path(__file__).resolve().parent
results=[]
for version,path in [('01',P.parent/'mcm-batched-numeric-execution01-2026-10-09/numeric_execution.py'),('02',P/'numeric_execution.py')]:
 tree=ast.parse(path.read_text());tree.body=[n for n in tree.body if not(isinstance(n,ast.ImportFrom) and any(x.name=='batched_numeric_reuse' for x in n.names))];ns={};exec(compile(tree,str(path),'exec'),ns)
 for failure in (True,False):
  root=P/f'read-{version}-{failure}';root.mkdir();fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY);child=os.open('body',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600,dir_fd=fd);os.write(child,b'oversize');os.close(child)
  cleanup=OSError('actual close succeeded; synthetic cleanup failure');closed=[]
  def closing(d):os.close(d);closed.append(d);raise cleanup
  proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});proxy.close=closing;ns['os']=proxy
  try:
   try:ns['read_file'](fd,'body',1 if failure else 8192)
   except BaseException as error:
    row={'version':version,'scope':'read_file','primary_failure':failure,'observed':str(error),'cleanup_primary':error is cleanup,'notes':getattr(error,'__notes__',[])}
    if version=='02' and failure:assert isinstance(error,ValueError) and str(error)=='numeric file extent' and row['notes']
    else:assert error is cleanup
    results.append(row)
   else:raise AssertionError('cleanup-only failure hidden')
  finally:ns['os']=os;os.close(fd)
  for d in closed:
   try:os.fstat(d)
   except OSError:pass
   else:raise AssertionError('descriptor leak')
 for failure in (True,False):
  root=P/f'summary-{version}-{failure}';root.mkdir();(root/'numeric-batches').mkdir();x=object.__new__(ns['NumericExecution']);x.root=root;x.fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY);x.root_pin=ns['sig'](os.fstat(x.fd))[:2];x.batches_fd=os.open(root/'numeric-batches',os.O_RDONLY|os.O_DIRECTORY);x.batches_pin=ns['sig'](os.fstat(x.batches_fd))[:2];x.origins_fd=os.open(root/'numeric-origins.bin',os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);x.origin_sig=ns['sig'](os.fstat(x.origins_fd))
  x.memo=types.SimpleNamespace(end_batch=lambda:None,counters={});x.ordinal=1;x.buffer=bytearray(ns['RECORD'].pack(0,0));x.batch=0;x.batch_computed=1;x.batch_reused=0;x.batch_elapsed=0.;x.receipts=hashlib.sha256();x.summary_bytes=0;x.max_summary_bytes=8192;x.max_origin_bytes=9
  primary=OSError('synthetic summary write failure');cleanup=OSError('actual close succeeded; synthetic cleanup failure');opened=[];closed=[];write_all=ns['write_all']
  def opening(*a,**kw):d=os.open(*a,**kw);opened.append(d);return d
  def closing(d):os.close(d);closed.append(d);raise cleanup
  def writing(d,body):
   if failure and d in opened:raise primary
   return write_all(d,body)
  proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});proxy.open=opening;proxy.close=closing;ns['os']=proxy;ns['write_all']=writing
  try:
   try:x._complete_batch()
   except BaseException as error:
    row={'version':version,'scope':'summary','primary_failure':failure,'observed':str(error),'primary_preserved':error is primary,'cleanup_primary':error is cleanup,'notes':getattr(error,'__notes__',[]),'batch_credit':x.batch}
    if version=='02' and failure:assert error is primary and row['notes']
    else:assert error is cleanup
    assert x.batch==0;results.append(row)
   else:raise AssertionError('cleanup failure hidden')
  finally:
   ns['os']=os;ns['write_all']=write_all
   for d in (x.origins_fd,x.batches_fd,x.fd):os.close(d)
  assert closed==opened
  for d in opened:
   try:os.fstat(d)
   except OSError:pass
   else:raise AssertionError('descriptor leak')
assert 'numpy' not in __import__('sys').modules
(P/'RESULT01.json').write_text(json.dumps({'status':'RED01_GREEN02','cases':results,'affinity':sorted(os.sched_getaffinity(0)),'numerical_imports':False,'source_sha256':hashlib.sha256((P/'numeric_execution.py').read_bytes()).hexdigest()},indent=2)+'\n');print('PASS: two baseline defects reproduced, both corrected, cleanup-only failures refuse, all inner FDs closed')
