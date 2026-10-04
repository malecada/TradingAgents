from pathlib import Path
import ast,os,sys,signal,time,subprocess,json
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-compatibility-baseline-flat-successor-preparation03-2026-10-05';OLD=D.parent/'financial-wrapper-compatibility-baseline-flat-successor-preparation02-2026-10-05';sys.path[:0]=[str(OLD),str(OLD/'utilities')];import watch01 as W;import owned_io as IO
scope=D/'exit-overlap04';scope.mkdir(mode=0o700);nodes=[n for n in ast.parse((P/'caller04.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('raw','process_state','paused_census')];env={'Path':Path,'os':os,'signal':signal,'time':time,'subprocess':subprocess,'FILE':4194304,'D':scope};exec(compile(ast.Module(body=nodes,type_ignores=[]),'exact-caller03-exit-seam','exec'),env)
child=subprocess.Popen([sys.executable,'-B','-c','import sys;sys.stdin.buffer.read()'],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
original=env['process_state'];identity=original(child)[1];interleaved=[];error=None
# Real child is allowed to finish after its live PID/starttime observation and
# before STOP. It stays unreaped until the exact candidate calls poll().
def process_state(p):
 answer=original(p)
 if not interleaved:
  child.stdin.close();interleaved.append(True);begun=time.monotonic()
  while original(child)[0]!='Z':
   assert time.monotonic()-begun<2;time.sleep(.002)
 return answer
env['process_state']=process_state
sample=None
try:sample=env['paused_census'](child,identity,W,IO)
except BaseException as caught:error=caught
finally:
 if child.poll() is None:
  try:os.killpg(child.pid,signal.SIGKILL)
  except ProcessLookupError:pass
 code=child.wait(timeout=5)
assert code==0 and error is None and sample is not None;assert not Path('/proc',str(child.pid)).exists()
result={'finding':'NORMAL_EXIT_BEFORE_STOP_FALSE_FAILURE','actual_child_exit':code,'actual_pid':child.pid,'actual_start_ticks':identity,'refusal_type':None,'refusal':None,'static_sample':sample,'real_live_to_zombie_interleaving':True,'actual_reaped':True,'pid_absent':True,'conservative_refusal_no_incomplete_sample_accepted':True,'public_caller_invoked':False,'numerical_imports':False};(D/'EXIT_OVERLAP04.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
