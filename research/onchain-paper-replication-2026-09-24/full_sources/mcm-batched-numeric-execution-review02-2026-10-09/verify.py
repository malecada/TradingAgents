"""Actual-source metadata IO cleanup failure; no arrays or authority objects."""
import ast,hashlib,json,os,resource,signal,types
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent;C=H.parent/'mcm-batched-numeric-execution02-2026-10-09/numeric_execution.py'
tree=ast.parse(C.read_text());tree.body=[n for n in tree.body if not(isinstance(n,ast.ImportFrom) and any(x.name=='batched_numeric_reuse' for x in n.names))]
ns={};exec(compile(tree,str(C),'exec'),ns)
root=H/'fixture';root.mkdir();fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY);child=os.open('body',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600,dir_fd=fd);os.write(child,b'oversize');os.close(child)
original_os=ns['os'];trace=[];cleanup=OSError('synthetic descriptor close failure after actual close')
def close(child):
 os.close(child);trace.append(child);raise cleanup
proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});proxy.close=close
results=[]
try:
 for injection in (False,True):
  ns['os']=proxy if injection else original_os
  try:ns['read_file'](fd,'body',1)
  except BaseException as error:results.append({'injected_close_failure':injection,'type':type(error).__name__,'message':str(error),'is_cleanup':error is cleanup})
  else:raise AssertionError('oversize admitted')
finally:ns['os']=original_os;os.close(fd)
assert results[0]['type']=='ValueError' and results[0]['message']=='numeric file extent'
assert not results[1]['is_cleanup'] and results[1]['message']=='numeric file extent'
# Actual _complete_batch, synthetic metadata-only memo. No numeric execution.
root=H/'summary-fixture';root.mkdir();(root/'numeric-batches').mkdir();x=object.__new__(ns['NumericExecution'])
x.root=root;x.fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY);x.root_pin=ns['sig'](os.fstat(x.fd))[:2];x.batches_fd=os.open(root/'numeric-batches',os.O_RDONLY|os.O_DIRECTORY);x.batches_pin=ns['sig'](os.fstat(x.batches_fd))[:2]
x.origins_fd=os.open(root/'numeric-origins.bin',os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);x.origin_sig=ns['sig'](os.fstat(x.origins_fd))
x.memo=types.SimpleNamespace(end_batch=lambda:None,counters={});x.ordinal=1;x.buffer=bytearray(ns['RECORD'].pack(0,0));x.batch=0;x.batch_computed=1;x.batch_reused=0;x.batch_elapsed=0.;x.receipts=hashlib.sha256();x.summary_bytes=0;x.max_summary_bytes=8192;x.max_origin_bytes=9
primary=OSError('synthetic summary write failure');opened=[];original_write_all=ns['write_all']
def opening(*a,**kw):
 d=os.open(*a,**kw);opened.append(d);return d
def writing(d,body):
 if d in opened:raise primary
 return original_write_all(d,body)
proxy.open=opening;ns['os']=proxy;ns['write_all']=writing
try:
 try:x._complete_batch()
 except BaseException as error:
  results.append({'case':'summary-write-and-close','primary_preserved':error is primary,'observed':str(error),'summary_credit':x.batch})
 else:raise AssertionError('write failure hidden')
finally:
 ns['os']=original_os;ns['write_all']=original_write_all
 for d in (x.origins_fd,x.batches_fd,x.fd):os.close(d)
assert results[-1]['primary_preserved'] is True and results[-1]['summary_credit']==0
for d in opened:
 try:os.fstat(d)
 except OSError:pass
 else:raise AssertionError('test FD not actually closed')
out={'synthetic_metadata_only':True,'source_sha256':hashlib.sha256(C.read_bytes()).hexdigest(),'results':results,'arrays_or_authority_objects':False,'affinity':sorted(os.sched_getaffinity(0))}
(H/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
