import ast,ctypes,json,os,sys
from pathlib import Path
from supervisor01 import supervise
from descendants01 import pin
import parent01 as P
H=Path(__file__).resolve().parent;checks=[];outcomes=[]
def ok(n,v):assert v,n;checks.append(n)
def case(name,code,seconds=3,watch=lambda:None):
 d=H/(name+'-grace04');d.mkdir(mode=0o700);result=None;error=None
 try:result=supervise([sys.executable,'-B','-c',code],H,os.environ.copy(),d,seconds,watch)
 except BaseException as e:error=e
 cleanup=json.loads((d/'owned-tree-cleanup.json').read_bytes())
 ok(name+' all original descendants absent',all(pin(r['pid']) is None or pin(r['pid'])['ticks']!=r['ticks'] for r in cleanup['owned_pid_start_records']))
 ok(name+' no remaining original identities',cleanup['remaining_original_identities']==[])
 outcomes.append({'name':name,'result':result,'error_type':None if error is None else type(error).__name__,'cleanup':cleanup})
 return result,error,cleanup
r,e,c=case('tiny-exit7',"import sys;print('actual failure');sys.exit(7)")
ok('actual exit7 preserved',e is None and r['exit_code']==7)
r,e,c=case('tiny-orphan',"import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);print(p.pid,flush=True);time.sleep(.15);sys.exit(7)")
ok('orphan child captured',len(c['owned_pid_start_records'])>=2 and c['reaped_descendants'])
ok('leader exit7 remains actual',e is None and r['exit_code']==7)
code="""import os,time,signal
p=os.fork()
if p==0:
 os.setsid()
 q=os.fork()
 if q==0:
  signal.signal(signal.SIGTERM,signal.SIG_IGN)
  print('grandchild',os.getpid(),flush=True)
  time.sleep(30)
  os._exit(0)
 os._exit(0)
time.sleep(.2)
os._exit(0)
"""
r,e,c=case('tiny-double-fork',code)
ok('doublefork setsid drainage',e is None and len(c['owned_pid_start_records'])>=2 and len(c['reaped_descendants'])>=1)
r,e,c=case('tiny-timeout',"import subprocess,sys,time;subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);time.sleep(30)",.2)
ok('deadline retained',isinstance(e,ValueError))
fatal=KeyboardInterrupt('first fatal')
def fail():raise fatal
r,e,c=case('tiny-first-fatal','import time;time.sleep(30)',watch=fail)
ok('same firstfatal object',e is fatal)
q=json.loads((H/'REQUEST_TEMPLATE01.json').read_bytes())
try:P.validate_release(q)
except ValueError:checks.append('draft refused')
else:raise AssertionError('draft released')
# Source-order proof on exact preserved original body, without executing resources.
raw=(H/'original-resources.py').read_bytes();tree=ast.parse(raw);f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='guarded_run')
text=raw.decode();segment=ast.get_source_segment(text,f)
ok('original guarded source has no deletion of intent',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('unlink','remove','rmdir') for n in ast.walk(f)))
ok('pre-dispatch verifying phase publishes',"state['phase'] = 'verifying_cgroup'\n        publish()\n        args = ['systemd-run'" in segment)
ok('native publication atomic original record',"_native_atomic(receipt/'live.json',state,native_io)" in segment)
ok('unique unit precedes publication and launch',segment.index('unit = f\'onchain-replication-')<segment.index('def publish():')<segment.index('subprocess.run(args, check=True'))
(H/'CHECKS04.json').write_text(json.dumps({'checks':checks,'count':len(checks),'outcomes':outcomes,'native_commands_executed':False,'source_interface_mutated':False},sort_keys=True,indent=2)+'\n');print(len(checks),'checks passed')
