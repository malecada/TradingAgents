"""Independent exact-source helpers; synthetic faults and new tiny stdlib children only."""
import ast, dis, hashlib, importlib.util, json, os, pathlib, signal, subprocess, sys
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parent
A=P.parent/'neural-cold-feature-handoff-root-launch-request02-2026-10-03/parent_wait05.py'
assert hashlib.sha256(A.read_bytes()).hexdigest()=='33fb83b106e0c9c75162e6f60db4a2eab8cfb6d7248e9173ff7c49b1da0798a3'
s=importlib.util.spec_from_file_location('review_parent05',A);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
D=P/'parent05-fixtures';D.mkdir(); results=[]; realclose=os.close; realfsync=os.fsync
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
# The sole 04->05 AST change moves joined before any fd acquisition/spawn.
old=ast.parse((A.parent/'parent_wait04.py').read_bytes());new=ast.parse(A.read_bytes())
o=next(x for x in old.body if isinstance(x,ast.FunctionDef) and x.name=='main');n=next(x for x in new.body if isinstance(x,ast.FunctionDef) and x.name=='main')
ot=next(x for x in o.body if isinstance(x,ast.Try));nt=next(x for x in n.body if isinstance(x,ast.Try))
join=ot.finalbody.pop(0);ni=next(i for i,x in enumerate(n.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='joined' for t in x.targets))
assert ast.dump(n.body.pop(ni))==ast.dump(join)
assert ast.dump(old)==ast.dump(new)
actual=ast.parse(A.read_bytes());main=next(x for x in actual.body if isinstance(x,ast.FunctionDef) and x.name=='main');ji=next(i for i,x in enumerate(main.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='joined' for t in x.targets));ti=next(i for i,x in enumerate(main.body) if isinstance(x,ast.Try));assert ji<ti
assert len(main.body[ti].finalbody)==1
code=compile(ast.Module(body=main.body[ti].finalbody,type_ignores=[]),'exact-main-finally05','exec');assert 'BUILD_MAP' not in [x.opname for x in dis.get_instructions(code)]
calls=[];prior=SystemExit('original');ns={'finish_wait':lambda *a:(calls.append(a) or prior),'output':D,'child':child,'primary':prior,'joined':{'source':'synthetic'},'identity':'synthetic','command':[],'fds':[]};exec(code,ns);assert len(calls)==1 and ns['primary'] is prior
results.append('RP3: joined built before protected acquisition/spawn; exact finally calls cleanup preserving prior; only declared AST movement')
# Forced-cleanup branch with actual owned child and an injected first wait
# TimeoutExpired, plus failed TERM. Real KILL and final wait must still occur.
realpopen=subprocess.Popen;realkill=os.killpg;record=[]
class Proxy:
 def __init__(self,*a,**k):self.p=realpopen(*a,**k);self.waits=0
 @property
 def pid(self):return self.p.pid
 @property
 def returncode(self):return self.p.returncode
 def poll(self):return self.p.poll()
 def wait(self,timeout):
  self.waits+=1;record.append(('wait',timeout))
  if self.waits==1:raise subprocess.TimeoutExpired('synthetic firstwait',timeout)
  return self.p.wait(timeout=timeout)
def kill(pid,sig):
 record.append(('kill',int(sig)))
 if sig==signal.SIGTERM:raise OSError('injected TERM failure')
 return realkill(pid,sig)
fatal=MemoryError('original callback')
with patch.object(subprocess,'Popen',Proxy),patch.object(os,'killpg',side_effect=kill):
 child,p=run('forced-kill','import time;time.sleep(10)',fail)
assert p is fatal and child.returncode==-signal.SIGKILL and child.waits==2
assert record==[('kill',15),('wait',150),('kill',9),('wait',5)]
results.append('failed TERM and first wait do not skip real SIGKILL/final wait; exact first fatal retained')
assert not any(x.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for x in sys.modules)
print(json.dumps({'source_sha256':hashlib.sha256(A.read_bytes()).hexdigest(),'results':results,'no_original_main_or_capsule_invoked':True},indent=2))
