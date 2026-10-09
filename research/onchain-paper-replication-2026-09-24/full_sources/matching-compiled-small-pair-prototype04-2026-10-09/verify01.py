"""Stdlib real-FD lifecycle injections; not a new numerical/kernel sealing proof."""
import ast,os,sys,resource,signal,time,json,hashlib,types,stat
from pathlib import Path
P=Path(__file__).resolve().parent;OLD=P.parent/'matching-compiled-small-pair-prototype03-2026-10-09'
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)]:resource.setrlimit(k,(v,v))
signal.alarm(30);started=time.monotonic_ns();(P/'LIMITER01.json').write_text(json.dumps({'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'alarm_seconds':30},indent=2)+'\n')
assert os.sched_getaffinity(0)=={3}
body=P/'synthetic-body';body.write_bytes(b'opaque lifecycle fixture')
class OS:
 def __init__(self,fail):self.fail=fail;self.fds={};self.calls=[];self.errors={k:OSError('injected '+k+' close') for k in fail}
 def __getattr__(self,n):return getattr(os,n)
 def open(self,*a,**k):
  fd=os.open(*a,**k);self.fds['source']=fd;return fd
 def close(self,fd):
  kind=next(k for k,v in self.fds.items() if v==fd);self.calls.append(kind)
  if kind in self.fail:raise self.errors[kind]
  os.close(fd)
 def memfd(self):
  fd=os.open(P/'synthetic-memfd',os.O_RDWR|os.O_CREAT|os.O_TRUNC,0o600);self.fds['memfd']=fd;return fd
 def open_now(self):
  result=[]
  for kind,fd in self.fds.items():
   try:os.fstat(fd)
   except OSError:pass
   else:result.append(kind)
  return result
 def cleanup_fixture(self):
  for fd in self.fds.values():
   try:os.close(fd)
   except OSError:pass

def functions(path):
 t=ast.parse(path.read_text());return ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('_load_sealed','close')],type_ignores=[])
def loader(path,fail=(),primary=None):
 proxy=OS(fail);function=types.SimpleNamespace()
 def cdll(*args,**kwargs):
  if primary is not None:raise primary
  return types.SimpleNamespace(small_lse=function)
 ctypes=types.SimpleNamespace(c_double=object(),sizeof=lambda x:8,CDLL=cdll,c_int=int)
 ns={'os':proxy,'sys':types.SimpleNamespace(platform='linux',byteorder='little'),'platform':types.SimpleNamespace(machine=lambda:'x86_64'),'ctypes':ctypes,'stat':stat,'fcntl':types.SimpleNamespace(fcntl=lambda fd,command,*args:15 if command==1034 else 0),'_F_ADD_SEALS':1033,'_F_GET_SEALS':1034,'_F_SEAL_WRITE':8,'_F_SEAL_GROW':4,'_F_SEAL_SHRINK':2,'_F_SEAL_SEAL':1,'_PATH':body,'_EXPECTED':hashlib.sha256(body.read_bytes()).hexdigest(),'hashlib':hashlib,'_new_memfd':proxy.memfd,'_ARGS':[],'_fn':object(),'_fd':None,'_close_error':None}
 exec(compile(functions(path),str(path),'exec'),ns)
 return ns,proxy
checks=[]
def case(label,path,fail=(),primary=None):
 ns,proxy=loader(path,fail,primary);result=error=None
 try:
  try:result=ns['_load_sealed']()
  except BaseException as e:error=e
  record={'case':label,'close_attempts':list(proxy.calls),'remaining_real_fds':proxy.open_now(),'returned_backend':result is not None,'error_type':type(error).__name__ if error else None,'primary_preserved':error is primary if primary else None,'notes':getattr(error,'__notes__',[])}
  checks.append(record)
  return ns,proxy,result,error,record
 finally:proxy.cleanup_fixture()
# Original03 concrete RED: successful construction transfers too early, leaks provisional memfd.
_,_,_,e,r=case('baseline_source_close_RED',OLD/'compiled_small_lse.py',('source',));assert r['close_attempts']==['source'] and r['remaining_real_fds']==['source','memfd']
primary=RuntimeError('unexpected original primary')
_,_,_,e,r=case('baseline_primary_masked_RED',OLD/'compiled_small_lse.py',('source',),primary);assert e is not primary and r['close_attempts']==['source']
new=P/'compiled_small_lse.py'
_,_,res,e,r=case('success_transfer',new);assert res is not None and e is None and r['close_attempts']==['source'] and r['remaining_real_fds']==['memfd']
_,proxy,res,e,r=case('source_close_failure',new,('source',));assert res is None and e is proxy.errors['source'] and r['close_attempts']==['source','memfd'] and r['remaining_real_fds']==['source']
primary=RuntimeError('unexpected primary')
_,proxy,res,e,r=case('both_cleanup_fail_primary_preserved',new,('source','memfd'),primary);assert e is primary and r['close_attempts']==['source','memfd'] and r['remaining_real_fds']==['source','memfd']
_,proxy,res,e,r=case('both_cleanup_fail_no_primary',new,('source','memfd'));assert e is proxy.errors['source'] and r['close_attempts']==['source','memfd'] and res is None
primary=OSError('unsupported loader')
_,proxy,res,e,r=case('owned_close_fail_preserves_unsupported_primary',new,('memfd',),primary);assert e is primary and r['close_attempts']==['source','memfd'] and r['remaining_real_fds']==['memfd']
_,_,res,e,r=case('unsupported_clean_fallback',new,(),OSError('unsupported loader'));assert res is None and e is None and r['remaining_real_fds']==[]
primary=RuntimeError('unexpected primary clean')
_,_,res,e,r=case('unexpected_primary_clean',new,(),primary);assert e is primary and r['remaining_real_fds']==[]
for fail in (False,True):
 ns,proxy=loader(new,('memfd',) if fail else ());fd=proxy.memfd();ns['_fd']=fd
 errors=[]
 try:
  for _ in range(2):
   try:ns['close']()
   except BaseException as e:errors.append(e)
  assert ns['_fn'] is None and ns['_fd'] is None and proxy.calls==['memfd']
  if fail:assert len(errors)==2 and errors[0] is errors[1] is proxy.errors['memfd'] and proxy.open_now()==['memfd']
  else:assert errors==[] and proxy.open_now()==[]
  checks.append({'case':'terminal_close_failure_no_retry' if fail else 'terminal_close_idempotent','close_attempts':proxy.calls,'remaining_real_fds':proxy.open_now(),'disabled':True,'same_error_on_repeat':fail})
 finally:proxy.cleanup_fixture()
# Prove all code outside two lifecycle functions is identical to03.
def outside(path):
 t=ast.parse(path.read_text());t.body=[n for n in t.body if not(isinstance(n,ast.FunctionDef) and n.name in ('_load_sealed','close')) and not(isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='_close_error' for v in n.targets))];return ast.dump(t,include_attributes=False)
assert outside(new)==outside(OLD/'compiled_small_lse.py')
for n in ['matching_annealing.py','reduction.c','reduction.so']:assert (P/n).read_bytes()==(OLD/n).read_bytes()
result={'status':'PASS_LIFECYCLE_ONLY','checks':checks,'outside_lifecycle_AST_inverse':True,'numerical_and_binary_bodies_unchanged':True,'elapsed_ns':time.monotonic_ns()-started,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'qualification':'Actual real-FD open/close states; synthetic loader/seal stand-ins only. Failed closes not credited as closed; harness explicitly releases residual fixture descriptors afterward.'};(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
