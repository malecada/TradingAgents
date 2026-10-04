"""Owned stdlib filesystem/process controls; never calls a recovery entry point."""
import ast,hashlib,importlib.util,json,os,queue,stat,sys,threading,time,traceback,types
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
W=load('newwatch',D/'watch01.py');O=load('oldwatch',D/'watch.original03.py')
ROOT=D/'owned01';ROOT.mkdir()
rows=[]
def record(name,**data):
 rows.append(dict(name=name,**data));(D/'CONTROLS01.json').write_text(json.dumps(rows,indent=2)+'\n')
def req(v,m):
 if not v:raise AssertionError(m)
def tree(name):
 p=ROOT/name;p.mkdir();return p
def trial(fn):
 try:return {'returned':fn()},None
 except BaseException as e:return {'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()},e

def interleave(module,label):
 root=tree(label);(root/'opaque').write_bytes(b'bounded opaque body')
 requests=queue.Queue();responses=queue.Queue();events=[];original=Path.lstat;root_calls=0;deadline=None
 def publisher():
  nonlocal deadline
  while True:
   n=requests.get()
   if n is None:return
   if deadline is None:deadline=time.monotonic()+.05
   if time.monotonic()<deadline:
    before=original(root);(root/f'published-{n}').mkdir();after=original(root)
    events.append({'name':f'published-{n}','before':list(module.signature(before)),'after':list(module.signature(after)),'time':time.monotonic()})
   responses.put(True)
 worker=threading.Thread(target=publisher);worker.start()
 def lstat(p,*a,**k):
  nonlocal root_calls
  if p==root:
   root_calls+=1
   if root_calls%2==0:
    requests.put(root_calls);responses.get(timeout=1)
  return original(p,*a,**k)
 Path.lstat=lstat;begun=time.monotonic()
 try:result,error=trial(lambda:module.census(root))
 finally:
  Path.lstat=original;requests.put(None);worker.join(timeout=1);req(not worker.is_alive(),'publisher joined')
 result.update(events=events,elapsed=time.monotonic()-begun,root_lstat_calls=root_calls,source_sha256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest())
 record(label,**result)
 if module is O:req(type(error)is ValueError and len(events)==3 and root_calls==6,'old immediate retry RED')
 else:req(error is None and result['returned']['complete_attempts']==2 and len(events)==1 and result['returned']['members']==3,'new delayed complete GREEN')
for i in range(3):
 interleave(O,f'publication-old-{i}');interleave(W,f'publication-new-{i}')
req(O.POLICY==W.POLICY=={'logical':67108864,'allocated':100663296,'members':32768,'depth':32,'file':4194304,'sample_seconds':5,'floor':10737418240,'samples':8192},'fixed original policy')
record('all original policy values unchanged',policy=W.POLICY)
# Exact finite scheduler and fatal refusal, with fake clock only for elapsed-boundary tests.
class Clock:
 def __init__(self):self.now=0.;self.sleeps=[];self.jump=None;self.fatal=None
 def monotonic(self):return self.now
 def sleep(self,s):
  self.sleeps.append(s)
  if self.fatal is not None:raise self.fatal
  self.now+=s if self.jump is None else self.jump
saved_sample=W._sample;saved_time=W.time
for kind in ('changing','missing','value','permission','memory','interrupt','exit','remaining','oversleep','sleepfatal','success'):
 clock=Clock();calls=[];cause={'changing':W.ChangingTree('directory metadata'),'missing':FileNotFoundError('vanished namespace'),'value':ValueError('limit'),'permission':PermissionError('permission'),'memory':MemoryError('fatal'),'interrupt':KeyboardInterrupt('fatal'),'exit':SystemExit('fatal'),'remaining':W.ChangingTree('late'),'oversleep':W.ChangingTree('late'),'sleepfatal':W.ChangingTree('metadata'),'success':None}[kind]
 if kind=='oversleep':clock.jump=5
 if kind=='sleepfatal':clock.fatal=KeyboardInterrupt('wait fatal')
 def sample(root):
  calls.append(root)
  if kind=='remaining':clock.now=4.95
  if cause is not None:raise cause
  return {'complete':True}
 W._sample=sample;W.time=clock
 try:result,error=trial(lambda:W.census(ROOT))
 finally:W._sample=saved_sample;W.time=saved_time
 if kind in ('changing','missing'):req(type(error)is ValueError and error.__cause__ is cause and len(calls)==3 and clock.sleeps==[.1,.1],'three complete attempts/two waits')
 elif kind=='success':req(error is None and len(calls)==1 and clock.sleeps==[],'stable no wait')
 elif kind=='remaining':req(type(error)is ValueError and len(calls)==1 and clock.sleeps==[],'insufficient remaining deadline')
 elif kind=='oversleep':req(type(error)is ValueError and len(calls)==1 and clock.sleeps==[.1],'oversleep refused before next attempt')
 elif kind=='sleepfatal':req(error is clock.fatal and len(calls)==1 and clock.sleeps==[.1],'first wait fatal exact')
 else:req(error is cause and len(calls)==1 and clock.sleeps==[],'immediate first fatal/limit')
 record('schedule-'+kind,calls=len(calls),sleeps=clock.sleeps,**result)
# Real special namespace and resource violations. Caps only lowered within synthetic tests.
for kind in ('fifo','symlink','hardlink','file','logical','allocated','members','depth','floor'):
 root=tree('refuse-'+kind);p=root/'opaque';p.write_bytes(b'x'*32);policy=dict(W.POLICY);orig_disk=W.shutil.disk_usage;sleeps=[];calls=[]
 if kind=='fifo':os.mkfifo(root/'pipe')
 if kind=='symlink':(root/'link').symlink_to(p)
 if kind=='hardlink':os.link(p,root/'hard')
 if kind in ('file','logical'):W.POLICY[kind]=31
 if kind=='allocated':W.POLICY[kind]=0
 if kind=='members':W.POLICY[kind]=1
 if kind=='depth':W.POLICY[kind]=0
 if kind=='floor':W.shutil.disk_usage=lambda path:types.SimpleNamespace(free=W.POLICY['floor']-1)
 W.time=types.SimpleNamespace(monotonic=time.monotonic,sleep=lambda s:sleeps.append(s))
 def sample(root):calls.append(root);return saved_sample(root)
 W._sample=sample
 try:result,error=trial(lambda:W.census(root))
 finally:W.POLICY.clear();W.POLICY.update(policy);W.shutil.disk_usage=orig_disk;W.time=saved_time;W._sample=saved_sample
 req(type(error)is ValueError and len(calls)==1 and not sleeps,'resource/type immediate refusal')
 record('resource-'+kind,calls=len(calls),sleeps=sleeps,**result)
# Actual directory iterator closes real descriptor while retaining an exact original fatal object.
for primary in (KeyboardInterrupt('iterator fatal'),MemoryError('iterator memory')):
 root=tree('cleanup-'+type(primary).__name__);oldscan=W.os.scandir;before=len(os.listdir('/proc/self/fd'));secondary=OSError('close secondary');closed=[]
 class Broken:
  def __init__(self,p):self.it=oldscan(p)
  def __iter__(self):return self
  def __next__(self):raise primary
  def close(self):self.it.close();closed.append(True);raise secondary
 W.os.scandir=Broken
 try:result,error=trial(lambda:W.census(root))
 finally:W.os.scandir=oldscan
 req(error is primary and closed==[True] and len(os.listdir('/proc/self/fd'))==before,'actual fd/first fatal')
 record('real-iterator-'+type(primary).__name__,fd_before=before,fd_after=len(os.listdir('/proc/self/fd')),**result)
# Existing actual receiver source unchanged, only its imported watch is the successor.
import recover01 as R
R.W=W;R.HERE=tree('tinygit');R.START=time.monotonic();before=len(os.listdir('/proc/self/fd'))
body=R.git(['init','--bare',str(R.HERE/'one.git')],cwd=R.HERE)
call=R.CALLS[-1];req(call['exit']==call['actual_reaped_exit']==0 and call['actual_child_limits']=={'pid':call['pid'],'fsize':[4194304,4194304]} and call['cleanup_failures']==[],'actual init hard/soft4MiB and reap')
req(not Path('/proc',str(call['pid'])).exists(),'actual init PID gone')
try:os.killpg(call['pid'],0)
except ProcessLookupError:pass
else:raise AssertionError('init group remains')
req(before==len(os.listdir('/proc/self/fd')),'init no fd loss')
record('tiny-local-git-init',call=call,stdout=body.decode(),watch_samples=list(R.WATCHES),fd_before=before,fd_after=len(os.listdir('/proc/self/fd')))
for i,primary in enumerate((KeyboardInterrupt('owned child fatal'),MemoryError('owned child memory'),ValueError('owned child limit'))):
 R.HERE=tree('killgit-'+str(i));R.WATCHES=[];R.BASELINE=None;R.START=time.monotonic();count=0;origwatch=R.watch;before=len(os.listdir('/proc/self/fd'))
 def watch():
  global count
  count+=1
  if count==2:raise primary
  return origwatch()
 R.watch=watch
 try:result,error=trial(lambda:R.git(['-c','alias.pause=!sleep 5','pause'],cwd=R.HERE))
 finally:R.watch=origwatch
 call=R.CALLS[-1]
 req(error is primary and call['actual_reaped_exit']==-9 and call['actual_child_limits']=={'pid':call['pid'],'fsize':[4194304,4194304]} and call['cleanup_failures']==[],'actual killed child/readback/first fatal')
 req(not Path('/proc',str(call['pid'])).exists() and before==len(os.listdir('/proc/self/fd')),'actual kill PID gone/FD balanced')
 try:os.killpg(call['pid'],0)
 except ProcessLookupError:pass
 else:raise AssertionError('kill group remains')
 record('actual-kill-reap-'+type(primary).__name__,call=call,fd_before=before,fd_after=len(os.listdir('/proc/self/fd')),**result)
record('complete',rows_before_completion=len(rows),source_only=True,no_network=True,no_entry=True)
print(json.dumps({'rows':len(rows),'watch_sha256':hashlib.sha256((D/'watch01.py').read_bytes()).hexdigest()}))
