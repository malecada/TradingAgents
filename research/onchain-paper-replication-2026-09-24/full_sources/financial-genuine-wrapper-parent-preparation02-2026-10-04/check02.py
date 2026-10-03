import ctypes,json,os,signal,subprocess,sys
from pathlib import Path
from descendants01 import OwnedTree,pin
H=Path(__file__).resolve().parent;checks=[]
def ok(n,v):assert v,n;checks.append(n)
lib=ctypes.CDLL(None);before=ctypes.c_int();assert lib.prctl(37,ctypes.byref(before),0,0,0)==0
owned=OwnedTree();owned.begin();child=None
try:
 child=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(30)']);rows=owned.scan();actual=rows[child.pid];bad={child.pid:{**actual,'ticks':'wrong-start'}}
 try:owned.signal(bad,signal.SIGTERM)
 except ValueError:checks.append('foreign PID-start refusal')
 else:raise AssertionError('foreign start accepted')
 ok('rejected signal leaves actual child alive',child.poll() is None)
 cleanup=owned.drain(child);ok('actual original child then drained',not cleanup['remaining_original_identities'] and child.poll() is not None)
finally:
 if child is not None and child.poll() is None:child.kill();child.wait()
 owned.close()
after=ctypes.c_int();assert lib.prctl(37,ctypes.byref(after),0,0,0)==0
ok('prior subreaper state restored',before.value==after.value)
(H/'CHECKS02.json').write_text(json.dumps({'checks':checks,'count':len(checks),'actual_pid':child.pid,'cleanup':cleanup},indent=2)+'\n');print(len(checks),'checks passed')
