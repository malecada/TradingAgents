from pathlib import Path
import ast,os,sys,signal,time,subprocess,json,types,hashlib
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-compatibility-baseline-flat-successor-preparation02-2026-10-05';sys.path[:0]=[str(P),str(P/'utilities')];import watch01 as W;import owned_io as IO
results=[]
def extract(path,scope):
 nodes=[n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('raw','process_state','paused_census')];env={'Path':Path,'os':os,'signal':signal,'time':time,'subprocess':subprocess,'FILE':4194304,'D':scope};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env);return env
for label,path in [('old',P/'caller03.py'),('new',D/'caller04.py')]:
 scope=D/label;scope.mkdir(mode=0o700);env=extract(path,scope)
 child=subprocess.Popen([sys.executable,'-B','-c','import sys;sys.stdin.buffer.read()'],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 original=env['process_state'];identity=original(child)[1];trigger=[];error=None;sample=None
 def interleave(p):
  answer=original(p)
  if not trigger:
   child.stdin.close();trigger.append(True);begun=time.monotonic()
   while original(child)[0]!='Z':
    assert time.monotonic()-begun<2;time.sleep(.002)
  return answer
 env['process_state']=interleave
 try:sample=env['paused_census'](child,identity,W,IO)
 except BaseException as caught:error=caught
 finally:
  if child.poll() is None:os.killpg(child.pid,signal.SIGKILL)
  code=child.wait(timeout=5)
 assert code==0 and not Path('/proc',str(child.pid)).exists()
 if label=='old':assert isinstance(error,RuntimeError) and str(error)=='restore exited before STOP acknowledgement'
 else:assert error is None and sample['members']==1
 results.append({'case':label,'child_exit':code,'pid':child.pid,'start_ticks':identity,'error':None if error is None else str(error),'sample':sample,'pid_absent':True})
# Existing critical fatal path still resumes the actual stopped owned child.
scope=D/'fatal';scope.mkdir(mode=0o700);env=extract(D/'caller04.py',scope);child=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(20)'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True);identity=env['process_state'](child)[1];primary=KeyboardInterrupt('owned fatal control')
def fail(root):raise primary
try:
 try:env['paused_census'](child,identity,types.SimpleNamespace(census=fail,POLICY=W.POLICY),IO)
 except BaseException as error:assert error is primary
 else:raise AssertionError('lost fatal')
 begun=time.monotonic()
 while env['process_state'](child)[0]=='T':assert time.monotonic()-begun<1;time.sleep(.002)
finally:
 os.killpg(child.pid,signal.SIGKILL);code=child.wait(timeout=5)
assert code==-9 and not Path('/proc',str(child.pid)).exists();results.append({'case':'fatal','same_primary':True,'resumed':True,'reaped':code,'pid_absent':True})
v=json.loads((D/'INVERSE01.json').read_text());assert (D/'caller04.py').read_text().replace(v['new'],v['old'])==(P/'caller03.py').read_text()
for n in ('restore_successor02.py','utilities/recovery_ustar02.py'):assert (D/n).read_bytes()==(P/n).read_bytes()
(D/'CHECKS01.json').write_text(json.dumps({'cases':results,'single_literal_inverse':True,'unchanged_restore_ustar':True,'public_entry':False},indent=2)+'\n');print(json.dumps(results))
