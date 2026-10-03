"""Exact parent helper counterexamples; safe tiny new stdlib children only."""
import ast,hashlib,importlib.util,json,os,pathlib,signal,subprocess,sys,time,types
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parent;A=P.parent/'neural-cold-feature-handoff-root-launch-request02-2026-10-03/parent_wait02.py'
s=importlib.util.spec_from_file_location('review_parent02',A);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
result={'parent_source_sha256':hashlib.sha256(A.read_bytes()).hexdigest(),'no_actual_parent_main_or_CAP_invocation':True,'counterexamples':[]}
# Actual writer: ordinary body first, real descriptor closed once but injected
# close MemoryError suppressed. The file is an exclusive synthetic review body.
d=P/'writer-fixtures';d.mkdir();realclose=os.close;seen=[];first=ValueError('ordinary body');later=MemoryError('first actual fatal at close')
def close(fd):seen.append(fd);realclose(fd);raise later
with patch.object(os,'write',side_effect=first),patch.object(os,'close',side_effect=close):
 try:m.write(d,'ordinary-then-fatal.json',{})
 except BaseException as got:assert got is first
 else:raise AssertionError('expected error')
assert len(seen)==1
result['counterexamples'].append({'case':'ordinary-body-later-fatal-close','observed':'original ValueError; later MemoryError suppressed','fd_closed_once':True})
# Directory fsync fatal is replaced by a subsequent ordinary close error.
realfsync=os.fsync;fsyncs=[];closed=[];fatal=MemoryError('directory fsync first');ordinary=OSError('directory close later')
def fsync(fd):
 fsyncs.append(fd)
 if len(fsyncs)==2:raise fatal
 return realfsync(fd)
def close(fd):
 closed.append(fd);realclose(fd)
 if len(closed)==2:raise ordinary
with patch.object(os,'fsync',side_effect=fsync),patch.object(os,'close',side_effect=close):
 try:m.write(d,'directory-fatal.json',{})
 except BaseException as got:assert got is ordinary
 else:raise AssertionError('expected error')
assert len(closed)==2
result['counterexamples'].append({'case':'directory-fsync-fatal-later-ordinary-close','observed':'OSError replaces exact MemoryError','all_fds_closed_once':True})
# Real wait_owned callback failure preserves first fatal and normally reaps.
command=[sys.executable,'-B','-c','import time;time.sleep(10)'];first=MemoryError('on_child');children=[]
def on_child(child):children.append(child);raise first
with (P/'tiny.stdout').open('xb') as out,(P/'tiny.stderr').open('xb') as err:
 child,primary=m.wait_owned(command,P,out,err,on_child,lambda:None,seconds=3)
assert primary is first and child.returncode is not None and not pathlib.Path('/proc',str(child.pid)).exists()
result['normal_on_child_fatal_cleanup']={'pid':child.pid,'exit':child.returncode,'absent':True}
# Signal failure must not skip independent wait/forced cleanup. It currently
# does. This test kills/reaps only its own new child in independent harness finally.
children=[];first=MemoryError('on_child before stop fault')
with (P/'stop-fault.stdout').open('xb') as out,(P/'stop-fault.stderr').open('xb') as err:
 try:
  with patch.object(os,'killpg',side_effect=OSError('synthetic signal failure')):
   child,primary=m.wait_owned(command,P,out,err,on_child,lambda:None,seconds=3)
  live=child.poll() is None
  assert primary is first and live and pathlib.Path('/proc',str(child.pid)).exists()
  result['counterexamples'].append({'case':'signal-failure-skips-wait','pid':child.pid,'still_alive_when_wait_owned_returned':True,'primary_identity_preserved':True})
 finally:
  for child in children:
   if child.poll() is None:child.kill()
   child.wait(timeout=3)
   assert not pathlib.Path('/proc',str(child.pid)).exists()
# Actual terminal statements after wait_owned, with a real reaped tiny child
# represented by its observed PID/returncode. Publication failure displaces the
# already-selected fatal; this is AST-only, not parent main/claim authority.
tree=ast.parse(A.read_bytes());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');block=next(n for n in main.body if isinstance(n,ast.With));i=next(i for i,n in enumerate(block.body) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='wait_owned')
first=MemoryError('original callback fatal');second=OSError('wait receipt write failure')
ns={'child':child,'primary':first,'write':lambda *a:(_ for _ in ()).throw(second),'output':P,'identity':'synthetic-review','request':{'source':'ab'*20,'output_parent':str(P)},'command':command,'request_ref':{'synthetic':True},'Path':pathlib.Path,'select':m.select,'require':m.require}
try:exec(compile(ast.Module(body=block.body[i+1:],type_ignores=[]),'actual-parent-post-wait','exec'),ns)
except BaseException as got:assert got is second
else:raise AssertionError('expected publication failure')
result['counterexamples'].append({'case':'post-wait-publication-masks-existing-fatal','observed':'OSError replaces MemoryError'})
# Actual SIGTERM cancellation path with a fresh tiny child.
children=[];sent=[];handlers={s:signal.getsignal(s) for s in (signal.SIGTERM,signal.SIGINT)}
def remember(child):children.append(child)
def cancel():
 if not sent:sent.append(True);os.kill(os.getpid(),signal.SIGTERM)
with (P/'cancel.stdout').open('xb') as out,(P/'cancel.stderr').open('xb') as err:child,primary=m.wait_owned(command,P,out,err,remember,cancel,seconds=3)
assert isinstance(primary,InterruptedError) and child.returncode is not None and not pathlib.Path('/proc',str(child.pid)).exists()
assert all(signal.getsignal(s)==h for s,h in handlers.items())
result['actual_SIGTERM_cleanup']={'pid':child.pid,'exit':child.returncode,'absent':True,'handlers_restored':True}
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print(json.dumps(result,indent=2))
