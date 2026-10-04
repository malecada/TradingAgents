from pathlib import Path
import types,time,os,json
H=Path(__file__).resolve().parent;checks=[];witnesses=[]
def load(name,file):
 m=types.ModuleType(name);m.__file__=str(H/file);exec(compile((H/file).read_bytes(),m.__file__,'exec'),m.__dict__);return m
O=load('original03','ORIGINAL03_copy_layout01.py');N=load('corrected04','copy_layout01.py');T=H/'owned-deadline04';T.mkdir(mode=0o700)
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
# Actual empty-directory scandir close followed by real5.1-second delay.
for label,m in [('old',O),('new',N)]:
 root=T/(label+'-real-close');root.mkdir(mode=0o700);closed=[];proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});real=m.os
 class Iterator:
  def __init__(self,p):self.inner=os.scandir(p)
  def __iter__(self):return self
  def __next__(self):return next(self.inner)
  def close(self):self.inner.close();closed.append(True);time.sleep(5.1)
 proxy.scandir=Iterator;m.os=proxy;start=time.monotonic();failure=None
 try:
  try:m.namespace(root);result='accepted'
  except ValueError as e:result='refused';failure=str(e)
 finally:m.os=real
 elapsed=time.monotonic()-start;ok(closed==[True],'real iterator closed exactly once '+label);ok(elapsed>=5.1,'actual wall delay '+label);ok(result==('accepted' if label=='old' else 'refused'),'real originalRED/newrefusal '+label);witnesses.append({'source':label,'case':'actual emptydir/realclose/real5.1sleep','seconds':elapsed,'result':result,'reason':failure,'close_count':len(closed)})
# Separate final-statvfs deadline path: actual statvfs, deterministic monotonic
# offset injected afterwards; this is a clock control, not measured5s wall work.
for label,m in [('old',O),('new',N)]:
 root=T/(label+'-last-resource');root.mkdir(mode=0o700);offset=[0];ro,rt=m.os,m.time;proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)})
 def fs(p):v=os.statvfs(p);offset[0]=5.1;return v
 proxy.statvfs=fs;m.os=proxy;m.time=types.SimpleNamespace(monotonic=lambda:time.monotonic()+offset[0]);result=None
 try:
  try:m.namespace(root);result='accepted'
  except ValueError as e:result='refused'
 finally:m.os=ro;m.time=rt
 ok(result==('accepted' if label=='old' else 'refused'),'final resource deadline '+label);witnesses.append({'source':label,'case':'actualstatvfs + injected monotonic5.1offset','result':result,'actual_wall5s_claim':False})
# Deadline observation cannot replace actual iterator/body first fatal.
for pc,sc in [(KeyboardInterrupt,ValueError),(KeyboardInterrupt,SystemExit),(MemoryError,ValueError),(ValueError,MemoryError),(SystemExit,KeyboardInterrupt)]:
 root=T/(pc.__name__+'-'+sc.__name__);root.mkdir(mode=0o700);(root/'opaque').write_bytes(b'x');primary=pc('iteration');secondary=sc('close');closed=[];offset=[0];ro,rt=N.os,N.time
 class Iterator:
  def __init__(self,p):self.inner=os.scandir(p)
  def __iter__(self):return self
  def __next__(self):next(self.inner);raise primary
  def close(self):self.inner.close();closed.append(True);offset[0]=5.1;raise secondary
 proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});proxy.scandir=Iterator;N.os=proxy;N.time=types.SimpleNamespace(monotonic=lambda:time.monotonic()+offset[0])
 try:
  try:N.namespace(root)
  except BaseException as actual:
   expected=primary if isinstance(primary,MemoryError) or not isinstance(primary,Exception) else secondary;ok(actual is expected,'deadline never replaces firstfatal');ok(closed==[True],'actual failing iterator closed once')
  else:raise AssertionError('fatal lost')
 finally:N.os=ro;N.time=rt
# Actual writer cleanup followed by expired genuine Reader guard: no success.
root=T/'writer';root.mkdir(mode=0o700);source=root/'input';source.write_bytes(b'opaque');source.chmod(0o600);spec={'rows':[{'original_path':str(source),'path':str(source),'destination':'body','original_mode':0o600,'copy_mode':0o600,'output_mode':0o600,'bytes':6,'sha256':N.h(b'opaque'),'role':'receipt'}]};reader=N.PC.Reader();put=N.put;calls=[]
def delayed_writer(*args):
 put(*args);calls.append(args[1]);reader.deadline=time.monotonic()-1
N.put=delayed_writer
try:
 try:N.copy_layout(spec,root/'partial',reader)
 except ValueError:ok(calls==['body'] and (root/'partial/body').read_bytes()==b'opaque','writer aftercleanup expired Reader refuses/partial retained')
 else:raise AssertionError('expired writer accepted')
finally:N.put=put
ok(not os.path.lexists(N.OUTPUT),'fixed actualRoot never executed')
(H/'DEADLINE04.json').write_text(json.dumps({'checks':checks,'assertions':len(checks),'witnesses':witnesses,'writer_deadline_is_injected_not120s_wall':True,'Root_entry_invoked':False},indent=2,sort_keys=True)+'\n');print(json.dumps({'assertions':len(checks),'witnesses':witnesses}))
