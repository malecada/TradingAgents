import json,os,sys
from pathlib import Path
import parent01 as P
from supervisor01 import supervise
H=Path(__file__).resolve().parent;checks=[];owned=[]
def ok(n,v):assert v,n;checks.append(n)
def refuse(n,f):
 try:f()
 except ValueError:checks.append(n);return
 raise AssertionError(n+' accepted')
q=json.loads((H/'REQUEST_TEMPLATE01.json').read_bytes())
refuse('unreleased template refuses',lambda:P.validate_release(q))
for key in ('identity','source','final_review','runtime_mapping'):
 changed=dict(q,status='RELEASED_ONE_USE_FINANCIAL_PARENT');changed[key]=None
 refuse('null actual proof '+key,lambda:P.validate_release(changed))
for label,code,expected in [('complete',"import sys;print('out');print('err',file=sys.stderr)",0),('failed',"import sys;print('planned failure bytes');sys.exit(7)",7)]:
 d=H/('tiny-'+label);d.mkdir(mode=0o700);r=supervise([sys.executable,'-B','-c',code],H,os.environ.copy(),d,3,on_spawn=lambda p:owned.append(p))
 ok(label+' actual exit retained',r['exit_code']==expected)
 ok(label+' PID reaped',not Path('/proc',str(r['pid'])).exists())
 ok(label+' raw output retained',(d/'stdout').read_bytes()!=b'')
 refuse(label+' one-use log namespace',lambda:supervise([sys.executable,'-c','pass'],H,os.environ.copy(),d,3)) if False else None
 # O_EXCL's concrete FileExistsError is the required nonreplay refusal.
 try:supervise([sys.executable,'-c','pass'],H,os.environ.copy(),d,3)
 except FileExistsError:checks.append(label+' reused namespace refuses')
 else:raise AssertionError('reused namespace')
d=H/'tiny-timeout';d.mkdir(mode=0o700)
refuse('actual deadline terminates child',lambda:supervise([sys.executable,'-B','-c','import time;time.sleep(30)'],H,os.environ.copy(),d,.15,on_spawn=lambda p:owned.append(p)))
ok('timeout child reaped',owned[-1].poll() is not None and not Path('/proc',str(owned[-1].pid)).exists())
d=H/'tiny-fatal';d.mkdir(mode=0o700);fatal=KeyboardInterrupt('first actual synthetic fatal')
def watch():raise fatal
try:supervise([sys.executable,'-B','-c','import time;time.sleep(30)'],H,os.environ.copy(),d,3,watch,on_spawn=lambda p:owned.append(p))
except BaseException as actual:ok('first fatal object preserved',actual is fatal)
else:raise AssertionError('fatal lost')
ok('fatal child reaped',owned[-1].poll() is not None and not Path('/proc',str(owned[-1].pid)).exists())
(H/'CHECKS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'actual_owned_child_pids':[p.pid for p in owned],'all_children_reaped':all(p.poll() is not None for p in owned),'native_or_numerical':False},indent=2)+'\n');print(len(checks),'checks passed')
