"""Independent exact-source helpers; synthetic faults and new tiny stdlib children only."""
import ast, dis, hashlib, importlib.util, json, os, pathlib, signal, subprocess, sys
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parent
A=P.parent/'neural-cold-feature-handoff-root-launch-request02-2026-10-03/parent_wait04.py'
assert hashlib.sha256(A.read_bytes()).hexdigest()=='b570c7dd5e95c64ce8681ddde963b0657c4815cae85029dc4411070a069aa1d2'
s=importlib.util.spec_from_file_location('review_parent04',A);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
D=P/'parent04-fixtures';D.mkdir(); results=[]; realclose=os.close; realfsync=os.fsync
first=ValueError('body');fatal=MemoryError('close');closed=[]
def close(fd):closed.append(fd);realclose(fd);raise fatal
with patch.object(os,'write',side_effect=first),patch.object(os,'close',side_effect=close):
 try:m.write(D,'file.json',{})
 except BaseException as e:assert e is fatal
 else:raise AssertionError
assert len(closed)==1;results.append('ordinary body then fatal file close: exact fatal retained, once')
closed=[];synced=[];fatal=MemoryError('dirfsync')
def fsync(fd):
 synced.append(fd)
 if len(synced)==2:raise fatal
 return realfsync(fd)
def close(fd):
 closed.append(fd);realclose(fd)
 if len(closed)==2:raise OSError('dirclose')
with patch.object(os,'fsync',side_effect=fsync),patch.object(os,'close',side_effect=close):
 try:m.write(D,'directory.json',{})
 except BaseException as e:assert e is fatal
 else:raise AssertionError
assert len(closed)==2;results.append('directory fatal then ordinary close: exact fatal retained, both once')
# Actual fresh, short-lived children; no resource/native/research commands.
handlers={s:signal.getsignal(s) for s in (signal.SIGTERM,signal.SIGINT)};children=[]
def run(case, code, callback, monitor=lambda:None, signal_fault=False):
 with (D/(case+'.stdout')).open('xb') as out,(D/(case+'.stderr')).open('xb') as err:
  if signal_fault:
   with patch.object(os,'killpg',side_effect=OSError('injected TERM failure')):
    child,primary=m.wait_owned([sys.executable,'-B','-c',code],D,out,err,callback,monitor,3)
  else:child,primary=m.wait_owned([sys.executable,'-B','-c',code],D,out,err,callback,monitor,3)
 children.append(child);assert child.returncode is not None and not pathlib.Path('/proc',str(child.pid)).exists()
 assert all(signal.getsignal(s)==v for s,v in handlers.items())
 results.append({'case':case,'pid':child.pid,'exit':child.returncode,'absent':True,'handlers_restored':True})
 return child,primary
fatal=MemoryError('callback')
def fail(c):raise fatal
child,p=run('callback','import time;time.sleep(10)',fail);assert p is fatal
child,p=run('failed-signal-wait','import time;time.sleep(.05)',fail,signal_fault=True);assert p is fatal and child.returncode==0
sent=[]
def cancel():
 if not sent:sent.append(True);os.kill(os.getpid(),signal.SIGTERM)
child,p=run('cancel','import time;time.sleep(10)',lambda c:None,cancel);assert isinstance(p,InterruptedError)
# Actual finish helper independently closes both fd and tries both receipts.
fatal=MemoryError('prior');calls=[];fds=[os.open(D/('stream'+str(i)),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600) for i in range(2)];closed=[]
def close(fd):closed.append(fd);realclose(fd);raise OSError('close error')
def write(*args):calls.append(args[1]);raise SystemExit('later fatal')
with patch.object(os,'close',side_effect=close),patch.object(m,'write',side_effect=write):
 p=m.finish_wait(D,child,fatal,{'source':'synthetic','request_reference':{},'output_parent':str(D)},'synthetic',[],fds)
assert p is fatal and closed==fds and calls==['wait.json','failure.json'];results.append('postwait first fatal retained, both fd close and both publication attempts')
# Exact main finally with a plain dict. Opcode fault simulates MemoryError in
# mapping allocation; no parent main, argv parsing, capsule or process launch.
tree=ast.parse(A.read_bytes());main=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='main');t=next(x for x in main.body if isinstance(x,ast.Try));code=compile(ast.Module(body=t.finalbody,type_ignores=[]),'exact-main-finally04','exec');ops={x.offset:x.opname for x in dis.get_instructions(code)};calls=[];original=SystemExit('original fatal');later=MemoryError('mapping allocation');ns={'request':{'source':'synthetic'},'request_ref':{},'primary':original,'finish_wait':lambda *a:calls.append(a),'output':D,'child':child,'identity':'synthetic','command':[],'fds':[]}
def trace(frame,event,arg):
 if frame.f_code is code:
  frame.f_trace_opcodes=True
  if event=='opcode' and ops[frame.f_lasti]=='BUILD_MAP':raise later
 return trace
try:
 sys.settrace(trace)
 try:exec(code,ns)
 except BaseException as e:assert e is later
 else:raise AssertionError
finally:sys.settrace(None)
assert not calls and ns['primary'] is original
results.append({'counterexample':'main final mapping allocation precedes finish_wait','injected_at':'actual BUILD_MAP opcode, plain request dict','observed':'later MemoryError replaces original SystemExit; finish_wait not called','qualification':'synthetic allocation error, no real exhausted memory'})
assert not any(x.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for x in sys.modules)
print(json.dumps({'source_sha256':hashlib.sha256(A.read_bytes()).hexdigest(),'results':results,'no_original_main_or_capsule_invoked':True},indent=2))
